from yublog.models import Article, Column, Post
from yublog.utils.cache import cache_operate, CacheType


def get_model_cache(typ, key):
    """获取博客文章缓存"""
    data = cache_operate.get(typ, key)
    return data if data else set_model_cache(typ, key)


def set_model_cache(typ, key):
    """设置博客文章缓存"""
    *_, query_field = key.split("_")

    data = {}
    if typ == CacheType.POST.name:
        data = _generate_post_cache(query_field)
    elif typ == CacheType.ARTICLE.name:
        data = _generate_article_cache(query_field)
    elif typ == CacheType.COLUMN.name:
        data = _generate_column_cache(query_field)

    cache_operate.set(typ, key, data)
    return data


def update_linked_cache(typ, cur):
    """在新文章更新后，清掉最近一篇文章的缓存"""
    posts = Post.query.filter_by(draft=False).order_by(Post.create_time.desc()).all()
    idx = posts.index(cur)
    prev_post = posts[idx-1] if idx > 0 else None
    next_post = posts[idx+1] if idx < len(posts)-1 else None
    if prev_post:
        cache_operate.clean(typ, "_".join(map(str, [prev_post.year, prev_post.month, prev_post.url_name])))
    if next_post:
        cache_operate.clean(typ, "_".join(map(str, [next_post.year, next_post.month, next_post.url_name])))
    return True


def _generate_post_cache(field):
    def linked_post_data(p):
        return {
            "year": p.year,
            "month": p.month,
            "url": p.url_name,
            "title": p.title
        }
    
    cur = Post.query.filter_by(url_name=field).first_or_404()

    posts = Post.query.filter_by(draft=False).order_by(Post.create_time.desc()).all()
    tags = cur.tags.split(",")
    data = cur.to_dict()

    _next = linked_post_data(posts[posts.index(cur)+1]) if posts[-1] != cur else None
    _prev = linked_post_data(posts[posts.index(cur)-1]) if posts[0] != cur else None
    data.update({
        "tags": tags,
        "next_post": _next,
        "prev_post": _prev
    })
    return data


def _generate_article_cache(field):
    def linked_article_data(a):
        return {
            "id": a.id,
            "title": a.title
        }
    
    cur = Article.query.get_or_404(field)
    cur_column = Column.query.get_or_404(cur.column_id)
    column_cache = get_model_cache(CacheType.COLUMN.name, cur_column.url_name)

    articles = column_cache["articles"]
    data = cur.to_dict()

    _next = linked_article_data(articles[articles.index(cur)+1]) if articles[-1] != cur else None
    _prev = linked_article_data(articles[articles.index(cur)-1]) if articles[0] != cur else None
    data.update({
        "next_article": _next,
        "prev_article": _prev
    })
    return data


def _generate_column_cache(field):
    def linked_article_data(a):
        return {
            "id": a.id,
            "title": a.title
        }
    
    cur = Column.query.filter_by(url_name=field).first_or_404()
    data = cur.to_dict()

    _articles = Article.query.filter_by(
        column_id=cur.id).order_by(Article.timestamp.asc()).all()
    articles = []

    for i, a in enumerate(_articles):
        article = a.to_dict()
        _prev = None if i == 0 else linked_article_data(_articles[i-1])
        _next = None if i == len(_articles)-1 else linked_article_data(_articles[i+1])
        article.update({
            "next_article": _next,
            "prev_article": _prev
        })
        articles.append(article)
    data["articles"] = articles
    return data
