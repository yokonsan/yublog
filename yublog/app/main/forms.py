from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired


class SearchForm(FlaskForm):
    search = StringField('Search', validators=[DataRequired()])


class MobileSearchForm(FlaskForm):
    search = StringField('Search', validators=[DataRequired()])


class CommentForm(FlaskForm):
    nickname = StringField('nickname', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    website = StringField('website')
    comment = TextAreaField('comment', validators=[DataRequired()])


class ArticlePasswordForm(FlaskForm):
    password = StringField('password', validators=[DataRequired()])

