from flask import render_template, redirect, request, \
    g, current_app, abort, jsonify

from yublog.app.main import main
from yublog.app.main.forms import SearchForm, MobileSearchForm
from yublog.app.models import *
from yublog.app.utils.tools import asyncio_send
from yublog.app.caches import cache_tool
from yublog.app.exceptions import NoPostException


def get_post_cache(key):
    """获取博客文章缓存"""
    data = cache_tool.get(key)
    return data if data else set_post_cache(key)


def set_post_cache(key):
    """设置博客文章缓存"""
    year, month, url = key.split('_')
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


def _prev_post(post):
    """
    获取本篇文章的上一篇
    :param post: post
    :return: prev post
    """
    post_list = Post.query.order_by(Post.timestamp.desc()).all()
    posts = [post for post in post_list if post.draft is False]
    if posts[0] != post:
        _prev = posts[posts.index(post) - 1]
        return {
            'year': _prev.year,
            'month': _prev.month,
            'url': _prev.url_name,
            'title': _prev.title
        }
    return None


@main.before_request
def before_request():
    g.search_form = SearchForm()
    g.search_form2 = MobileSearchForm()


@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html', title='404'), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    db.session.rollback()
    db.session.commit()
    return render_template('error/500.html', title='500'), 500


@main.route('/')
@main.route('/index')
def index():
    _page = request.args.get('page', 1, type=int)
    per_page = current_app.config['POSTS_PER_PAGE']

    counts = Post.query.filter_by(draft=False).count()
    max_page = counts // per_page + 1 if counts % per_page != 0 else counts // per_page
    post_list = Post.query.order_by(Post.timestamp.desc()).limit(per_page).offset((page - 1) * per_page).all()
    all = (post for post in post_list if post.draft is False)
    posts = []
    for post in all:
        cache_key = '_'.join(map(str, ['post', post.year, post.month, post.url_name]))
        post = get_post_cache(cache_key)
        posts.append(post)
    return render_template('main/index.html', title='首页',
                           posts=posts, page=_page, max_page=max_page,
                           pagination=range(1, max_page + 1))


@main.route('/<int:year>/<int:month>/<article_name>/')
def post(year, month, article_name):
    cache_key = '_'.join(map(str, ['post', year, month, article_name]))
    post = get_post_cache(cache_key)

    page = request.args.get('page', 1, type=int)
    if page == -1:
        counts = post.get('comment_count', 0)
        page = (counts - 1) / current_app.config['COMMENTS_PER_PAGE'] + 1

    pagination = Comment.query.filter_by(post_id=post['id'], isReply=False, disabled=True).order_by(
        Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['COMMENTS_PER_PAGE'],
        error_out=False
    )
    comments = pagination.items
    replys = Comment.query.filter_by(post_id=post['id'], isReply=True, disabled=True).all()
    meta_tags = ','.join(post['tags'])
    return render_template('main/post.html', post=post, title=post['title'],
                           pagination=pagination, comments=comments, replys=replys,
                           counts=len(comments) + len(replys), meta_tags=meta_tags)


@main.route('/page/<page_url>/')
def page(page_url):
    page = Page.query.filter_by(url_name=page_url).first()
    p = request.args.get('page', 1, type=int)
    if p == -1:
        counts = page.comments.count()
        p = (counts - 1) / current_app.config['COMMENTS_PER_PAGE'] + 1
    pagination = Comment.query.filter_by(page=page, isReply=False, disabled=True).order_by(
        Comment.timestamp.desc()).paginate(
        p, per_page=current_app.config['COMMENTS_PER_PAGE'],
        error_out=False
    )
    comments = pagination.items
    replys = page.comments.filter_by(isReply=True, disabled=True).all()

    return render_template('main/page.html', page=page, title=page.title, pagination=pagination,
                           comments=comments, replys=replys, counts=len(comments) + len(replys))


@main.route('/tag/<tag_name>/')
def tag(tag_name):
    tag = tag_name
    all_posts = Post.query.order_by(Post.timestamp.desc()).all()
    posts = (post for post in all_posts if post.tag_in_post(tag) and post.draft is False)

    return render_template('main/tag.html', tag=tag, posts=posts)


@main.route('/category/<category_name>/')
def category(category_name):
    category = Category.query.filter_by(category=category_name).first()

    posts = Post.query.filter_by(category=category, draft=False).order_by(Post.timestamp.desc()).all()
    return render_template('main/category.html',
                           category=category,
                           posts=posts,
                           title='分类：' + category.category)


@main.route('/archives/')
def archives():
    count = Post.query.filter_by(draft=False).count()
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['ACHIVES_POSTS_PER_PAGE'],
        error_out=False)
    posts = (post for post in pagination.items if post.draft is False)
    year = list(set([i.year for i in posts]))[::-1]
    data = {}
    year_post = []
    for y in year:
        for p in posts:
            if y == p.year:
                year_post.append(p)
                data[y] = year_post
        year_post = []

    return render_template('main/archives.html', title='归档', posts=posts,
                           year=year, data=data, count=count,
                           pagination=pagination)


@main.route('/search/', methods=['POST'])
def search():
    if g.search_form.validate_on_submit():
        query = g.search_form.search.data
        return redirect(url_for('main.search_result', keywords=query))

    elif g.search_form2.validate_on_submit():
        query = g.search_form2.search.data
        return redirect(url_for('main.search_result', keywords=query))


# /search-result?keywords=query
@main.route('/search-result')
def search_result():
    query = request.args.get('keywords')
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.whooshee_search(query).order_by(Post.id.desc()).paginate(
        page, per_page=current_app.config['SEARCH_POSTS_PER_PAGE'],
        error_out=False
    )
    # pagination2 = Article.query.whooshee_search(query).order_by(Post.id.desc()).paginate(
    #     page, per_page=current_app.config['SEARCH_POSTS_PER_PAGE'],
    #     error_out=False
    # )
    results = (post for post in pagination.items if post.draft is False)
    return render_template('main/results.html', results=results,
                           query=query, pagination=pagination,
                           title=query + '的搜索结果')


# 侧栏 love me 插件
@main.route('/loveme', methods=['POST'])
def love_me():
    """
    :return: json
    """
    data = request.get_json()
    if data.get('i_am_handsome', '') == 'yes':
        # 更新缓存
        global_cache = cache_tool.get(cache_tool.GLOBAL_KEY)
        global_cache['loves'] += 1
        cache_tool.set(cache_tool.GLOBAL_KEY, global_cache)
        love_me_counts = LoveMe.query.all()[0]
        love_me_counts.loveMe += 1
        db.session.add(love_me_counts)
        db.session.commit()
        return jsonify(counts=love_me_counts.loveMe)
    return jsonify(you_are_sb='yes')


# 保存评论的函数
def save_comment(post, form):
    # 邮件配置
    to_addr = current_app.config['ADMIN_MAIL']
    # 站点链接
    base_url = current_app.config['WEB_URL']

    nickname = form['nickname']
    email = form['email']
    website = form['website'] or None
    com = form['comment']
    # com = form['comment'].replace('<', '&lt;').replace('>', '&gt;') \
    #     .replace('"', '&quot;').replace('\'', '&apos;')
    reply_to = form.get('reply_to', '')
    if reply_to:
        replyName = Comment.query.get(reply_to).author
        if website and len(website) > 4:
            comment = '<p class="reply-header"><a class="comment-user" href="{website}" ' \
                      'target="_blank">{nickname}</a><span>回复</span> {replyName}：</p>\n\n' \
                      '{com}'.format(website=website, nickname=nickname, replyName=replyName, com=com)
        else:
            comment = '<p class="reply-header">{nickname}<span>回复</span>  {replyName}：' \
                      '</p>\n\n{com}'.format(nickname=nickname, replyName=replyName, com=com)

        comment = Comment(comment=comment, author=nickname, email=email,
                          website=website, isReply=True, replyTo=reply_to)
        data = {'nickname': nickname, 'email': email, 'website': website,
                'comment': com, 'is_reply': True, 'reply_to': reply_to}
    else:
        comment = Comment(comment=com, author=nickname, email=email, website=website)
        data = {'nickname': nickname, 'email': email, 'website': website, 'comment': com}

    post_url = ''
    if isinstance(post, Post):
        post_url = 'http://' + '/'.join(map(str, [base_url, post.year, post.month, post.url_name]))
        comment.post = post
    elif isinstance(post, Page):
        post_url = 'http://' + base_url + '/page/' + post.url_name
        comment.page = post
    elif isinstance(post, Article):
        post_url = 'http://' + base_url + '/column/' + post.column.url_name + '/' + str(post.id)
        comment.article = post
    # 发送邮件
    if email != to_addr:
        msg = render_template('admin_mail.html', nickname=nickname,
                              title=post.title, comment=com,
                              email=email, website=website, url=post_url)
        asyncio_send(to_addr, msg)
    db.session.add(comment)
    db.session.commit()
    return data


@main.route('/<url>/comment', methods=['POST'])
def comment(url):
    post = Post.query.filter_by(url_name=url).first()
    if not post:
        post = Page.query.filter_by(url_name=url).first()
    form = request.get_json()
    data = save_comment(post, form)
    if data.get('reply_to'):
        return jsonify(nickname=data['nickname'], email=data['email'],
                       website=data['website'], body=data['comment'],
                       isReply=data['is_reply'], replyTo=data['reply_to'], post=post.title)
    return jsonify(nickname=data['nickname'], email=data['email'],
                   website=data['website'], body=data['comment'], post=post.title)


@main.route('/shuoshuo')
def shuoshuo():
    shuos = Shuoshuo.query.order_by(Shuoshuo.timestamp.desc()).all()
    years = list(set([y.year for y in shuos]))[::-1]
    data = {}
    year_shuo = []
    for y in years:
        for s in shuos:
            if y == s.year:
                year_shuo.append(s)
                data[y] = year_shuo
        year_shuo = []
    return render_template('main/shuoshuo.html', title='说说', years=years, data=data)


# friend link page
@main.route('/friends')
def friends():
    friends = SiteLink.query.filter_by(isFriendLink=True).order_by(SiteLink.id.desc()).all()
    great_links = (link for link in friends if link.isGreatLink is True)
    bad_links = (link for link in friends if link.isGreatLink is False)

    return render_template('main/friends.html', title="朋友",
                           great_links=great_links, bad_links=bad_links)
