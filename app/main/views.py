from flask import render_template, redirect, url_for, request, g, current_app, abort, jsonify

from . import main
from .forms import SearchForm
from ..models import *
from ..utils import send_mail
from .. import cache


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
#@cache.cached(timeout=60*60*12, key_prefix=cache_key)
def index():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False
    )
    posts = [post for post in pagination.items if post.draft is False]

    return render_template('main/index.html',
                           title='首页',
                           posts=posts,
                           pagination=pagination)

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
#@cache.cached(timeout=60*5, key_prefix='post/%s', unless=None)
def post(year, month, article_name):
    time = str(year) + '-' + str(month)
    posts = Post.query.filter_by(url_name=article_name).all()
    post = ''
    if len(posts) == 1:
        post = posts[0]
    elif len(posts) > 1:
        post = [i for i in posts if time in i.timestamp][0]
    elif len(posts) < 1:
        abort(404)

    post.view_num += 1
    db.session.add(post)
    tags = [tag for tag in post.tags.split(',')]
    next_post = nextPost(post)
    prev_post = prevPost(post)

    page = request.args.get('page', 1, type=int)
    if page == -1:
        counts = post.comments.count()
        page = (counts - 1) / \
               current_app.config['COMMENTS_PER_PAGE'] + 1
    pagination = Comment.query.filter_by(post=post,isReply=False,disabled=True).order_by(
        Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['COMMENTS_PER_PAGE'],
        error_out=False
    )
    comments = pagination.items
    replys = post.comments.filter_by(isReply=True, disabled=True).all()
    return render_template('main/post.html', post=post, tags=tags, title=post.title,
                           next_post=next_post, prev_post=prev_post, pagination=pagination,
                           comments=comments, replys=replys, counts=len(comments)+len(replys))


@main.route('/page/<page_url>/')
#@cache.cached(timeout=60*60*24, key_prefix='page/%s', unless=None)
def page(page_url):
    page = Page.query.filter_by(url_name=page_url).first()
    p = request.args.get('page', 1, type=int)
    if p == -1:
        counts = page.comments.count()
        p = (counts - 1) / \
               current_app.config['COMMENTS_PER_PAGE'] + 1
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
#@cache.cached(timeout=60*60*24*30, key_prefix='tag/%s', unless=None)
def tag(tag_name):
    tag = tag_name
    all_posts = Post.query.order_by(Post.timestamp.desc()).all()
    posts = [post for post in all_posts if post.tag_in_post(tag) and post.draft==False]

    return render_template('main/tag.html', tag=tag, posts=posts)

@main.route('/category/<category_name>/')
#@cache.cached(timeout=60*60*24*30, key_prefix='category/%s', unless=None)
def category(category_name):
    category = Category.query.filter_by(category=category_name).first()

    posts = Post.query.filter_by(category=category, draft=False).order_by(Post.timestamp.desc()).all()
    return render_template('main/category.html',
                           category=category,
                           posts=posts,
                           title='分类：' + category.category)

@main.route('/archives/')
#@cache.cached(timeout=60*60*24*30, key_prefix=cache_key)
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

    return render_template('main/archives.html',
                           title='归档',
                           posts=posts,
                           year=year,
                           data=data,
                           count=count,
                           pagination=pagination)

@main.route('/search/', methods=['POST'])
def search():
    print(g.search_form)
    print(1)
    if g.search_form.validate_on_submit():
        print(2)
        query = g.search_form.search.data
        return redirect(url_for('main.search_result', keywords=query))

    elif g.search_form2.validate_on_submit():
        print(3)
        query = g.search_form2.search.data
        return redirect(url_for('main.search_result', keywords=query))
    return redirect(url_for('main.search_result', keywords='1'))

# /search-result?keywords=query
@main.route('/search-result')
def search_result():
    query = request.args.get('keywords')
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.whooshee_search(query).order_by(Post.id.desc()).paginate(
        page, per_page=current_app.config['SEARCH_POSTS_PER_PAGE'],
        error_out=False
    )
    results = [post for post in pagination.items if post.draft is False]
    return render_template('main/results.html',
                           results=results,
                           query=query,
                           pagination=pagination,
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
    try:
        replyTo = form['replyTo']
        comment = Comment(comment=com, author=nickname,
                          email=email, website=website,
                          isReply=True, replyTo=replyTo)

        # msg = nickname + '在文章：' + post.title + '\n' + '中发布一条评论：' + com + '\n' + '请前往查看。'
        # send_mail(from_addr, password, to_addr, smtp_server, mail_port, msg)
        data = {'nickname': nickname, 'email': email, 'website': website,
                'comment': com, 'isReply': True, 'replyTo': replyTo}
    except:
        comment = Comment(comment=com, author=nickname,
                          email=email, website=website)

        # msg = nickname + '在文章：' + post.title + '\n' + '中发布一条评论：' + com + '\n' + '请前往查看。'
        # send_mail(from_addr, password, to_addr, smtp_server, mail_port, msg)
        data = {'nickname': nickname, 'email': email, 'website': website, 'comment': com}
    finally:
        try:
            comment.post = post
        except:
            comment.page = post
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
#@cache.cached(timeout=60*60*24*30, key_prefix='shuoshuo', unless=None)
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
#@cache.cached(timeout=60*60*24*30, key_prefix='friends', unless=None)
def friends():
    friends = SiteLink.query.filter_by(isFriendLink=True).order_by(SiteLink.id.desc()).all()
    great_links = [link for link in friends if link.isGreatLink is True]
    bad_links = [link for link in friends if link.isGreatLink is False]

    return render_template('main/friends.html', title="朋友",
                           great_links=great_links, bad_links=bad_links)


