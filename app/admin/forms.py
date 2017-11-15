from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField, DateTimeField
from wtforms.validators import DataRequired
from flask_pagedown.fields import PageDownField


class AdminLogin(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])

class AdminWrite(FlaskForm):
    title = StringField('title', validators=[DataRequired()])
    time = DateTimeField('datetime', validators=[DataRequired()])
    tags = StringField('tag', validators=[DataRequired()])
    category = StringField('category', validators=[DataRequired()])
    url_name = StringField('urlName', validators=[DataRequired()])
    body = PageDownField('body', validators=[DataRequired()])

    save_draft = SubmitField('save')
    submit = SubmitField('submit')

class EditpostForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired()])
    body = PageDownField('编辑文章', validators=[DataRequired()])
    update = SubmitField('更新')
    submit = SubmitField('发布')
    save_draft = SubmitField('保存')

class AdminProfile(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    profile = StringField('profile', validators=[DataRequired()])

class AddLinkForm(FlaskForm):
    link = StringField('url', validators=[DataRequired()])
    name = StringField('name', validators=[DataRequired()])
    isFriendLink = BooleanField('type')

