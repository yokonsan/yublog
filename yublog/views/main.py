from collections import OrderedDict
from flask import (
    redirect,
    request,
    g,
    jsonify,
    current_app,
    render_template,
    url_for,
    abort,
)

from yublog.utils.as_sync import sync_copy_app_context
from yublog.utils.cache import cache_operate, CacheKey, CacheType
from yublog.extensions import db
from yublog.models import Post, Category, Tag, Talk, Link, LoveMe, Page
from yublog.utils.functools import get_pagination
from yublog.views import main_bp
from yublog.utils.cache.model import (
    get_posts,
    get_model_cache,
    comment_pagination_kwargs,
    post_pagination_kwargs,
)


@main_bp.route("/")
@main_bp.route("/index")
def index():
    per = current_app.config["POSTS_PER_PAGE"]
    cur_page = request.args.get("page", 1, type=int)

    posts_args = post_pagination_kwargs(cur_page, per)

    return render_template(
        "main/index.html",
        title="首页",
        **posts_args
    )


@main_bp.route("/<int:year>/<int:month>/<post_url>/")
def post(year, month, post_url):
    _post = get_model_cache(
        CacheType.POST,
        f"{year}_{month}_{post_url}"
    )

    per = current_app.config["COMMENTS_PER_PAGE"]
    cur_page = max(request.args.get("page", 1, type=int), 1)

    comment_args = comment_pagination_kwargs(_post, cur_page, per)

    return render_template(
        "main/post.html",
        post=_post,
        title=_post.title,
        **comment_args
    )


@main_bp.route("/page/<page_url>/")
def page(page_url):
    _page = cache_operate.getset(
        CacheType.PAGE,
        f"{page_url}",
        callback=lambda: Page.query.filter_by(url_name=page_url).first_or_404()
    )

    per = current_app.config["COMMENTS_PER_PAGE"]
    cur_page = max(request.args.get("page", 1, type=int), 1)

    comment_args = dict(
        comments=[],
        counts=0,
        max_page=0,
        cur_page=cur_page,
        pagination=range(0)
    )
    if _page.enable_comment:
        comment_args = comment_pagination_kwargs(_page, cur_page, per)

    return render_template(
        "main/page.html",
        page=_page,
        title=_page.title,
        **comment_args
    )


@main_bp.route("/tag/<tag_name>/")
def tag(tag_name):
    _tag = cache_operate.getset(
        CacheType.POST,
        f"tag:{tag_name}",
        callback=lambda: Tag.query
                   .filter_by(tag=tag_name)
                   .first_or_404()
    )

    posts = (p for p in get_posts() if p.tag_in_post(tag_name))
    return render_template(
        "main/tag.html",
        tag=tag_name,
        posts=posts,
        title=f"标签：{tag_name}"
    )


@main_bp.route("/category/<category_name>/")
def category(category_name):
    _category = cache_operate.getset(
        CacheType.POST,
        f"category:{category_name}",
        callback=lambda: Category.query
                        .filter_by(category=category_name, is_show=True)
                        .first_or_404()
    )

    posts = (p for p in get_posts() if p.category_name == category_name)
    return render_template(
        "main/category.html",
        category=_category,
        posts=posts,
        title=f"分类：{category_name}"
    )


@main_bp.route("/archives/")
def archives():
    per = current_app.config["ARCHIVES_POSTS_PER_PAGE"]
    cur_page = request.args.get("page", 1, type=int)

    posts_args = post_pagination_kwargs(cur_page, per)

    data = OrderedDict()
    for p in posts_args["posts"]:
        data.setdefault(p.year, []).append(p)

    return render_template(
        "main/archives.html",
        title="归档",
        data=data,
        **posts_args
    )


@main_bp.route("/search/", methods=["POST"])
def search():
    if g.search_form.validate_on_submit():
        query = g.search_form.search.data
        return redirect(url_for("main.search_result", keywords=query))

    elif g.search_form2.validate_on_submit():
        query = g.search_form2.search.data
        return redirect(url_for("main.search_result", keywords=query))


@main_bp.route("/search-result")
def search_result():
    query = request.args.get("keywords")
    cur_page = request.args.get("page", 1, type=int)
    per = current_app.config["SEARCH_POSTS_PER_PAGE"]
    query_session = Post.query \
                        .whooshee_search(query) \
                        .filter_by(draft=False) \
                        .order_by(Post.id.desc())

    counts = query_session.count()
    max_page, cur_page = get_pagination(counts, per, cur_page)
    results = query_session.paginate(cur_page, error_out=False, per_page=per).items

    return render_template(
        "main/results.html",
        title=f"{query}的搜索结果",
        results=results,
        query=query,
        pagination=range(1, max_page + 1),
        cur_page=cur_page,
        max_page=max_page
    )


@main_bp.route("/loveme", methods=["POST"])
def love_me():
    @sync_copy_app_context
    def db_commit():
        love_me_counts = LoveMe.query.first()
        love_me_counts.count += 1

        db.session.add(love_me_counts)
        db.session.commit()
        return

    data = request.get_json()
    if data.get("i_am_handsome", "") == "yes":
        cache_operate.incr(CacheType.GLOBAL, CacheKey.LOVE_COUNT)
        db_commit()

        return jsonify(counts=cache_operate.get(CacheType.GLOBAL, CacheKey.LOVE_COUNT))
    return jsonify(faker="yes")


@main_bp.route("/<target_type>/<target_id>/comment", methods=["POST"])
def comment(target_type, target_id):
    form = request.get_json()

    from yublog.utils.comment import commit_comment
    commit_comment(target_type, form, target_id)

    # todo
    return jsonify(**form)


@main_bp.route("/talk")
def talk():
    talks = cache_operate.getset(
        CacheType.TALK,
        CacheKey.TALKS,
        callback=lambda: Talk.query
                             .order_by(Talk.timestamp.desc())
                             .all()
    )
    data = OrderedDict()
    for t in talks:
        data.setdefault(t.year, []).append(t)

    return render_template(
        "main/talk.html",
        title="说说",
        data=data
    )


@main_bp.route("/friends")
def friends():
    friend_links = cache_operate.getset(
        CacheType.LINK,
        CacheKey.FRIEND_LINKS,
        callback=lambda: Link.query
                             .filter_by(is_friend=True)
                             .order_by(Link.id.desc())
                             .all()
    )
    great_links = (link for link in friend_links if link.is_great)
    bad_links = (link for link in friend_links if not link.is_great)

    return render_template(
        "main/friends.html",
        title="友链",
        great_links=great_links,
        bad_links=bad_links
    )
