from flask import abort

from yublog.models import Post
from yublog.caches import cache_tool
from yublog.exceptions import NoPostException


CACHE_MODEL_TYPES = ['post', 'article']
class ModelType:
    POST = 'post'
    ARTICLE = 'article'


def _generate_post_cache(field):
    def linked_post_data(p):
        return {
            'year': p.year,
            'month': p.month,
            'url': p.url_name,
            'title': p.title
        }
    
    cur = Post.query.filter_by(url_name=field).first()
    if not cur: abort(404)
    
    posts = Post.query.filter_by(draft=False).order_by(Post.timestamp.desc()).all()
    tags = cur.tags.split(',')
    data = cur.to_dict()

    _next = linked_post_data(posts[posts.index(cur) + 1]) if posts[-1] != cur else None
    _prev = linked_post_data(posts[posts.index(cur) - 1]) if posts[0] != cur else None
    data.update({
        'tags': tags,
        'next_post': _next,
        'prev_post': _prev
    })
    return data


def get_model_cache(key):
    """获取博客文章缓存"""
    data = cache_tool.get(key)
    return data if data else set_model_cache(key)


def set_model_cache(key):
    """设置博客文章缓存"""
    _type, _, _, query_field = key.split('_')
    if _type not in CACHE_MODEL_TYPES:
        raise NoPostException('Set the post cache exception.')
    
    if _type == ModelType.POST:
        data = _generate_post_cache(query_field)

    cache_tool.set(key, data, timeout=60 * 60 * 24 * 30)
    return data


def update_first_cache():
    """在新文章更新后，清掉最近一篇文章的缓存"""
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    if len(posts) > 1:
        first_post = posts[1]
        cache_key = '_'.join(map(str, ['post', first_post.year, first_post.month, first_post.url_name]))
        cache_tool.clean(cache_key)
    return True
