from functools import partial

from yublog.models import Article, Column, Post
from yublog.utils.as_sync import sync_request_context
from yublog.utils.cache import cache_operate, CacheType, CacheKey
from yublog.utils.functools import get_pagination


def get_posts():
    def filter_by():
        posts = []
        for p in Post.query\
                     .filter_by(draft=False)\
                     .order_by(Post.create_time.desc())\
                     .all():
            p.comment_count = len(comment_cache(p))
            posts.append(p)

        return posts

    return cache_operate.getset(
        CacheType.POST,
        CacheKey.POSTS,
        callback=filter_by
    )


def get_model_cache(typ, key):
    """获取博客文章缓存"""
    return cache_operate.getset(
        typ,
        key,
        callback=partial(set_model_cache, typ=typ, key=key)
    )


def set_model_cache(typ, key):
    """设置博客文章缓存"""
    data = {}
    if typ == CacheType.POST:
        data = _generate_post_cache(key)
    elif typ == CacheType.ARTICLE:
        data = _generate_article_cache(key)

    return data


def _generate_post_cache(field):
    def linked_post(p):
        return {
            "year": p.year,
            "month": p.month,
            "url": p.url_name,
            "title": p.title
        }

    *_, field = field.split("_")
    cur = Post.query.filter_by(url_name=field).first_or_404()
    posts = get_posts()
    cur_idx = posts.index(cur)

    cur.next_post = linked_post(posts[cur_idx+1]) if posts[-1] != cur else None
    cur.prev_post = linked_post(posts[cur_idx-1]) if posts[0] != cur else None
    cur.comment_count = len(comment_cache(cur))
    return cur


def _generate_article_cache(field):
    def linked_article(a):
        return {
            "id": a.id,
            "title": a.title
        }
    
    cur = Article.query.get_or_404(field)
    cur_column = Column.query.get_or_404(cur.column_id)

    articles = cur_column.articles.all()
    cur_idx = articles.index(cur)

    cur.next_article = linked_article(articles[cur_idx+1]) if articles[-1] != cur else None
    cur.prev_article = linked_article(articles[cur_idx-1]) if articles[0] != cur else None
    return cur


def comment_cache(model):
    def filter_by():
        comments = getattr(model, "comments")  # 直接抛异常
        if comments:
            comments = [{c: c.replies} for c in comments if c.disabled and c.replied_id is None]
            comments.sort(key=lambda item: list(item.keys())[0], reverse=True)
        return comments or []

    return cache_operate.getset(
        CacheType.COMMENT,
        f"{model.__tablename__}:{model.id}",
        callback=filter_by
    )


def column_cache(url_name):
    return cache_operate.getset(
        CacheType.COLUMN,
        url_name,
        callback=lambda: Column.query
                               .filter_by(url_name=url_name)
                               .first_or_404()
    )


def articles_cache(column_id):
    return cache_operate.getset(
        CacheType.COLUMN,
        f"{column_id}:articles",
        callback=lambda: Article.query
                                .filter_by(column_id=column_id)
                                .order_by(Article.id.desc())
                                .all()
    )


def comment_pagination_kwargs(model, cur_page, per):
    comments = comment_cache(model)

    counts = len(comments)
    max_page, cur_page = get_pagination(counts, per, cur_page)
    start_idx = per * (cur_page - 1)
    comments = comments[start_idx:start_idx + per]

    return dict(
        comments=comments,
        counts=counts,
        max_page=max_page,
        cur_page=cur_page,
        pagination=range(1, max_page + 1)
    )


def post_pagination_kwargs(cur_page, per):
    posts = get_posts()

    counts = len(posts)
    max_page, cur_page = get_pagination(counts, per, cur_page)
    start_idx = per * (cur_page - 1)
    posts = [
        get_model_cache(CacheType.POST, f"{p.year}_{p.month}_{p.url_name}")
        for p in posts[start_idx:start_idx + per]
    ]

    return dict(
        posts=posts,
        counts=counts,
        max_page=max_page,
        cur_page=cur_page,
        pagination=range(1, max_page + 1)
    )


def clean_post_relative_cache():
    @sync_request_context
    def _clean_post_relative_cache():
        cache_operate.clean(CacheType.POST)
        cache_operate.clean(CacheType.GLOBAL, CacheKey.TAGS)
        cache_operate.clean(CacheType.GLOBAL, CacheKey.CATEGORIES)
        cache_operate.incr(CacheType.GLOBAL, CacheKey.POST_COUNT)

    return _clean_post_relative_cache()
