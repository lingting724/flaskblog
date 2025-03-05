from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import current_user, login_required
from app import db
from app.models.post import Post, Category, Tag
from app.models.comment import Comment
from app.forms.blog import CommentForm, SearchForm
from sqlalchemy import func, desc, or_
from app.models.user import User
from slugify import slugify
from app.models.notification import Notification

blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(is_published=True).order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=10)
    posts = pagination.items
    
    # 获取热门文章
    popular_posts = Post.query.filter_by(is_published=True).order_by(
        Post.view_count.desc()
    ).limit(5).all()
    
    # 获取所有分类并确保有 slug
    categories = Category.query.all()
    for category in categories:
        if not category.slug:
            category.slug = slugify(category.name)
    db.session.commit()
    
    # 获取热门标签
    tags = Tag.query.join(Tag.posts).group_by(Tag.id).order_by(
        db.func.count(Post.id).desc()
    ).limit(20).all()
    
    return render_template('front/index.html',
                         posts=posts,
                         pagination=pagination,
                         popular_posts=popular_posts,
                         categories=categories,
                         tags=tags)

@blog_bp.route('/post/<string:slug>')
def post_detail(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    # 增加浏览量
    post.increment_view()
    
    # 创建评论表单
    form = CommentForm()
    
    # 获取已审核的文章评论
    comments = Comment.query.filter_by(
        post_id=post.id,
        parent_id=None,  # 只获取顶级评论
        is_approved=True  # 只获取已审核的评论
    ).order_by(Comment.created_at.desc()).all()
    
    # 获取相关文章
    related_posts = Post.query.filter(
        Post.id != post.id,  # 排除当前文章
        Post.is_published == True,  # 只获取已发布的文章
        (
            (Post.category_id == post.category_id) |  # 同分类
            (Post.author_id == post.author_id) |      # 同作者
            (Post.tags.any(Tag.id.in_([tag.id for tag in post.tags])))  # 相同标签
        )
    ).order_by(
        Post.created_at.desc()
    ).limit(5).all()
    
    return render_template('front/post_detail.html',
                         post=post,
                         form=form,
                         comments=comments,
                         related_posts=related_posts)

@blog_bp.route('/post/<slug>/comment', methods=['POST'])
@login_required
def post_comment(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    form = CommentForm()
    
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            post=post,
            author=current_user
        )
        db.session.add(comment)
        
        # 给文章作者发送通知
        if current_user != post.author:
            notification = Notification(
                message=f'{current_user.username} 评论了你的文章 "{post.title}"',
                user=post.author,
                type='comment',
                post=post,  # 关联文章
                comment=comment  # 关联评论
            )
            db.session.add(notification)
        
        db.session.commit()
        flash('评论已发布', 'success')
        
    return redirect(url_for('blog.post_detail', slug=post.slug))

@blog_bp.route('/category/<string:slug>')
def category_posts(slug):
    page = request.args.get('page', 1, type=int)
    category = Category.query.filter_by(slug=slug).first_or_404()
    
    # 获取该分类下已发布的文章
    posts_query = Post.query.filter_by(
        category_id=category.id,
        is_published=True
    )
    
    # 获取已发布文章的总数
    published_count = posts_query.count()
    
    # 分页
    posts = posts_query.order_by(
        Post.created_at.desc()
    ).paginate(
        page=page,
        per_page=10,
        error_out=False
    )
    
    # 添加调试信息
    print(f"分类: {category.name}")
    print(f"已发布文章数量: {published_count}")
    print(f"当前页文章: {len(posts.items)}")
    
    return render_template('front/category_posts.html',
                         category=category,
                         posts=posts,
                         published_count=published_count)  # 传递已发布文章数量

@blog_bp.route('/tag/<slug>')
def tag_posts(slug):
    tag = Tag.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = tag.posts.filter_by(is_published=True).order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=10)
    posts = pagination.items
    return render_template('front/tag_posts.html',
                          title=f'标签: {tag.name}',
                          tag=tag,
                          posts=posts,
                          pagination=pagination)

@blog_bp.route('/search')
def search():
    """搜索文章"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    if query:
        # 通过标题或作者名进行模糊搜索
        posts = Post.query.join(User, Post.author_id == User.id).filter(
            Post.is_published == True,  # 只搜索已发布的文章
            or_(
                Post.title.ilike(f'%{query}%'),  # 标题模糊匹配
                User.username.ilike(f'%{query}%')  # 作者名模糊匹配
            )
        ).order_by(Post.created_at.desc()).paginate(
            page=page, 
            per_page=10,
            error_out=False
        )
    else:
        posts = None
    
    return render_template('front/search.html',
                         title='搜索结果',
                         query=query,
                         posts=posts)

@blog_bp.route('/user/<username>/posts')
def user_posts(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(
        author=user,
        is_published=True
    ).order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template('front/user/posts.html',
                         user=user,
                         posts=pagination,  # 注意这里，直接传递 pagination 对象
                         pagination=pagination)

@blog_bp.route('/comment/<int:id>/delete', methods=['POST'])
@login_required
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    if comment.author != current_user:
        abort(403)
    
    post = comment.post
    db.session.delete(comment)
    db.session.commit()
    flash('评论已删除', 'success')
    return redirect(url_for('blog.post_detail', slug=post.slug))

@blog_bp.route('/favorite/<string:slug>', methods=['POST'])
@login_required
def favorite_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    current_user.favorite_post(post)
    flash('文章已收藏！', 'success')
    return redirect(url_for('blog.post_detail', slug=slug))

@blog_bp.route('/unfavorite/<string:slug>', methods=['POST'])
@login_required
def unfavorite_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    current_user.unfavorite_post(post)
    flash('已取消收藏！', 'success')
    return redirect(url_for('blog.post_detail', slug=slug))


# 错误页面测试
@blog_bp.route('/test-errors/<error_code>')
def test_errors(error_code):
    if error_code == '404':
        # 触发404错误
        abort(404)
    elif error_code == '403':
        # 触发403错误
        abort(403)
    elif error_code == '500':
        # 触发500错误
        abort(500)
    elif error_code == '429':
        # 触发429错误
        abort(429)
    return "这个页面不会被显示"

