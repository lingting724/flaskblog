from app import db
from datetime import datetime

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    type = db.Column(db.String(20))  # 通知类型: comment, follow, favorite 等
    
    # 外键关联
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_notification_user'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', name='fk_notification_post'))
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id', name='fk_notification_comment'))
    
    # 关系
    post = db.relationship('Post', backref=db.backref('notifications', lazy='dynamic'))
    comment = db.relationship('Comment', backref=db.backref('notifications', lazy='dynamic'))

    def __repr__(self):
        return f'<Notification {self.id}>' 