from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired


class AdminLogin(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    remember_me = BooleanField('remember', default=False)

class AdminWrite(FlaskForm):
    title = StringField('title', validators=[DataRequired()])
    time = StringField('datetime', validators=[DataRequired()])
    tags = StringField('tag', validators=[DataRequired()])
    category = StringField('category', validators=[DataRequired()])
    url_name = StringField('urlName', validators=[DataRequired()])
    body = TextAreaField('body', validators=[DataRequired()])

    save_draft = SubmitField('save')
    submit = SubmitField('submit')

class AddPageForm(FlaskForm):
    title = StringField('title', validators=[DataRequired()])
    url_name = StringField('url_name', validators=[DataRequired()])
    body = TextAreaField('body', validators=[DataRequired()])
    can_comment = BooleanField('can_comment')
    is_nav = BooleanField('is_nav')
    submit = SubmitField('submit')

class AddLinkForm(FlaskForm):
    link = StringField('url', validators=[DataRequired()])
    name = StringField('name', validators=[DataRequired()])
    isFriendLink = BooleanField('type', default=False)

class AdminSiteForm(FlaskForm):
    site_name = StringField('name', validators=[DataRequired()])
    site_title = StringField('title', validators=[DataRequired()])

    username = StringField('username', validators=[DataRequired()])
    profile = StringField('profile', validators=[DataRequired()])


