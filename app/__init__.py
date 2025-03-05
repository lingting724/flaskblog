import os
from flask import Flask
from config import Config
from app.extensions import db, migrate, login_manager, mail, moment, ckeditor, admin

def create_app(config_class=Config):
    app = Flask(__name__)
    
    # 确保instance目录存在
    os.makedirs(app.instance_path, exist_ok=True)
    
    app.config.from_object(config_class)
    
    # 从环境变量读取配置
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    
    # 确保上传目录存在
    upload_path = os.path.join(app.static_folder, app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_path, exist_ok=True)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    ckeditor.init_app(app)
    admin.init_app(app)
    
    # 设置登录视图
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = 'info'
    
    # 注册蓝图
    from app.controllers.auth import auth_bp
    from app.controllers.blog import blog_bp
    from app.controllers.user import user_bp
    from app.controllers.admin import admin_bp
    from app.controllers.errors import errors_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(admin_bp, url_prefix='/manage')
    app.register_blueprint(errors_bp)
    
    # 注册命令
    from app import commands
    commands.init_app(app)
    
    return app

# 导入模型以便迁移可以检测到
from app.models import user, post, comment


