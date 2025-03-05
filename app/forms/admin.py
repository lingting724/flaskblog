from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SelectMultipleField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from flask_ckeditor import CKEditorField

class PostForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(1, 120)])
    summary = TextAreaField('摘要', validators=[Length(0, 200)])
    content = CKEditorField('内容', validators=[DataRequired()])
    category_id = SelectField('分类', coerce=int, validators=[DataRequired()])
    tags = SelectMultipleField('标签', coerce=int)
    cover = FileField('封面图', validators=[FileAllowed(['jpg', 'png'], '只允许上传jpg或png格式的图片!')])
    is_published = BooleanField('发布')
    submit = SubmitField('保存')

class CategoryForm(FlaskForm):
    name = StringField('分类名称', validators=[DataRequired(), Length(1, 30)])
    description = TextAreaField('描述', validators=[Optional(), Length(0, 200)])
    submit = SubmitField('保存')

class TagForm(FlaskForm):
    name = StringField('标签名称', validators=[DataRequired(), Length(1, 30)])
    submit = SubmitField('保存') 