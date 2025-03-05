from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.user import User
from app.models.post import Post, Category, Tag
from app.models.comment import Comment
from app.models.notification import Notification
from app.forms.blog import PostForm, CategoryForm, TagForm
from app.forms.user import ProfileForm, ChangePasswordForm, NotificationSettingsForm
from app.utils.upload import save_image
from app.utils.decorators import permission_required
from sqlalchemy import func
import os
from datetime import datetime

user_bp = Blueprint('user', __name__)

def redirect_back():
    """返回上一页面，如果没有则返回首页"""
    return redirect(request.referrer or url_for('blog.index'))

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    password_form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if form.avatar.data:
            avatar_path = save_image(form.avatar.data, 'avatars')
            current_user.avatar_path = avatar_path
        
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.bio = form.bio.data
        db.session.commit()
        flash('个人资料已更新', 'success')
        return redirect(url_for('user.profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.bio.data = current_user.bio
    
    return render_template('front/user/profile.html', 
                         title='个人资料',
                         form=form,
                         password_form=password_form)

@user_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.old_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('密码已修改', 'success')
            return redirect(url_for('user.profile'))
        else:
            flash('原密码不正确', 'danger')
    return redirect(url_for('user.profile'))

@user_bp.route('/favorite/<int:post_id>', methods=['POST'])
@login_required
def favorite(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user.has_favorited(post):
        current_user.unfavorite(post)
        flash('已取消收藏', 'info')
    else:
        current_user.favorite(post)
        flash('已添加到收藏', 'success')
    
    return redirect(request.referrer or url_for('blog.index'))

@user_bp.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow(user_id):
    """关注/取消关注用户"""
    user = User.query.get_or_404(user_id)
    if current_user.is_following(user):
        current_user.unfollow(user)
        flash('已取消关注', 'success')
    else:
        current_user.follow(user)
        flash('关注成功', 'success')
    return redirect(request.referrer or url_for('blog.index'))

@user_bp.route('/unfollow/<int:user_id>', methods=['POST'])
@login_required
def unfollow(user_id):
    user = User.query.get_or_404(user_id)
    if not current_user.is_following(user):
        flash('你还没有关注这个用户', 'info')
    else:
        current_user.unfollow(user)
        db.session.commit()
        flash('已取消关注', 'info')
    return redirect(request.referrer or url_for('blog.index'))

@user_bp.route('/following')
@login_required
def following():
    """我的关注页面"""
    page = request.args.get('page', 1, type=int)
    pagination = current_user.following.paginate(
        page=page,
        per_page=10,  # 直接使用固定值
        error_out=False
    )
    return render_template('front/user/following.html', users=pagination)

@user_bp.route('/followers')
@login_required
def followers():
    """我的粉丝页面"""
    page = request.args.get('page', 1, type=int)
    pagination = current_user.followers.paginate(
        page=page,
        per_page=10,  # 直接使用固定值
        error_out=False
    )
    return render_template('front/user/followers.html', users=pagination)

@user_bp.route('/<username>/posts')
def user_posts(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(
        author=user,
        is_published=True
    ).order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template('front/user/user_posts.html',
                         user=user,
                         pagination=pagination,
                         posts=pagination.items)

@user_bp.route('/dashboard')
@login_required
def dashboard():
    # 统计数据
    post_count = Post.query.filter_by(author=current_user).count()
    comment_count = Comment.query.filter_by(author=current_user).count()
    view_count = Post.query.with_entities(func.sum(Post.view_count)).filter_by(author=current_user).scalar() or 0
    
    # 最近的文章
    recent_posts = Post.query.filter_by(author=current_user).order_by(Post.created_at.desc()).limit(5).all()
    
    # 最近的评论
    recent_comments = Comment.query.filter_by(author=current_user).order_by(Comment.created_at.desc()).limit(5).all()
    
    return render_template('front/user/dashboard.html',
                         title='控制台',
                         post_count=post_count,
                         comment_count=comment_count,
                         view_count=view_count,
                         recent_posts=recent_posts,
                         recent_comments=recent_comments)

@user_bp.route('/posts')
@login_required
def my_posts():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(author=current_user).order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=10)
    posts = pagination.items
    return render_template('front/user/my_posts.html',
                         title='我的文章',
                         posts=posts,
                         pagination=pagination)

@user_bp.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    # 只获取当前用户创建的分类
    form.category_id.choices = [(c.id, c.name) for c in 
                              Category.query.filter_by(author=current_user).all()]
    # 只获取当前用户创建的标签
    form.tags.choices = [(t.id, t.name) for t in 
                        Tag.query.filter_by(author=current_user).all()]
    
    if form.validate_on_submit():
        # 验证选择的分类是否属于当前用户
        category = Category.query.get(form.category_id.data)
        if not category or category.author != current_user:
            flash('无效的分类选择', 'danger')
            return render_template('front/user/post_form.html', form=form)
            
        post = Post(
            title=form.title.data,
            content=form.content.data,
            summary=form.summary.data,
            category_id=form.category_id.data,
            author=current_user,
            is_published=form.is_published.data
        )
        
        # 处理标签
        if form.tags.data:
            selected_tags = Tag.query.filter(
                Tag.id.in_(form.tags.data),
                Tag.author == current_user
            ).all()
            post.tags = selected_tags
        
        # 处理封面图片
        if form.cover.data:
            try:
                filename = save_image(form.cover.data, 'posts')
                post.cover_path = filename
            except Exception as e:
                current_app.logger.error(f'保存封面图片失败: {str(e)}')
                flash('封面图片保存失败', 'danger')
                return render_template('front/user/post_form.html', form=form)
        
        try:
            db.session.add(post)
            db.session.commit()
            flash('文章发布成功！', 'success')
            return redirect(url_for('user.my_posts'))
        except Exception as e:
            current_app.logger.error(f'保存文章失败: {str(e)}')
            db.session.rollback()
            flash('文章保存失败', 'danger')
            
    return render_template('front/user/post_form.html', form=form)

@user_bp.route('/posts/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required(User.PERMISSION_WRITE)
def edit_post(id):
    post = Post.query.get_or_404(id)
    if post.author != current_user:
        abort(403)
    
    form = PostForm(obj=post)
    # 只显示当前用户的分类
    form.category_id.choices = [(c.id, c.name) for c in 
                              Category.query.filter_by(author=current_user).order_by(Category.name).all()]
    # 只显示当前用户的标签
    form.tags.choices = [(t.id, t.name) for t in 
                        Tag.query.filter_by(author=current_user).order_by(Tag.name).all()]
    
    if form.validate_on_submit():
        # 验证选择的分类是否属于当前用户
        category = Category.query.get(form.category_id.data)
        if not category or category.author != current_user:
            flash('无效的分类选择', 'danger')
            return render_template('front/user/post_form.html', form=form, post=post)
            
        if post.title != form.title.data:
            post.title = form.title.data
            post.slug = post.generate_slug()
        
        post.content = form.content.data
        post.summary = form.summary.data
        post.category_id = form.category_id.data
        post.is_published = form.is_published.data
        
        # 更新标签
        if form.tags.data:
            selected_tags = Tag.query.filter(
                Tag.id.in_(form.tags.data),
                Tag.author == current_user
            ).all()
            post.tags = selected_tags
        else:
            post.tags = []
        
        if form.cover.data:
            filepath = save_image(form.cover.data, 'posts')
            post.cover_path = filepath
        
        db.session.commit()
        flash('文章已更新', 'success')
        return redirect(url_for('blog.post_detail', slug=post.slug))
    else:
        form.tags.data = [tag.id for tag in post.tags]
    
    return render_template('front/user/post_form.html', form=form, post=post)

@user_bp.route('/comments')
@login_required
def my_comments():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.filter_by(author=current_user).order_by(
        Comment.created_at.desc()
    ).paginate(page=page, per_page=20)
    comments = pagination.items
    return render_template('front/user/my_comments.html',
                         title='我的评论',
                         comments=comments,
                         pagination=pagination)

@user_bp.route('/favorites')
@login_required
def favorites():
    page = request.args.get('page', 1, type=int)
    pagination = current_user.favorite_posts.order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=10)
    return render_template('front/user/favorites.html', pagination=pagination)

@user_bp.route('/comments/delete/<int:id>', methods=['POST'])
@login_required
@permission_required(User.PERMISSION_COMMENT)
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    if comment.author != current_user:
        abort(403)
    
    db.session.delete(comment)
    db.session.commit()
    flash('评论已删除', 'success')
    return redirect(request.referrer or url_for('user.my_comments'))

@user_bp.route('/posts/delete/<int:id>', methods=['POST'])
@login_required
@permission_required(User.PERMISSION_WRITE)
def delete_post(id):
    post = Post.query.get_or_404(id)
    if post.author != current_user:
        abort(403)
    
    # 删除封面图片
    if post.cover_path:
        try:
            os.remove(os.path.join(current_app.static_folder, post.cover_path))
        except:
            pass
    
    db.session.delete(post)
    db.session.commit()
    flash('文章已删除', 'success')
    return redirect(url_for('user.my_posts'))

@user_bp.route('/following/<username>')
def following_posts(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.followed_posts().paginate(page=page, per_page=10)
    posts = pagination.items
    return render_template('front/user/following_posts.html',
                         title='关注的人的文章',
                         user=user,
                         posts=posts,
                         pagination=pagination)

@user_bp.route('/notifications')
@login_required
def notifications():
    page = request.args.get('page', 1, type=int)
    filter = request.args.get('filter', 'unread')  # 默认显示未读消息
    
    # 获取未读消息数
    unread_count = current_user.notifications.filter_by(is_read=False).count()
    
    # 根据筛选条件查询
    query = current_user.notifications
    if filter == 'unread':
        query = query.filter_by(is_read=False)
    elif filter == 'read':
        query = query.filter_by(is_read=True)
        
    # 分页
    notifications = query.order_by(Notification.timestamp.desc()).paginate(
        page=page, per_page=10
    )
    
    return render_template('front/user/notifications.html',
                         notifications=notifications,
                         filter=filter,
                         unread_count=unread_count)

@user_bp.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_read(notification_id):
    notification = current_user.notifications.filter_by(id=notification_id).first_or_404()
    notification.is_read = True
    db.session.commit()
    flash('消息已标记为已读', 'success')
    return redirect(url_for('user.notifications'))

@user_bp.route('/notifications/mark_all_read', methods=['POST'])
@login_required
def mark_all_read():
    current_user.notifications.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    flash('所有消息已标记为已读', 'success')
    return redirect(url_for('user.notifications'))

@user_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = NotificationSettingsForm()
    if form.validate_on_submit():
        current_user.notify_followed = form.notify_followed.data
        current_user.notify_comment = form.notify_comment.data
        current_user.notify_reply = form.notify_reply.data
        current_user.show_email = form.show_email.data
        current_user.show_following = form.show_following.data
        db.session.commit()
        flash('设置已更新', 'success')
        return redirect(url_for('user.settings'))
    elif request.method == 'GET':
        form.notify_followed.data = current_user.notify_followed
        form.notify_comment.data = current_user.notify_comment
        form.notify_reply.data = current_user.notify_reply
        form.show_email.data = current_user.show_email
        form.show_following.data = current_user.show_following
    return render_template('front/user/settings.html', 
                         title='系统设置',
                         form=form)

@user_bp.route('/settings/email', methods=['POST'])
@login_required
def update_email_settings():
    # 更新邮件通知设置
    current_user.notify_followed = request.form.get('notify_followed', type=bool)
    current_user.notify_comment = request.form.get('notify_comment', type=bool)
    current_user.notify_reply = request.form.get('notify_reply', type=bool)
    db.session.commit()
    flash('邮件通知设置已更新', 'success')
    return redirect(url_for('user.settings'))

@user_bp.route('/settings/privacy', methods=['POST'])
@login_required
def update_privacy_settings():
    # 更新隐私设置
    current_user.show_email = request.form.get('show_email', type=bool)
    current_user.show_following = request.form.get('show_following', type=bool)
    db.session.commit()
    flash('隐私设置已更新', 'success')
    return redirect(url_for('user.settings'))

@user_bp.route('/categories')
@login_required
def my_categories():
    # 只获取当前用户创建的分类
    categories = Category.query.filter_by(author=current_user).all()
    form = CategoryForm()
    return render_template('front/user/categories.html',
                         title='分类管理',
                         categories=categories,
                         form=form)

@user_bp.route('/categories/create', methods=['POST'])
@login_required
def create_category():
    form = CategoryForm()
    if form.validate_on_submit():
        # 创建分类时设置作者
        category = Category(name=form.name.data, author=current_user)
        db.session.add(category)
        db.session.commit()
        flash('分类已创建', 'success')
    return redirect(url_for('user.my_categories'))

@user_bp.route('/categories/delete/<int:id>', methods=['POST'])
@login_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    # 检查是否是分类的创建者
    if category.author != current_user:
        abort(403)
    if category.posts.count() > 0:
        flash('该分类下还有文章，无法删除', 'danger')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('分类已删除', 'success')
    return redirect(url_for('user.my_categories'))

@user_bp.route('/tags')
@login_required
def my_tags():
    # 修改为只获取当前用户创建的标签
    tags = Tag.query.filter_by(author_id=current_user.id).all()
    form = TagForm()
    return render_template('front/user/tags.html',
                         title='标签管理',
                         tags=tags,
                         form=form)

@user_bp.route('/tags/create', methods=['POST'])
@login_required
def create_tag():
    form = TagForm()
    if form.validate_on_submit():
        # 检查标签名是否已存在
        existing_tag = Tag.query.filter_by(
            name=form.name.data, 
            author_id=current_user.id
        ).first()
        
        if existing_tag:
            flash('该标签名已存在', 'danger')
        else:
            # 创建标签时设置作者ID
            tag = Tag(
                name=form.name.data,
                author_id=current_user.id
            )
            try:
                db.session.add(tag)
                db.session.commit()
                flash('标签已创建', 'success')
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'创建标签失败: {str(e)}')
                flash('创建标签失败', 'danger')
    return redirect(url_for('user.my_tags'))

@user_bp.route('/tags/delete/<int:id>', methods=['POST'])
@login_required
def delete_tag(id):
    tag = Tag.query.get_or_404(id)
    # 检查是否是标签的创建者
    if tag.author_id != current_user.id:
        abort(403)
    
    if tag.posts.count() > 0:
        flash('该标签下还有文章，无法删除', 'danger')
    else:
        try:
            db.session.delete(tag)
            db.session.commit()
            flash('标签已删除', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'删除标签失败: {str(e)}')
            flash('删除标签失败', 'danger')
    return redirect(url_for('user.my_tags')) 