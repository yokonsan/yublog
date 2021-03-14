from flask import abort

from yublog.models import Article, Column, Post
from yublog.caches import cache_tool
from yublog.exceptions import NoPostException


class ModelType:
    MODEL_TYPES = ['post', 'article', 'column', 'page']
    POST = 'post'
    ARTICLE = 'article'
    COLUMN = 'column'
    PAGE = 'page'


def get_model_cache(key):
    """获取博客文章缓存"""
    data = cache_tool.get(key)
    return data if data else set_model_cache(key)


def set_model_cache(key):
    """设置博客文章缓存"""
    _type, *_, query_field = key.split('_')
    if _type not in ModelType.MODEL_TYPES:
        raise NoPostException('Set the post cache exception.')
    
    if _type == ModelType.POST:
        data = _generate_post_cache(query_field)
    elif _type == ModelType.ARTICLE:
        data = _generate_article_cache(query_field)
    elif _type == ModelType.COLUMN:
        data = _generate_column_cache(query_field)

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


def _generate_post_cache(field):
    def linked_post_data(p):
        return {
            'year': p.year,
            'month': p.month,
            'url': p.url_name,
            'title': p.title
        }
    
    cur = Post.query.filter_by(url_name=field).first_or_404()

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


def _generate_article_cache(field):
    def linked_article_data(a):
        return {
            'id': a.id,
            'title': a.title
        }
    
    cur = Article.query.get_or_404(field)
    cur_column = Column.query.get_or_404(cur.column_id)
    column_cache = get_model_cache('column_{}'.format(cur_column.url_name))

    articles = column_cache['articles']
    data = cur.to_dict()

    _next = linked_article_data(articles[articles.index(cur) + 1]) if articles[-1] != cur else None
    _prev = linked_article_data(articles[articles.index(cur) - 1]) if articles[0] != cur else None
    data.update({
        'next_article': _next,
        'prev_article': _prev
    })
    return data


def _generate_column_cache(field):
    cur = Column.query.filter_by(url_name=field).first_or_404()
    data = cur.to_dict()

    _articles = Article.query.filter_by(
        column_id=cur.id).order_by(Article.timestamp.asc()).all()
    articles = [a.to_dict() for a in _articles]
    data['articles'] = articles
    return data
