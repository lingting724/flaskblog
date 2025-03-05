import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models.user import User
from app.models.post import Post, Category, Tag
from app.models.comment import Comment
from faker import Faker
import random
import os
from slugify import slugify

fake = Faker('zh_CN')

def init_data():
    """初始化数据（生成slug等）"""
    # 为所有分类生成slug
    for category in Category.query.all():
        if not category.slug:
            category.generate_slug()
    
    # 为所有标签生成slug
    for tag in Tag.query.all():
        if not tag.slug:
            tag.generate_slug()
    
    # 为所有文章生成slug
    for post in Post.query.all():
        if not post.slug:
            post.generate_slug()
    
    db.session.commit()

@click.command('init-db')
@with_appcontext
def init_db_command():
    """初始化数据库"""
    try:
        # 确保instance目录存在
        from flask import current_app
        os.makedirs(current_app.instance_path, exist_ok=True)
        
        # 创建数据库表
        db.create_all()
        
        # 初始化数据
        init_data()
        
        click.echo('数据库初始化完成。')
    except Exception as e:
        click.echo(f'初始化数据库时出错: {e}')

@click.command('create-admin')
@click.option('--auto', is_flag=True, help='Automatically use default admin credentials')
@with_appcontext
def create_admin(auto=False):
    """创建管理员账户"""
    print("创建管理员账户...")
    
    # 检查数据库表
    print("确保数据库表已创建")
    
    # 检查是否已存在管理员
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        # 如果用户存在但不是管理员，则设置为管理员
        if not admin.is_admin:
            admin.is_admin = True
            try:
                db.session.commit()
                print(f"已将用户 {admin.username} 设置为管理员!")
            except Exception as e:
                db.session.rollback()
                print(f"设置管理员失败: {str(e)}")
        else:
            print("管理员账户已存在")
        return

    # 创建新管理员
    if auto:
        # 使用默认值自动创建
        username = 'admin'
        password = '123456'
        email = '1043744584@qq.com'
    else:
        # 交互式创建
        use_default = input("是否使用默认管理员账户? (admin/123456/1043744584@qq.com) [Y/n]: ")
        if use_default.lower() != 'n':
            username = 'admin'
            password = '123456'
            email = '1043744584@qq.com'
        else:
            username = input("请输入管理员用户名: ")
            password = input("请输入管理员密码: ")
            email = input("请输入管理员邮箱: ")

    # 创建管理员用户
    new_admin = User(
        username=username,
        email=email,
        is_admin=True
    )
    new_admin.set_password(password)
    
    try:
        db.session.add(new_admin)
        db.session.commit()
        print(f"管理员账户 {username} 创建成功!")
    except Exception as e:
        db.session.rollback()
        print(f"创建管理员账户失败: {str(e)}")

@click.command('init-data')
@with_appcontext
def init_data_command():
    """生成测试数据"""
    try:
        # 获取或创建管理员用户
        admin = User.query.filter_by(email='1043744584@qq.com').first()
        if not admin:
            admin = User(
                username='admin',
                email='1043744584@qq.com',
                is_admin=True
            )
            admin.set_password('123456')
            db.session.add(admin)
            db.session.flush()

        # 创建默认分类
        categories = []
        category_names = ['技术', '生活', '随笔', '读书', '音乐']
        for name in category_names:
            # 检查分类是否已存在
            category = Category.query.filter_by(name=name).first()
            if not category:
                category = Category(
                    name=name,
                    author_id=admin.id  # 使用 author_id 而不是 author
                )
                db.session.add(category)
                db.session.flush()
            elif not category.author_id:  # 如果是已存在的分类但没有作者
                category.author_id = admin.id
            categories.append(category)
        
        # 创建默认标签
        tags = []
        tag_names = ['Python', 'Flask', 'Web开发', '编程', '数据库', 
                    '前端', '后端', 'Linux', '开源', '人工智能']
        for name in tag_names:
            # 检查标签是否已存在
            tag = Tag.query.filter_by(name=name).first()
            if not tag:
                tag = Tag(name=name, author_id=admin.id)  # 使用 author_id
                db.session.add(tag)
                db.session.flush()
            elif not tag.author_id:  # 如果是已存在的标签但没有作者
                tag.author_id = admin.id
            tags.append(tag)
        
        # 生成测试文章
        for i in range(50):
            title = fake.sentence()
            post = Post(
                title=title,
                slug=None,  # 让模型自动生成 slug
                summary=fake.text(max_nb_chars=200),
                content='\n\n'.join(fake.paragraphs(nb=5)),
                author=admin,  # Post模型可以直接使用author关系
                category=random.choice(categories),
                is_published=random.choice([True, True, True, False]),
                view_count=random.randint(0, 1000)
            )
            # 随机添加1-4个标签
            post.tags = random.sample(tags, random.randint(1, 4))
            db.session.add(post)
        
        # 生成测试评论
        posts = Post.query.all()
        for i in range(200):
            post = random.choice(posts)
            comment = Comment(
                content=fake.paragraph(),
                author=admin,
                post=post,
                is_approved=random.choice([True, True, True, False])
            )
            db.session.add(comment)
        
        db.session.commit()
        click.echo('测试数据生成成功！')
        
    except Exception as e:
        db.session.rollback()
        click.echo(f'生成测试数据时出错: {e}')

def init_app(app):
    """注册命令"""
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin)
    app.cli.add_command(init_data_command) 