from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import jwt
import time
import hashlib
from flask import current_app
from app.models.notification import Notification

# 用户关注关系表
followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('timestamp', db.DateTime, default=datetime.utcnow)
)

# 用户收藏文章关系表
favorites = db.Table('favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', name='fk_favorites_user')),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id', name='fk_favorites_post')),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    bio = db.Column(db.String(256))  # 个人简介
    avatar_path = db.Column(db.String(256))  # 头像路径
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    # 通知设置
    notify_followed = db.Column(db.Boolean, default=True)  # 关注通知
    notify_comment = db.Column(db.Boolean, default=True)   # 评论通知
    notify_reply = db.Column(db.Boolean, default=True)     # 回复通知
    show_email = db.Column(db.Boolean, default=False)      # 是否公开邮箱
    show_following = db.Column(db.Boolean, default=True)   # 是否公开关注列表
    
    # 权限常量
    PERMISSION_COMMENT = 0x01    # 评论权限
    PERMISSION_WRITE = 0x02      # 写文章权限
    PERMISSION_MODERATE = 0x04   # 管理评论权限
    PERMISSION_ADMIN = 0x80      # 管理员权限
    
    @property
    def gravatar_hash(self):
        """获取邮箱的MD5哈希值，用于Gravatar头像"""
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()
    
    # 关系
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    last_notification_read_time = db.Column(db.DateTime)
    
    # 用户关注的人
    following = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )
    
    # 收藏关系
    favorite_posts = db.relationship('Post', 
        secondary=favorites,
        backref=db.backref('favorited_by', lazy='dynamic'),
        lazy='dynamic'
    )
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def follow(self, user):
        """关注用户"""
        if not self.is_following(user):
            self.following.append(user)
            db.session.commit()
    
    def unfollow(self, user):
        """取消关注用户"""
        if self.is_following(user):
            self.following.remove(user)
            db.session.commit()
    
    def is_following(self, user):
        """判断是否关注了某用户"""
        if user.id is None:
            return False
        return self.following.filter(
            followers.c.followed_id == user.id).count() > 0
    
    def get_following_posts(self):
        """获取关注用户的文章"""
        from app.models.post import Post
        return Post.query.join(
            followers, (followers.c.followed_id == Post.author_id)
        ).filter(followers.c.follower_id == self.id)
    
    def favorite_post(self, post):
        """收藏文章"""
        if not self.has_favorited(post):
            self.favorite_posts.append(post)
            db.session.commit()
    
    def unfavorite_post(self, post):
        """取消收藏文章"""
        if self.has_favorited(post):
            self.favorite_posts.remove(post)
            db.session.commit()
    
    def has_favorited(self, post):
        """检查是否已收藏文章"""
        return self.favorite_posts.filter_by(id=post.id).first() is not None
    
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time.time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')
    
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return None
        return User.query.get(id)

    def can(self, permission):
        """检查用户是否有指定权限"""
        if self.is_admin:
            return True
        if permission == self.PERMISSION_COMMENT:
            return self.is_active
        if permission == self.PERMISSION_WRITE:
            return self.is_active
        return False

    @property
    def permissions(self):
        """获取用户的所有权限"""
        perms = 0
        if self.is_active:
            perms |= self.PERMISSION_COMMENT
            perms |= self.PERMISSION_WRITE
        if self.is_admin:
            perms |= self.PERMISSION_MODERATE
            perms |= self.PERMISSION_ADMIN
        return perms

    @property
    def unread_notification_count(self):
        """获取未读通知数量"""
        if self.last_notification_read_time:
            return self.notifications.filter(
                Notification.timestamp > self.last_notification_read_time
            ).count()
        return self.notifications.filter_by(is_read=False).count()

    def add_notification(self, message, type='info'):
        """添加一条通知"""
        notification = Notification(message=message, type=type, user=self)
        db.session.add(notification)
        return notification

    @property
    def following_count(self):
        """关注数"""
        return self.following.count()

    @property
    def followers_count(self):
        """粉丝数"""
        return self.followers.count()

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id)) 