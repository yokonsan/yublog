from flask import (
    render_template,
    request,
    jsonify,
    current_app,
    redirect,
    url_for,
    make_response,
    abort
)

from yublog import CacheType, cache_operate, CacheKey
from yublog.forms import ArticlePasswordForm
from yublog.models import Column
from yublog.views import column_bp
from yublog.utils.comment import commit_comment
from yublog.utils.cache.model import get_model_cache, comment_pagination_kwargs, column_cache, articles_cache


@column_bp.route("/")
def index():
    columns = cache_operate.getset(
        CacheType.COLUMN,
        CacheKey.COLUMNS,
        callback=lambda: Column.query
                               .order_by(Column.id.desc())
                               .all()
    )

    return render_template(
        "column/index.html",
        title="专栏目录",
        columns=columns
    )


@column_bp.route("/<url_name>")
def _column(url_name):
    column = column_cache(url_name)

    articles = articles_cache(column.id)
    
    first_id = articles[0].id if articles else None
    return render_template(
        "column/column.html",
        column=column,
        title=column.title,
        articles=enumerate(articles, 1),
        first_id=first_id
    )


@column_bp.route("/<url_name>/article/<int:id>")
def article(url_name, id):
    column = column_cache(url_name)
    articles = articles_cache(column.id)
    _article = get_model_cache(CacheType.ARTICLE, id) or abort(404)

    # judge whether secrecy
    if _article.secrecy \
            and request.cookies.get("secrecy") != column.password_hash:
        return redirect(url_for(
            "column.enter_password", url_name=url_name, id=id
        ))

    per = current_app.config["COMMENTS_PER_PAGE"]
    cur_page = max(request.args.get("page", 1, type=int), 1)
    comment_args = comment_pagination_kwargs(_article, cur_page, per)
    
    return render_template(
        "column/article.html",
        title=_article.title,
        column=column,
        article=_article,
        articles=enumerate(articles, 1),
        **comment_args
    )


@column_bp.route(
    "/<url_name>/article/<int:id>/password",
    methods=["GET", "POST"]
)
def enter_password(url_name, id):
    form = ArticlePasswordForm()
    if form.validate_on_submit():
        column = column_cache(url_name)
        if column.verify_password(form.password.data):
            resp = make_response(redirect(url_for(
                "column.article", url_name=url_name, id=id
            )))
            resp.set_cookie(
                "secrecy", column.password_hash, max_age=7 * 24 * 60 * 60
            )
            return resp

        return redirect(url_for(
            "column.enter_password", url_name=url_name, id=id
        ))
    return render_template(
        "column/enter_password.html",
        title="输入密码",
        id=id,
        form=form,
        url_name=url_name,
    )


@column_bp.route("/column/<int:id>/comment", methods=["POST"])
def comment(id):
    form = request.get_json()

    commit_comment("article", form, id)
    return jsonify(**form)
