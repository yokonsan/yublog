from flask import render_template

from . import column
from app import db
from ..models import Column, Article


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

    return render_template('column/article.html', column=column, data=data, title=article.title,
                           article=article, prev_article=prev_article, next_article=next_article)

@column.route('/love/<int:id>')
def love_column(id):
    pass



