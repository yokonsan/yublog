from flask import Blueprint, abort, render_template, current_app

from yublog.models import *
from yublog.caches import *
from yublog.utils.tools import asyncio_send, regular_url
from yublog.exceptions import NoPostException

main_bp = Blueprint('main', __name__)
column_bp = Blueprint('column', __name__)
api_bp = Blueprint('api', __name__)
admin_bp = Blueprint('admin', __name__)


def get_post_cache(key):
    """获取博客文章缓存"""
    data = cache_tool.get(key)
    return data if data else set_post_cache(key)


def set_post_cache(key):
    """设置博客文章缓存"""
    _, year, month, url = key.split('_')
    time = str(year) + '-' + str(month)
    posts = Post.query.filter_by(url_name=url).all()
    if len(posts) > 1:
        _post = [p for p in posts if time in p.timestamp][0]
    elif len(posts) == 1:
        _post = posts[0]
    else:
        abort(404)
        raise NoPostException('Set the post cache exception.')

    tags = _post.tags.split(',')
    data = _post.to_dict()
    data['tags'] = tags
    data['next_post'] = _next_post(_post)
    data['prev_post'] = _prev_post(_post)

    cache_key = '_'.join(map(str, ['post', year, month, url]))
    cache_tool.set(cache_key, data, timeout=60 * 60 * 24 * 30)
    return data


def _next_post(_post):
    """
    获取本篇文章的下一篇
    :param _post: post
    :return: next post
    """
    post_list = Post.query.order_by(Post.timestamp.desc()).all()
    posts = [p for p in post_list if p.draft is False]
    if posts[-1] != _post:
        _next = posts[posts.index(_post) + 1]
        return {
            'year': _next.year,
            'month': _next.month,
            'url': _next.url_name,
            'title': _next.title
        }
    return None


def _prev_post(_post):
    """
    获取本篇文章的上一篇
    :param post: post
    :return: prev post
    """
    post_list = Post.query.order_by(Post.timestamp.desc()).all()
    posts = [p for p in post_list if p.draft is False]
    if posts[0] != _post:
        _prev = posts[posts.index(_post) - 1]
        return {
            'year': _prev.year,
            'month': _prev.month,
            'url': _prev.url_name,
            'title': _prev.title
        }
    return None


from yublog.views import main, admin, column, site, api, error  # noqa
