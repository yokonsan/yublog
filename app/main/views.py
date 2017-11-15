from flask import render_template, redirect, url_for, request

from .. import db
from . import main
from .forms import *
from ..models import *


@main.route('/')
def index():

    return render_template('index.html')

@main.route('/<int:year>/<int:month>/<article_name>/')
def post(year, month, article_name):
    pass

@main.route('/about/')
def about():
    pass

@main.route('/tag/<tag_name>/')
def tag(tag_name):
    pass

@main.route('/category/<category_name>/')
def category(category_name):
    pass

@main.route('/archives/')
def archives():
    pass

@main.route('/comments/')
def comment():
    pass

@main.route('/search/')
# url_for('main.search', {keywords: xxx})
def search():
    search = request.args.get('keywords')
    pass

