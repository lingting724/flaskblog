from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_ckeditor import CKEditor
from flask_admin import Admin

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
moment = Moment()
ckeditor = CKEditor()
admin = Admin(name='博客管理系统', template_mode='bootstrap4') 