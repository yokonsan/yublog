from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    TextAreaField,
    Field,
)
from wtforms.validators import DataRequired

from yublog.utils.times import nowstr


class FormMixin:
    """mixin some method"""

    @property
    def filter_fields(self):
        return {
            "csrf_token",
            "submit",
            "save_draft",
        }

    @property
    def ins_fields(self):
        return set()

    def __fields(self):
        try:
            fields = getattr(self, "data").keys()
        except AttributeError:
            fields = (k for k, v in self.__dict__.items() if isinstance(v, Field))

        return fields

    def to_form(self, item, **kwargs):
        for field in filter(
                lambda x: x not in (self.filter_fields | self.ins_fields),
                self.__fields()
        ):
            f = getattr(self, field)

            if field in kwargs:
                f.data = kwargs[field]
            else:
                f.data = getattr(item, field)

    def to_model(self, item, **kwargs):
        for field in filter(
                lambda x: x not in (self.filter_fields | self.ins_fields),
                self.__fields()
        ):
            if field in kwargs:
                setattr(item, field, kwargs[field])
            else:
                form = getattr(self, field)
                setattr(item, field, form.data)

    def new_model(self, model, **kwargs):
        kws = {}
        for field in filter(
                lambda x: x not in (self.filter_fields | self.ins_fields),
                self.__fields()
        ):
            kws[field] = getattr(self, field).data

        if kwargs:
            kws.update(kwargs)
        return model(**kws)


class AdminLogin(FlaskForm, FormMixin):
    username = StringField("username", validators=[DataRequired()])
    password = PasswordField("password", validators=[DataRequired()])
    remember_me = BooleanField("remember", default=False)


class AdminWrite(FlaskForm, FormMixin):
    title = StringField("title", validators=[DataRequired()])
    create_time = StringField("datetime", validators=[DataRequired()], default=nowstr(fmt="%Y-%m-%d"))
    tags = StringField("tag", validators=[DataRequired()])
    category = StringField("category", validators=[DataRequired()])
    url_name = StringField("urlName", validators=[DataRequired()])
    body = TextAreaField("body", validators=[DataRequired()])

    save_draft = SubmitField("save")
    submit = SubmitField("submit")


class AddPageForm(FlaskForm, FormMixin):
    title = StringField("title", validators=[DataRequired()])
    url_name = StringField("url_name", validators=[DataRequired()])
    body = TextAreaField("body", validators=[DataRequired()])
    enable_comment = BooleanField("can_comment")
    show_nav = BooleanField("is_nav")
    submit = SubmitField("submit")


class SocialLinkForm(FlaskForm, FormMixin):
    link = StringField("url", validators=[DataRequired()])
    name = StringField("name", validators=[DataRequired()])
    submit = SubmitField("submit")


class FriendLinkForm(FlaskForm, FormMixin):
    link = StringField("url", validators=[DataRequired()])
    name = StringField("name", validators=[DataRequired()])
    info = StringField("info", validators=[DataRequired()])
    submit2 = SubmitField("submit2")

    @property
    def ins_fields(self):
        return {"submit2"}


class AdminSiteForm(FlaskForm, FormMixin):
    site_name = StringField("name", validators=[DataRequired()])
    site_title = StringField("title", validators=[DataRequired()])

    username = StringField("username", validators=[DataRequired()])
    profile = StringField("profile", validators=[DataRequired()])

    record_info = StringField("record info")


class TalkForm(FlaskForm):
    talk = TextAreaField("talk", validators=[DataRequired()])


class ColumnForm(FlaskForm, FormMixin):
    title = StringField("column", validators=[DataRequired()])
    create_time = StringField("datetime", validators=[DataRequired()], default=nowstr(fmt="%Y-%m-%d"))
    url_name = StringField("urlName", validators=[DataRequired()])
    password = StringField("password")
    body = TextAreaField("body", validators=[DataRequired()])
    submit = SubmitField("submit")

    @property
    def ins_fields(self):
        return {"password"}


class ColumnArticleForm(FlaskForm, FormMixin):
    title = StringField("title", validators=[DataRequired()])
    create_time = StringField("datetime", validators=[DataRequired()], default=nowstr(fmt="%Y-%m-%d"))
    body = TextAreaField("body", validators=[DataRequired()])
    secrecy = BooleanField("secrecy")
    submit = SubmitField("submit")


class SideBoxForm(FlaskForm, FormMixin):
    title = StringField("title")
    body = TextAreaField("body", validators=[DataRequired()])
    is_advertising = BooleanField("is_advertising")
    submit = SubmitField("submit")


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField("Old password", validators=[DataRequired()])
    password = PasswordField("New password", validators=[DataRequired()])
    password2 = PasswordField("Confirm new password", validators=[DataRequired()])


class SearchForm(FlaskForm):
    search = StringField("Search", validators=[DataRequired()])


class MobileSearchForm(FlaskForm):
    search = StringField("Search", validators=[DataRequired()])


class CommentForm(FlaskForm, FormMixin):
    nickname = StringField("nickname", validators=[DataRequired()])
    email = StringField("email", validators=[DataRequired()])
    website = StringField("website")
    comment = TextAreaField("comment", validators=[DataRequired()])


class ArticlePasswordForm(FlaskForm):
    password = StringField("password", validators=[DataRequired()])


class AddImagePathForm(FlaskForm):
    path_name = StringField("new path", validators=[DataRequired()])
