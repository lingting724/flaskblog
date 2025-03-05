from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SelectMultipleField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_ckeditor import CKEditorField
from flask_wtf.file import FileField, FileAllowed

class CommentForm(FlaskForm):
    content = TextAreaField('评论内容', validators=[DataRequired(), Length(1, 1000)])
    submit = SubmitField('提交评论')

class SearchForm(FlaskForm):
    q = StringField('搜索', validators=[DataRequired()])
    submit = SubmitField('搜索')

class PostForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(1, 128)])
    summary = TextAreaField('摘要', validators=[Length(0, 200)])
    category_id = SelectField('分类', coerce=int, validators=[DataRequired()])
    tags = SelectMultipleField('标签', coerce=int)
    content = TextAreaField('内容', validators=[DataRequired()])
    cover = FileField('封面图', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '只允许上传图片文件!')
    ])
    is_published = BooleanField('立即发布')
    submit = SubmitField('保存')

class CategoryForm(FlaskForm):
    name = StringField('分类名称', validators=[DataRequired(), Length(1, 64)])
    submit = SubmitField('创建分类')

class TagForm(FlaskForm):
    name = StringField('标签名称', validators=[DataRequired(), Length(1, 64)])
    submit = SubmitField('创建标签') 