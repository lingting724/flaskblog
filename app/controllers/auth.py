from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models.user import User
from app.forms.auth import LoginForm, RegisterForm, ResetPasswordRequestForm, ResetPasswordForm
from app.utils.email import send_password_reset_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('邮箱或密码不正确', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('blog.index')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='登录', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('blog.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='注册', form=form)

@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
            flash('重置密码的邮件已发送到您的邮箱，请查收。', 'info')
            return redirect(url_for('auth.login'))
        flash('该邮箱未注册。', 'danger')
    return render_template('auth/reset_password_request.html', title='重置密码', form=form)

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        flash('重置链接无效或已过期。', 'danger')
        return redirect(url_for('blog.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('您的密码已重置。', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form) 