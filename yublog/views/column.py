from os import abort
from flask import render_template, request, jsonify, \
    current_app, redirect, url_for, make_response

from yublog import CacheType, cache_operate, CacheKey
from yublog.forms import ArticlePasswordForm
from yublog.models import Column, Comment
from yublog.views import column_bp
from yublog.utils.cache.model import get_model_cache


@column_bp.route("/")
def index():
    columns = cache_operate.getset(
        CacheType.COLUMN,
        CacheKey.COLUMNS,
        lambda: Column.query.order_by(Column.id.desc()).all()
    )

    return render_template(
        "column/index.html",
        title="专栏目录",
        columns=columns
    )


@column_bp.route("/<url_name>")
def _column(url_name):
    column = cache_operate.getset(CacheType.COLUMN, url_name)
    articles = [{"num": i, "item": a} for i, a in enumerate(column["articles"])]
    
    first_id = articles[0]["item"]["id"] if articles else None
    return render_template("column/column.html", column=column,
                           title=column["title"], articles=articles, first_id=first_id)


@column_bp.route("/<url>/<int:id>")
def article(url, id):
    column = get_model_cache(CacheType.COLUMN, url)
    # get this column all articles cache at sidebar
    _article, articles = None, []
    for i, a in enumerate(column["articles"]):
        articles.append({"num": i, "item": a})
        if a["id"] == id:
            _article = a
    if _article is None:
        abort(404)
    # judge whether secrecy
    if _article.get("secrecy"):
        secrecy = request.cookies.get("secrecy")
        if not secrecy or secrecy != column.get("password_hash"):
            return redirect(url_for("column.enter_password", url=url, id=id))

    page = request.args.get("page", 1, type=int)
    if page == -1:
        counts = _article.comments.count()
        page = (counts - 1) / current_app.config["COMMENTS_PER_PAGE"] + 1

    pagination = Comment.query.filter_by(article_id=_article["id"], disabled=True, replied_id=None) \
        .order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config["COMMENTS_PER_PAGE"],
        error_out=False
    )
    comments = pagination.items
    
    return render_template("column/article.html", column=column, articles=articles,
                           title=_article["title"], article=_article,
                           pagination=pagination, comments=comments,
                           counts=len(comments))


@column_bp.route("/article/<url>/<int:id>/password", methods=["GET", "POST"])
def enter_password(url, id):
    form = ArticlePasswordForm()
    if form.validate_on_submit():
        column = Column.query.filter_by(url_name=url).first()
        password = form.password.data
        if column.verify_password(password):
            resp = make_response(redirect(url_for("column.article", url=url, id=id)))
            resp.set_cookie("secrecy", column.password_hash, max_age=7 * 24 * 60 * 60)
            return resp
        return redirect(url_for("column.enter_password", url=url, id=id))
    return render_template("column/enter_password.html", form=form,
                           url=url, id=id, title="输如密码")


@column_bp.route("/column/<int:id>/comment", methods=["POST"])
def comment(id):
    form = request.get_json()

    from yublog.utils.comment import commit_comment
    commit_comment("article", form, id)

    return jsonify(**form)
