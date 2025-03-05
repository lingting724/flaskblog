from flask import current_app
from flask import url_for
from flask_mail import Message
from threading import Thread
from app import mail
from flask import render_template
from datetime import datetime

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, body, html=None):
    msg = Message(
        subject=subject,
        recipients=recipients,
        body=body,
        html=html,
        sender=current_app.config['MAIL_USERNAME']
    )
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()

def send_verification_code(email, code):
    subject = '验证码 - Flask博客系统'
    body = f'您的验证码是：{code}\n该验证码10分钟内有效。'
    html = f'''
    <h1>验证码</h1>
    <p>您的验证码是：<strong>{code}</strong></p>
    <p>该验证码10分钟内有效。</p>
    <p>如果这不是您的操作，请忽略此邮件。</p>
    '''
    send_email(subject, [email], body, html)

def send_password_reset_email(user):
    """发送密码重置邮件"""
    token = user.get_reset_password_token()
    reset_url = f'http://192.168.21.4:5000{url_for("auth.reset_password", token=token)}'
    
    # 渲染HTML模板
    html = render_template('email/reset_password.html',
                         username=user.username,
                         reset_url=reset_url,
                         year=datetime.now().year)
    
    # 简单文本版本
    text = f'''亲爱的 {user.username}：

要重置您的密码，请访问以下链接：

{reset_url}

如果您没有请求重置密码，请忽略此邮件。
此链接将在10分钟后失效。

Flask博客系统
'''
    
    send_email(
        subject='[Flask博客] 重置您的密码',
        recipients=[user.email],
        body=text,
        html=html
    )

def send_notification_email(user, title, content, url):
    """发送通知邮件"""
    msg = Message(
        subject=title,
        recipients=[user.email]
    )
    msg.html = render_template(
        'email/notification.html',
        title=title,
        content=content,
        url=url,
        year=datetime.now().year
    )
    
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start() 