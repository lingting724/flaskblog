from app import db
from datetime import datetime
from slugify import slugify
import re
import random
import string

# 文章-标签关联表
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id', name='fk_post_tags_post')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id', name='fk_post_tags_tag')),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    slug = db.Column(db.String(128), unique=True)
    summary = db.Column(db.String(200))
    content = db.Column(db.Text)
    cover_path = db.Column(db.String(256))  # 添加封面图片路径字段
    view_count = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键（添加约束名称）
    author_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_post_author'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id', name='fk_post_category'))
    
    # 关系
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary=post_tags, backref=db.backref('posts', lazy='dynamic'))
    
    def __init__(self, **kwargs):
        super(Post, self).__init__(**kwargs)
        if self.title and not self.slug:
            self.slug = slugify(self.title)
    
    def __repr__(self):
        return f'<Post {self.title}>'
    
    def increment_view(self):
        """增加浏览量"""
        self.view_count += 1
        db.session.add(self)
        db.session.commit()

    def generate_slug(self):
        """生成文章的 slug"""
        if self.title:
            self.slug = slugify(self.title)
        return self

    @classmethod
    def init_slugs(cls):
        """为所有没有 slug 的文章生成 slug"""
        posts = cls.query.filter_by(slug=None).all()
        for post in posts:
            post.generate_slug()
        # 不在这里提交，让调用者处理提交

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    slug = db.Column(db.String(50), unique=True)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 添加作者字段
    author_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_category_author'))
    author = db.relationship('User', backref=db.backref('categories', lazy='dynamic'))
    
    # 关系
    posts = db.relationship('Post', backref='category', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(Category, self).__init__(**kwargs)
        if self.name and not self.slug:
            self.slug = slugify(self.name)
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    def save(self):
        """保存分类，确保有 slug"""
        if not self.slug and self.name:
            self.slug = slugify(self.name)
        db.session.add(self)
        db.session.commit()
        return self
    
    @property
    def post_count(self):
        """获取分类下的文章数量"""
        return self.posts.filter_by(is_published=True).count()

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    slug = db.Column(db.String(50), unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 添加作者字段
    author_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_tag_author'))
    author = db.relationship('User', backref=db.backref('tags', lazy='dynamic'))
    
    def __init__(self, **kwargs):
        super(Tag, self).__init__(**kwargs)
        if self.name and not self.slug:
            self.slug = slugify(self.name)
    
    def __repr__(self):
        return f'<Tag {self.name}>'
    
    def save(self):
        if not self.slug:
            self.slug = slugify(self.name)
        db.session.add(self)
        db.session.commit()
        return self

    @staticmethod
    def init_slugs():
        """为所有没有slug的标签生成slug"""
        tags = Tag.query.filter_by(slug=None).all()
        for tag in tags:
            tag.slug = slugify(tag.name)
        # 不在这里提交，让调用者处理提交 