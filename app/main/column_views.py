from flask import render_template, request, jsonify, \
    current_app, redirect, url_for, make_response

from . import column
from app import db, cache
from ..models import Column, Article, Comment
from .views import save_comment
from  .forms import ArticlePasswordForm


def get_all_articles_cache(column_id, key):
    """
    专栏所有文章
    :param key: column_ + column_url
    """
    data = cache.get(key)
    if data:
        return data

    _, column_url = key.split('_')
    articles = Article.query.filter_by(column_id=int(column_id)).order_by(Article.timestamp.asc()).all()
    items = []
    for i in articles:
        items.append({
            'id': i.id,
            'title': i.title,
            'secrecy': i.secrecy
        })
    cache.set(key, items, timeout=60 * 60 * 24 * 30)
    return items

def get_article_cache(column_id, key):
    """获取博客文章缓存"""
    data = cache.get(key)
    if data:
        return data
    else:
        _, url, id = key.split('_')
        return set_article_cache(column_id, url, int(id))

def set_article_cache(column_id, column_url, id):
    """设置专栏文章缓存"""
    articles = get_all_articles_cache(column_id, 'column_'+column_url)

    article = Article.query.get_or_404(id)
    # I don't even know what I did.
    _data = {'id': article.id, 'title': article.title, 'secrecy': article.secrecy}
    prev_article = next_article = None
    if articles[0] != _data:
        prev_article = articles[int(articles.index(_data)) - 1]
    if articles[-1] != _data:
        next_article = articles[int(articles.index(_data)) + 1]
    data = article.to_dict()
    data['next_article'] = {
        'id': next_article['id'],
        'title': next_article['title']
    } if next_article else None
    data['prev_article'] = {
        'id': prev_article['id'],
        'title': prev_article['title']
    } if prev_article else None
    cache_key = '_'.join(['article', column_url, str(id)])
    cache.set(cache_key, data, timeout=60 * 60 * 24 * 30)
    return data


def enum_list(list):
    data = []
    d = {}
    for index, item in enumerate(list):
        d = {
            'num': index,
            'item': item
        }
        data.append(d)
    return data

@column.route('/')
def index():
    columns = Column.query.order_by(Column.id.desc()).all()

    return render_template('column/index.html', title='专栏目录', columns=columns)

@column.route('/<int:id>')
def _column(id):
    column = Column.query.get_or_404(id)

    if not request.cookies.get('column_' + str(id)):
        column.view_num += 1
        db.session.add(column)

    articles = get_all_articles_cache(column.id, 'column_' + column.url_name)

    data = enum_list(articles)
    first_id = None
    if articles:
        first_id = articles[0].get('id')

    resp =  make_response(render_template('column/column.html', column=column,
                           title=column.column, data=data, first_id=first_id))
    resp.set_cookie('column_' + str(id), '1', max_age=1*24*60*60)
    return resp


@column.route('/<url>/<int:id>')
def article(url, id):
    column = Column.query.filter_by(url_name=url).first()
    # get this article cache
    article = get_article_cache(column.id, '_'.join(['article', url, str(id)]))
    # judge whether secrecy
    if article.get('secrecy'):
        secrecy = request.cookies.get('secrecy')
        if not secrecy or secrecy != column.password_hash:
            return redirect(url_for('column.enter_password', url=url, id=id))
    # get this column all articles cache at sidebar
    articles = get_all_articles_cache(column.id, 'column_' + url)
    data = enum_list(articles)

    page = request.args.get('page', 1, type=int)
    if page == -1:
        counts = article.comments.count()
        page = (counts - 1) / current_app.config['COMMENTS_PER_PAGE'] + 1

    pagination = Comment.query.filter_by(article_id=article['id'],
                                         isReply=False, disabled=True).order_by(
        Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['COMMENTS_PER_PAGE'],
        error_out=False
    )
    comments = pagination.items
    replys = Comment.query.filter_by(article_id=article['id'],
                                     isReply=True, disabled=True).all()

    return render_template('column/article.html', column=column, data=data,
                           title=article['title'], article=article,
                           pagination=pagination, comments=comments, replys=replys,
                           counts=len(comments)+len(replys))

@column.route('/article/<url>/<int:id>/password', methods=['GET', 'POST'])
def enter_password(url, id):
    form = ArticlePasswordForm()
    if form.validate_on_submit():
        column = Column.query.filter_by(url_name=url).first()
        print(column)
        password = form.password.data
        if column.verify_password(password):
            resp = make_response(redirect(url_for('column.article', url=url, id=id)))
            resp.set_cookie('secrecy', column.password_hash, max_age=7*24*60*60)
            return resp
        return redirect(url_for('column.enter_password', url=url, id=id))
    return render_template('column/enter_password.html', form=form,
                           url=url, id=id, title='输如密码')

@column.route('/love/<int:id>')
def love_column(id):
    column = Column.query.get_or_404(id)
    column.love_num += 1
    db.session.add(column)
    db.session.commit()
    return jsonify(counts=column.love_num)

@column.route('/<int:id>/comment', methods=['POST'])
def comment(id):
    post = Article.query.filter_by(id=id).first()
    form = request.get_json()
    data = save_comment(post, form)
    if data.get('replyTo'):
        return jsonify(nickname=data['nickname'], email=data['email'],
                       website=data['website'], body=data['comment'],
                       isReply=data['isReply'], replyTo=data['replyTo'], post=post.title)
    return jsonify(nickname=data['nickname'], email=data['email'],
                       website=data['website'], body=data['comment'], post=post.title)


