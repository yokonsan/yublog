from collections import OrderedDict
from flask import redirect, request, g, jsonify, current_app, render_template, url_for

from yublog.caches import cache_tool, global_cache_key
from yublog.extensions import db
from yublog.models import Post, Comment, Page, Category, Tag, Talk, SiteLink, LoveMe
from yublog.views import main_bp
from yublog.views.utils.comment_utils import CommentUtils
from yublog.views.utils.model_cache_utils import get_model_cache


@main_bp.route('/')
@main_bp.route('/index')
def index():
    _page = request.args.get('page', 1, type=int)
    per_page = current_app.config['POSTS_PER_PAGE']

    _posts = Post.query.filter_by(draft=False).order_by(Post.timestamp.desc())
    counts = _posts.count()
    max_page = counts // per_page + 1 if counts % per_page != 0 else counts // per_page
    post_list = _posts.limit(per_page).offset((_page - 1) * per_page).all()
    posts = []
    for p in post_list:
        cache_key = '_'.join(map(str, ['post', p.year, p.month, p.url_name]))
        # print(f'key: {cache_key}')
        posts.append(get_model_cache(cache_key))
    return render_template('main/index.html', title='首页',
                           posts=posts, page=_page, max_page=max_page,
                           pagination=range(1, max_page + 1))


@main_bp.route('/<int:year>/<int:month>/<post_url>/')
def post(year, month, post_url):
    cache_key = '_'.join(map(str, ['post', year, month, post_url]))
    _post = get_model_cache(cache_key)

    page_cnt = request.args.get('page', 1, type=int)
    if page_cnt == -1:
        counts = _post.get('comment_count', 0)
        page_cnt = (counts - 1) / current_app.config['COMMENTS_PER_PAGE'] + 1

    pagination = Comment.query.filter_by(post_id=_post['id'], disabled=True, replied_id=None) \
        .order_by(Comment.timestamp.desc()) \
        .paginate(page_cnt, per_page=current_app.config['COMMENTS_PER_PAGE'], error_out=False)
    comments = pagination.items

    return render_template('main/post.html', post=_post, title=_post['title'],
                           pagination=pagination, comments=comments,
                           counts=len(comments), meta_tags=','.join(_post['tags']))


@main_bp.route('/page/<page_url>/')
def page(page_url):
    _page = Page.query.filter_by(url_name=page_url).first()
    p = request.args.get('page', 1, type=int)
    if p == -1:
        counts = _page.comments.count()
        p = (counts - 1) / current_app.config['COMMENTS_PER_PAGE'] + 1
    pagination = Comment.query.filter_by(page_id=_page.id, disabled=True, replied_id=None).order_by(
        Comment.timestamp.desc()).paginate(
        p, per_page=current_app.config['COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items

    return render_template('main/page.html', page=_page, title=_page.title,
                           pagination=pagination, comments=pagination.items,
                           counts=len(comments))


@main_bp.route('/tag/<tag_name>/')
def tag(tag_name):
    Tag.query.filter_by(tag=tag_name).first()

    all_posts = Post.query.filter_by(draft=False).order_by(Post.timestamp.desc()).all()
    posts = (p for p in all_posts if p.tag_in_post(tag_name))

    return render_template('main/tag.html', tag=tag_name,
                           posts=posts, title='标签：{}'.format(tag_name))


@main_bp.route('/category/<category_name>/')
def category(category_name):
    _category = Category.query.filter_by(category=category_name, is_show=True).first()

    posts = Post.query.filter_by(category=_category,
                                 draft=False).order_by(Post.timestamp.desc()).all()
    return render_template('main/category.html', category=_category,
                           posts=posts, title='分类：{}'.format(_category.category))


@main_bp.route('/archives/')
def archives():
    count = Post.query.filter_by(draft=False).count()
    page_cnt = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(draft=False) \
        .order_by(Post.timestamp.desc()) \
        .paginate(page_cnt, error_out=False,
                  per_page=current_app.config['ARCHIVES_POSTS_PER_PAGE'])
    posts = pagination.items
    data = OrderedDict()
    for p in posts:
        data.setdefault(p.year, []).append(p)

    return render_template('main/archives.html', title='归档', posts=posts,
                           data=data, count=count, pagination=pagination)


@main_bp.route('/search/', methods=['POST'])
def search():
    if g.search_form.validate_on_submit():
        query = g.search_form.search.data
        return redirect(url_for('main.search_result', keywords=query))

    elif g.search_form2.validate_on_submit():
        query = g.search_form2.search.data
        return redirect(url_for('main.search_result', keywords=query))


# /search-result?keywords=query
@main_bp.route('/search-result')
def search_result():
    query = request.args.get('keywords')
    page_cnt = request.args.get('page', 1, type=int)
    pagination = Post.query.whooshee_search(query) \
        .order_by(Post.id.desc()) \
        .paginate(page_cnt, error_out=False,
                  per_page=current_app.config['SEARCH_POSTS_PER_PAGE'])
    results = (p for p in pagination.items if p.draft is False)

    return render_template('main/results.html', results=results,
                           query=query, pagination=pagination,
                           title='{}的搜索结果'.format(query))


# 侧栏 love me 插件
@main_bp.route('/loveme', methods=['POST'])
def love_me():
    data = request.get_json()
    if data.get('i_am_handsome', '') == 'yes':
        # 更新缓存
        global_cache = cache_tool.get(cache_tool.GLOBAL_KEY)
        global_cache[global_cache_key.LOVE_COUNT] += 1
        cache_tool.set(cache_tool.GLOBAL_KEY, global_cache)
        love_me_counts = LoveMe.query.first()
        love_me_counts.love_count += 1

        db.session.add(love_me_counts)
        db.session.commit()
        return jsonify(counts=love_me_counts.love_count)
    return jsonify(you_are_sb='yes')


@main_bp.route('/<target_type>/<target_id>/comment', methods=['POST'])
def comment(target_type, target_id):
    form = request.get_json()
    data = CommentUtils(target_type, form).save_comment(target_id)

    # todo
    return jsonify(nickname=data['nickname'], email=data['email'],
                   website=data['website'], body=data['body'])


@main_bp.route('/talk')
def talk():
    talks = Talk.query.order_by(Talk.timestamp.desc()).all()
    data = OrderedDict()
    for t in talks:
        data.setdefault(t.year, []).append(t)

    return render_template('main/talk.html', title='说说', data=data)


# friend link page
@main_bp.route('/friends')
def friends():
    friend_links = SiteLink.query.filter_by(is_friend=True).order_by(SiteLink.id.desc()).all()
    great_links = (link for link in friend_links if link.is_great is True)
    bad_links = (link for link in friend_links if link.is_great is False)

    return render_template('main/friends.html', title="朋友",
                           great_links=great_links, bad_links=bad_links)
