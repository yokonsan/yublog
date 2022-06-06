from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    TextAreaField
)
from wtforms.validators import DataRequired


class AdminLogin(FlaskForm):
    username = StringField("username", validators=[DataRequired()])
    password = PasswordField("password", validators=[DataRequired()])
    remember_me = BooleanField("remember", default=False)


class AdminWrite(FlaskForm):
    title = StringField("title", validators=[DataRequired()])
    time = StringField("datetime", validators=[DataRequired()])
    tags = StringField("tag", validators=[DataRequired()])
    category = StringField("category", validators=[DataRequired()])
    url_name = StringField("urlName", validators=[DataRequired()])
    body = TextAreaField("body", validators=[DataRequired()])

    save_draft = SubmitField("save")
    submit = SubmitField("submit")


class AddPageForm(FlaskForm):
    title = StringField("title", validators=[DataRequired()])
    url_name = StringField("url_name", validators=[DataRequired()])
    body = TextAreaField("body", validators=[DataRequired()])
    can_comment = BooleanField("can_comment")
    is_nav = BooleanField("is_nav")
    submit = SubmitField("submit")


class SocialLinkForm(FlaskForm):
    link = StringField("url", validators=[DataRequired()])
    name = StringField("name", validators=[DataRequired()])
    submit = SubmitField("submit")


class FriendLinkForm(FlaskForm):
    link = StringField("url", validators=[DataRequired()])
    name = StringField("name", validators=[DataRequired()])
    info = StringField("info", validators=[DataRequired()])
    submit2 = SubmitField("submit2")


class AdminSiteForm(FlaskForm):
    site_name = StringField("name", validators=[DataRequired()])
    site_title = StringField("title", validators=[DataRequired()])

    username = StringField("username", validators=[DataRequired()])
    profile = StringField("profile", validators=[DataRequired()])

    record_info = StringField("record info")


class TalkForm(FlaskForm):
    talk = TextAreaField("talk", validators=[DataRequired()])


# 专题表单
class ColumnForm(FlaskForm):
    column = StringField("column", validators=[DataRequired()])
    date = StringField("datetime", validators=[DataRequired()])
    url_name = StringField("urlName", validators=[DataRequired()])
    password = StringField("password")
    body = TextAreaField("body", validators=[DataRequired()])
    submit = SubmitField("submit")


class ColumnArticleForm(FlaskForm):
    title = StringField("title", validators=[DataRequired()])
    date = StringField("datetime", validators=[DataRequired()])
    body = TextAreaField("body", validators=[DataRequired()])
    secrecy = BooleanField("secrecy")
    submit = SubmitField("submit")


# 侧栏插件表单
class SideBoxForm(FlaskForm):
    title = StringField("title")
    body = TextAreaField("body", validators=[DataRequired()])
    is_advertising = BooleanField("is_advertising")
    submit = SubmitField("submit")


# 更改密码
class ChangePasswordForm(FlaskForm):
    old_password = PasswordField("Old password", validators=[DataRequired()])
    password = PasswordField("New password", validators=[DataRequired()])
    password2 = PasswordField("Confirm new password", validators=[DataRequired()])


class SearchForm(FlaskForm):
    search = StringField("Search", validators=[DataRequired()])


class MobileSearchForm(FlaskForm):
    search = StringField("Search", validators=[DataRequired()])


class CommentForm(FlaskForm):
    nickname = StringField("nickname", validators=[DataRequired()])
    email = StringField("email", validators=[DataRequired()])
    website = StringField("website")
    comment = TextAreaField("comment", validators=[DataRequired()])


class ArticlePasswordForm(FlaskForm):
    password = StringField("password", validators=[DataRequired()])


class AddImagePathForm(FlaskForm):
    path_name = StringField("new path", validators=[DataRequired()])
