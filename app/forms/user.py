from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_login import current_user
from app.models.user import User

class ProfileForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(3, 64)])
    email = StringField('邮箱', validators=[DataRequired(), Email(), Length(1, 120)])
    bio = TextAreaField('个人简介', validators=[Length(0, 256)])
    avatar = FileField('头像', validators=[FileAllowed(['jpg', 'png', 'gif'], '只允许上传图片!')])
    submit = SubmitField('保存修改')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('该用户名已被使用')
    
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('该邮箱已被注册')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('原密码', validators=[DataRequired()])
    new_password = PasswordField('新密码', validators=[DataRequired(), Length(6, 128)])
    new_password2 = PasswordField('确认新密码', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('修改密码')

class NotificationSettingsForm(FlaskForm):
    notify_followed = BooleanField('有人关注我时通知')
    notify_comment = BooleanField('文章收到评论时通知')
    notify_reply = BooleanField('收到回复时通知')
    show_email = BooleanField('公开显示邮箱')
    show_following = BooleanField('公开显示关注列表')
    submit = SubmitField('保存设置') 