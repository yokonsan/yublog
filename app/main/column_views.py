from flask import render_template, request, jsonify, current_app

from . import column
from app import db
from ..models import Column, Article, Comment
from .views import save_comment


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
    column.view_num += 1
    db.session.add(column)
    articles = Article.query.order_by(Article.timestamp.asc()).all()

    data = enum_list(list(articles))

    return render_template('column/column.html', column=column,
                           title=column.column, data=data, first_id=articles[0].id)


@column.route('/<url>/<int:id>')
def article(url, id):
    column = Column.query.filter_by(url_name=url).first()

    articles = Article.query.filter_by(column=column).order_by(Article.timestamp.asc()).all()
    article = Article.query.get_or_404(id)
    article.view_num += 1
    db.session.add(article)

    prev_article = next_article = None
    if articles[0] != article:
        prev_article = articles[int(articles.index(article)) - 1]
    if articles[-1] != article:
        next_article = articles[int(articles.index(article)) + 1]

    data = enum_list(list(articles))

    page = request.args.get('page', 1, type=int)
    if page == -1:
        counts = article.comments.count()
        page = (counts - 1) / \
               current_app.config['COMMENTS_PER_PAGE'] + 1
    pagination = Comment.query.filter_by(article=article, isReply=False, disabled=True).order_by(
        Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['COMMENTS_PER_PAGE'],
        error_out=False
    )
    comments = pagination.items
    replys = article.comments.filter_by(isReply=True, disabled=True).all()

    return render_template('column/article.html', column=column, data=data, title=article.title,
                           article=article, prev_article=prev_article, next_article=next_article,
                           pagination=pagination, comments=comments, replys=replys,
                           counts=len(comments)+len(replys))

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


