from flask import render_template, redirect, url_for, request, \
                g, current_app, abort, jsonify, make_response

from . import main
from .forms import SearchForm
from ..models import *
from ..utils import asyncio_send
from .. import cache


def get_post_cache(key):
    """获取博客文章缓存"""
    data = cache.get(key)
    if data:
        return data
    else:
        items = key.split('_')
        return set_post_cache(items[1], items[2], items[3])

def set_post_cache(year, month, url):
    """设置博客文章缓存"""
    time = str(year) + '-' + str(month)
    posts = Post.query.filter_by(url_name=url).all()
    post = ''
    if len(posts) == 1:
        post = posts[0]
    elif len(posts) > 1:
        post = [i for i in posts if time in i.timestamp][0]
    elif len(posts) < 1:
        abort(404)
    tags = [tag for tag in post.tags.split(',')]
    next_post = nextPost(post)
    prev_post = prevPost(post)
    data = post.to_dict()
    data['tags'] = tags
    data['next_post'] = {
        'year': next_post.year,
        'month': next_post.month,
        'url': next_post.url_name,
        'title': next_post.title
    } if next_post else None
    data['prev_post'] = {
        'year': prev_post.year,
        'month': prev_post.month,
        'url': prev_post.url_name,
        'title': prev_post.title
    } if prev_post else None
    cache_key = '_'.join(map(str, ['post', year, month, url]))
    cache.set(cache_key, data, timeout=60 * 60 * 24 * 30)
    return data

@main.before_request
def before_request():
    g.search_form = SearchForm()
    g.search_form2 = SearchForm()

@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html', title='404'), 404

@main.app_errorhandler(500)
def internal_server_error(e):
    db.session.rollback()
    db.session.commit()
    return render_template('error/500.html', title='500'), 500

# def cache_key(*args, **kwargs):
#     """
#     以
#     自定义缓存键:
#         首页和归档页路由 url 是带参数的分页页数组成：/index?page=2
#         flask-cache 缓存的 key_prefix 默认值获取 path ：/index
#         需要自定义不同页面的 cache_key : /index/page/2
#     """
#     path = request.path
#     args = dict(request.args.items())
#
#     return (path + '/page/' + str(args['page'])) if args else path

@main.route('/')
@main.route('/index')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['POSTS_PER_PAGE']

    counts = Post.query.filter_by(draft=False).count()
    max_page = counts // per_page + 1 if counts%per_page!=0 else counts // per_page
    post_list = Post.query.order_by(Post.timestamp.desc()).limit(per_page).offset((page-1)*per_page).all()
    all = (post for post in post_list if post.draft is False)
    posts = []
    for post in all:
        cache_key = '_'.join(map(str, ['post', post.year, post.month, post.url_name]))
        post = get_post_cache(cache_key)
        posts.append(post)
    return render_template('main/index.html', title='首页',
                           posts=posts, page=page, max_page=max_page,
                           pagination=range(1, max_page+1))

def nextPost(post):
    """
    获取本篇文章的下一篇
    :param post: post
    :return: next post
    """
    post_list = Post.query.order_by(Post.timestamp.desc()).all()
    posts = [post for post in post_list if post.draft is False]
    if posts[-1] != post:
        next_post = posts[posts.index(post) + 1]
        return next_post
    return None
def prevPost(post):
    """
    获取本篇文章的上一篇
    :param post: post
    :return: prev post
    """
    post_list = Post.query.order_by(Post.timestamp.desc()).all()
    posts = [post for post in post_list if post.draft is False]
    if posts[0] != post:
        prev_post = posts[posts.index(post) - 1]
        return prev_post
    return None

@main.route('/<int:year>/<int:month>/<article_name>/')
def post(year, month, article_name):
    cache_key = '_'.join(map(str, ['post', year, month, article_name]))
    post = get_post_cache(cache_key)

    page = request.args.get('page', 1, type=int)
    if page == -1:
        counts = post.get('comment_count', 0)
        page = (counts - 1) / current_app.config['COMMENTS_PER_PAGE'] + 1

    pagination = Comment.query.filter_by(post_id=post['id'],isReply=False,disabled=True).order_by(
        Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['COMMENTS_PER_PAGE'],
        error_out=False
    )
    comments = pagination.items
    replys = Comment.query.filter_by(post_id=post['id'], isReply=True, disabled=True).all()
    return render_template('main/post.html', post=post, title=post['title'],
                   pagination=pagination, comments=comments, replys=replys,
                   counts=len(comments)+len(replys))

@main.route('/view/<type>/<int:id>', methods=['GET'])
def views(type, id):
    """浏览量"""
    view = View.query.filter_by(type=type, relationship_id=id).first()
    if not view:
        view = View(type=type, count=1, relationship_id=id)
        db.session.add(view)
        db.session.commit()
        resp = jsonify(count=1)
        resp.set_cookie('post_' + str(id), '1', max_age=1 * 24 * 60 * 60)
        return resp

    if type == 'post':
        if not request.cookies.get('post_' + str(id)):
            view.count += 1
            db.session.add(view)
            db.session.commit()
            resp = jsonify(count=view.count)
            resp.set_cookie('post_' + str(id), '1', max_age=1 * 24 * 60 * 60)
            return resp
        return jsonify(count=view.count)
    elif type == 'column':
        pass

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
                           comments=comments, replys=replys, counts=len(comments)+len(replys))

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
    count = Post.query.count()
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['ACHIVES_POSTS_PER_PAGE'],
        error_out=False
    )
    posts = [post for post in pagination.items if post.draft is False]
    # times = [post.timestamp for post in posts ]
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
    results = (post for post in pagination.items if post.draft is False)
    return render_template('main/results.html', results=results,
                           query=query, pagination=pagination,
                           title=query + '的搜索结果')

# 侧栏 love me 插件
@main.route('/loveme', methods=['GET'])
def love_me():
    """
    由于请求一次就要更新一次页面，所以需要清除页面所有缓存，
    这样做很蠢，有待改进
    :return: json
    """
    # 清除所有页面缓存
    cache.clear()
    love_me_counts = LoveMe.query.all()[0]
    love_me_counts.loveMe += 1
    db.session.add(love_me_counts)
    db.session.commit()
    return jsonify(counts=love_me_counts.loveMe)


# 保存评论的函数
def save_comment(post, form):
    # 邮件配置
    # from_addr = current_app.config['MAIL_USERNAME']
    # password = current_app.config['MAIL_PASSWORD']
    # to_addr = current_app.config['ADMIN_MAIL']
    # smtp_server = current_app.config['MAIL_SERVER']
    # mail_port = current_app.config['MAIL_PORT']

    nickname = form['nickname']
    email = form['email']
    website = form['website'] or None
    com = form['comment']
    comment = ''
    try:
        replyTo = form['replyTo']
        comment = Comment(comment=com, author=nickname,
                          email=email, website=website,
                          isReply=True, replyTo=replyTo)

        # msg = nickname + '在文章：' + post.title + '\n' + '中发布一条评论：' + com + '\n' + '请前往查看。'
        # asyncio_send(from_addr, password, to_addr, smtp_server, mail_port, msg)
        data = {'nickname': nickname, 'email': email, 'website': website,
                'comment': com, 'isReply': True, 'replyTo': replyTo}
    except:
        comment = Comment(comment=com, author=nickname,
                          email=email, website=website)

        # msg = nickname + '在文章：' + post.title + '\n' + '中发布一条评论：' + com + '\n' + '请前往查看。'
        # asyncio_send(from_addr, password, to_addr, smtp_server, mail_port, msg)
        data = {'nickname': nickname, 'email': email, 'website': website, 'comment': com}
    finally:
        if isinstance(post, Post):
            comment.post = post
        elif isinstance(post, Page):
            comment.page = post
        elif isinstance(post, Article):
            comment.article = post
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
    if data.get('replyTo'):
        return jsonify(nickname=data['nickname'], email=data['email'],
                       website=data['website'], body=data['comment'],
                       isReply=data['isReply'], replyTo=data['replyTo'], post=post.title)
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
    great_links = [link for link in friends if link.isGreatLink is True]
    bad_links = [link for link in friends if link.isGreatLink is False]

    return render_template('main/friends.html', title="朋友",
                           great_links=great_links, bad_links=bad_links)




