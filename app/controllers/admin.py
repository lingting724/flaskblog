from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.post import Post, Category, Tag
from app.models.comment import Comment
from app.forms.admin import PostForm, CategoryForm, TagForm
from app.utils.upload import save_image
from app.utils.decorators import admin_required
from slugify import slugify
from werkzeug.utils import secure_filename
import os

# 修改蓝图名称和URL前缀，避免与Flask-Admin冲突
admin_bp = Blueprint('admin_custom', __name__, url_prefix='/manage')

@admin_bp.before_request
@login_required
@admin_required
def before_request():
    """确保只有管理员可以访问管理页面"""
    pass

@admin_bp.route('/')
def index():
    # 统计数据
    post_count = Post.query.count()
    user_count = User.query.count()
    comment_count = Comment.query.count()
    category_count = Category.query.count()
    tag_count = Tag.query.count()
    
    print("统计数据:", post_count, user_count, comment_count, category_count, tag_count)
    
    # 最近发布的文章
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    
    # 最近注册的用户
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/index.html',
                         title='管理后台',
                         post_count=post_count,
                         user_count=user_count,
                         comment_count=comment_count,
                         category_count=category_count,
                         tag_count=tag_count,
                         recent_posts=recent_posts,
                         recent_users=recent_users)

# 文章管理
@admin_bp.route('/posts')
def posts():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('admin/posts.html', title='文章管理', posts=posts)

@admin_bp.route('/posts/create', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    # 设置分类和标签的选项
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]
    form.tags.choices = [(t.id, t.name) for t in Tag.query.order_by(Tag.name).all()]
    
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            slug='-'.join(form.title.data.lower().split()[:8]),
            summary=form.summary.data,
            content=form.content.data,
            category_id=form.category_id.data,
            author=current_user,
            is_published=form.is_published.data
        )
        
        # 处理标签
        if form.tags.data:
            tags = Tag.query.filter(Tag.id.in_(form.tags.data)).all()
            post.tags = tags
        
        # 处理封面图
        if form.cover.data:
            filename = secure_filename(form.cover.data.filename)
            file_path = os.path.join('uploads/posts', filename)
            form.cover.data.save(os.path.join(current_app.static_folder, file_path))
            post.cover_path = file_path
        
        db.session.add(post)
        db.session.commit()
        flash('文章已创建', 'success')
        return redirect(url_for('admin_custom.posts'))
    
    return render_template('admin/post_form.html', title='新建文章', form=form)

@admin_bp.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
def edit_post(id):
    post = Post.query.get_or_404(id)
    form = PostForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    form.tags.choices = [(t.id, t.name) for t in Tag.query.all()]
    
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.summary = form.summary.data
        post.is_published = form.is_published.data
        post.category_id = form.category_id.data
        
        # 处理标签
        post.tags = []
        for tag_id in form.tags.data:
            tag = Tag.query.get(tag_id)
            if tag:
                post.tags.append(tag)
        
        # 处理特色图片
        if form.cover.data:
            filename = secure_filename(form.cover.data.filename)
            file_path = os.path.join('uploads/posts', filename)
            form.cover.data.save(os.path.join(current_app.static_folder, file_path))
            post.cover_path = file_path
        
        db.session.commit()
        flash('文章更新成功', 'success')
        return redirect(url_for('admin_custom.posts'))
    
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        form.summary.data = post.summary
        form.is_published.data = post.is_published
        form.category_id.data = post.category_id
        form.tags.data = [tag.id for tag in post.tags]
    
    return render_template('admin/post_form.html', title='编辑文章', form=form, post=post)

@admin_bp.route('/posts/delete/<int:id>', methods=['POST'])
def delete_post(id):
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    flash('文章已删除', 'success')
    return redirect(url_for('admin_custom.posts'))

# 分类管理
@admin_bp.route('/categories')
def categories():
    page = request.args.get('page', 1, type=int)
    pagination = Category.query.order_by(Category.name).paginate(page=page, per_page=10)
    categories = pagination.items
    form = CategoryForm()
    return render_template('admin/categories.html',
                         title='分类管理',
                         categories=categories,
                         pagination=pagination,
                         form=form)

@admin_bp.route('/categories/create', methods=['POST'])
@login_required
def create_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(name=form.name.data)
        category.save()  # save() 方法会自动生成 slug
        flash('分类已创建', 'success')
    return redirect(url_for('admin_custom.categories'))

@admin_bp.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
def edit_category(id):
    category = Category.query.get_or_404(id)
    form = CategoryForm()
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        category.slug = slugify(form.name.data)
        db.session.commit()
        flash('分类更新成功', 'success')
        return redirect(url_for('admin_custom.categories'))
    
    elif request.method == 'GET':
        form.name.data = category.name
        form.description.data = category.description
    
    return render_template('admin/edit_category.html', title='编辑分类', form=form, category=category)

@admin_bp.route('/categories/delete/<int:id>', methods=['POST'])
def delete_category(id):
    category = Category.query.get_or_404(id)
    
    # 检查是否有文章使用此分类
    if category.posts.count() > 0:
        flash('无法删除，该分类下有文章', 'danger')
        return redirect(url_for('admin_custom.categories'))
    
    db.session.delete(category)
    db.session.commit()
    flash('分类已删除', 'success')
    return redirect(url_for('admin_custom.categories'))

# 标签管理
@admin_bp.route('/tags')
def tags():
    page = request.args.get('page', 1, type=int)
    pagination = Tag.query.order_by(Tag.name).paginate(page=page, per_page=10)
    tags = pagination.items
    form = TagForm()
    return render_template('admin/tags.html',
                         title='标签管理',
                         tags=tags,
                         pagination=pagination,
                         form=form)

@admin_bp.route('/tags/create', methods=['GET', 'POST'])
def create_tag():
    form = TagForm()
    if form.validate_on_submit():
        tag = Tag(
            name=form.name.data,
            slug=slugify(form.name.data)
        )
        tag.save()
        flash('标签创建成功', 'success')
        return redirect(url_for('admin_custom.tags'))
    
    return render_template('admin/create_tag.html', title='创建标签', form=form)

@admin_bp.route('/tags/edit/<int:id>', methods=['GET', 'POST'])
def edit_tag(id):
    tag = Tag.query.get_or_404(id)
    form = TagForm()
    
    if form.validate_on_submit():
        tag.name = form.name.data
        tag.slug = slugify(form.name.data)
        db.session.commit()
        flash('标签更新成功', 'success')
        return redirect(url_for('admin_custom.tags'))
    
    elif request.method == 'GET':
        form.name.data = tag.name
    
    return render_template('admin/edit_tag.html', title='编辑标签', form=form, tag=tag)

@admin_bp.route('/tags/delete/<int:id>', methods=['POST'])
def delete_tag(id):
    tag = Tag.query.get_or_404(id)
    db.session.delete(tag)
    db.session.commit()
    flash('标签已删除', 'success')
    return redirect(url_for('admin_custom.tags'))

# 用户管理
@admin_bp.route('/users')
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('admin/users.html', title='用户管理', users=users)

@admin_bp.route('/users/toggle_active/<int:id>', methods=['POST'])
def toggle_user_active(id):
    user = User.query.get_or_404(id)
    
    # 不能禁用自己
    if user == current_user:
        flash('不能禁用自己的账户', 'danger')
        return redirect(url_for('admin_custom.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    status = '启用' if user.is_active else '禁用'
    flash(f'用户 {user.username} 已{status}', 'success')
    return redirect(url_for('admin_custom.users'))

@admin_bp.route('/users/delete/<int:id>', methods=['POST'])
def delete_user(id):
    user = User.query.get_or_404(id)
    
    # 不能删除自己或管理员
    if user == current_user:
        flash('不能删除自己的账户', 'danger')
        return redirect(url_for('admin_custom.users'))
    
    if user.is_admin:
        flash('不能删除管理员账户', 'danger')
        return redirect(url_for('admin_custom.users'))
    
    # 删除用户的所有文章和评论
    Post.query.filter_by(author=user).delete()
    Comment.query.filter_by(author=user).delete()
    db.session.delete(user)
    db.session.commit()
    
    flash(f'用户 {user.username} 及其所有内容已删除', 'success')
    return redirect(url_for('admin_custom.users'))

# 评论管理
@admin_bp.route('/comments')
def comments():
    page = request.args.get('page', 1, type=int)
    comments = Comment.query.order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('admin/comments.html', title='评论管理', comments=comments)

@admin_bp.route('/comments/toggle/<int:id>', methods=['POST'])
def toggle_comment(id):
    comment = Comment.query.get_or_404(id)
    comment.is_approved = not comment.is_approved
    db.session.commit()
    status = '审核通过' if comment.is_approved else '取消审核'
    flash(f'评论已{status}', 'success')
    return redirect(url_for('admin_custom.comments'))

@admin_bp.route('/comments/delete/<int:id>', methods=['POST'])
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    flash('评论已删除', 'success')
    return redirect(url_for('admin_custom.comments')) 