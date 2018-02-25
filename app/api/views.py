from flask import jsonify

from . import api
from ..models import *


"""
api 路由：
    get_posts(): 返回所有博客文章
    get_post(id): 返回指定 id 的文章
    get_tags(): 返回所有博客标签
    get_tag_posts(tag): 返回指定标签的文章
    get_categories(): 返回所有博客分类
    get_category_posts(cate): 返回指定分类的文章
    get_shuos(): 返回所有说说
"""


@api.route('/posts')
def get_posts():
    pass


@api.route('/post/<int:id>')
def get_post(id):
    pass


@api.route('/tags')
def get_tags():
    pass


@api.route('/tag/<tag>')
def get_tag_posts(tag):
    pass


@api.route('/categories')
def get_categories():
    pass


@api.route('/category/<category>')
def get_category_posts(category):
    pass


@api.route('shuos')
def get_shuos():
    pass


