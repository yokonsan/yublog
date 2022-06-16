import os
import re

from flask import (
    redirect,
    request,
    flash,
    render_template,
    current_app,
    url_for
)
from flask_login import (
    login_required,
    login_user,
    logout_user,
    current_user
)

from yublog.utils.cache import cache_operate, CacheKey, CacheType
from yublog.exceptions import DuplicateEntryException
from yublog.extensions import qn, whooshee
from yublog.forms import *
from yublog.models import (
    Admin,
    Post,
    Page,
    Link,
    SideBox,
    Column,
    Comment,
    Talk,
    Article,
)
from yublog.utils.cache.model import clean_post_relative_cache
from yublog.utils.comment import get_comment_url, update_comment_cache
from yublog.utils import commit
from yublog.utils.emails import send_mail
from yublog.views import admin_bp
from yublog.utils.save import save_post, save_category, save_xml, save_tags


@admin_bp.route("/")
@admin_bp.route("/index")
@login_required
def index():
    return render_template("admin/index.html")


@admin_bp.route("/login/", methods=["GET", "POST"])
def login():
    form = AdminLogin()
    if form.validate_on_submit():
        user = Admin.query.filter_by(login_name=form.username.data).first()
        if user and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(url_for("admin.index"))

        flash("Invalid account or password.")
    return render_template("admin/login.html", title="登录", form=form)


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Successfully logged out.")
    return redirect(url_for("admin.index"))


@admin_bp.route("/setting", methods=["GET", "POST"])
@login_required
def set_site():
    form = AdminSiteForm()
    user = Admin.query.all()[0]
    if form.validate_on_submit():
        form.to_model(user)
        commit.add(user)
        flash("Set successfully.")

        cache_operate.clean(CacheType.GLOBAL, CacheKey.ADMIN)
        return redirect(url_for("admin.index"))

    form.to_form(user)
    return render_template(
        "admin/profile.html", title="设置网站信息", form=form
    )


@admin_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.verify_password(form.old_password.data):
            flash("Please enter the correct password.")
            return redirect(url_for("admin.change_password"))

        if form.password.data != form.password2.data:
            flash("Please confirm whether the passwords are consistent.")
            return redirect(url_for("admin.change_password"))

        current_user.password = form.password.data
        commit.add(current_user)
        flash("Password changed successfully.")
        return redirect(url_for("admin.index"))
    return render_template(
        "admin/change_password.html", title="更改密码", form=form
    )


@admin_bp.route("/link/add", methods=["GET", "POST"])
@login_required
def add_link():
    def judge_exist(address):
        exist_link = Link.query.filter_by(link=address).first()
        if exist_link:
            flash(f"Link[{address!r}] already exists...")
            return redirect(url_for("admin.add_link"))
        return

    def _commit(item):
        commit.add(item)
        flash("Added successfully.")
        return redirect(url_for("admin.add_link"))

    social_form, friend_form = SocialLinkForm(), FriendLinkForm()
    # social link
    if social_form.submit.data and social_form.validate_on_submit():
        judge_exist(social_form.link.data)

        link = social_form.new_model(Link, is_friend=False)
        cache_operate.clean(CacheType.GLOBAL, CacheKey.SOCIAL_LINKS)
        _commit(link)

    # friend link
    if friend_form.submit2.data and friend_form.validate_on_submit():
        judge_exist(friend_form.link.data)

        link = friend_form.new_model(Link, is_friend=True)
        cache_operate.incr(CacheType.GLOBAL, CacheKey.FRIEND_COUNT)
        cache_operate.clean(CacheType.LINK, CacheKey.FRIEND_LINKS)
        _commit(link)

    return render_template(
        "admin/edit_link.html",
        title="站点链接",
        form=social_form,
        fr_form=friend_form
    )


@admin_bp.route("/links")
@login_required
def links():
    social_links, friend_links = [], []
    for link in Link.query.filter_by().order_by(Link.id.desc()).all():
        (friend_links if link.is_friend else social_links).append(link)

    return render_template(
        "admin/link.html",
        title="管理链接",
        social_links=social_links,
        friend_links=friend_links
    )


@admin_bp.route("/link/delete/<int:id>")
@login_required
def delete_link(id):
    link = Link.query.get_or_404(id)
    commit.delete(link)
    # update cache
    if link.is_friend:
        cache_operate.decr(CacheType.GLOBAL, CacheKey.FRIEND_COUNT)
        cache_operate.clean(CacheType.LINK, CacheKey.FRIEND_LINKS)
    else:
        cache_operate.clean(CacheType.GLOBAL, CacheKey.SOCIAL_LINKS)

    return redirect(url_for("admin.links"))


@admin_bp.route("/link/great/<int:id>")
@login_required
def great_link(id):
    link = Link.query.get_or_404(id)
    link.is_great = not link.is_great
    commit.add(link)

    cache_operate.clean(CacheType.LINK, CacheKey.FRIEND_LINKS)
    return redirect(url_for("admin.links"))


@admin_bp.route("/post/write", methods=["GET", "POST"])
@login_required
def write_post():
    form = AdminWrite()
    if form.validate_on_submit():
        if Post.query.filter_by(url_name=form.url_name.data).first():
            flash("Duplicate articles.")
            raise DuplicateEntryException("Duplicate articles.")

        if "submit" in request.form:
            post = save_post(form)
            commit.add(post)
            flash("Posted successfully.")

            clean_post_relative_cache()
        else:
            post = save_post(form, True)
            commit.add(post)
            flash("Saved successfully.")

        return redirect(url_for("admin.write_post"))
    return render_template("admin/edit_post.html", form=form, title="写文章")


@admin_bp.route("/post/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)
    form = AdminWrite()
    if form.validate_on_submit():
        category = post.category
        if form.category.data != post.category.category:
            category = save_category(post.category.category, form.category.data)
        if not category.is_show:
            category.is_show = True

        form.to_model(post, category=category)

        if post.draft:
            if "submit" in request.form:
                post.draft = False
                msg = "Posted successfully."

                clean_post_relative_cache()
                save_xml(post.create_time)
                save_tags(post.tags.split(","))
            else:
                msg = "Saved successfully."
        else:
            msg = "Update successfully."
            cache_operate.clean(
                CacheType.POST, f"{post.year}_{post.month}_{post.url_name}"
            )
            save_xml(post.create_time)

        flash(msg)
        commit.add(post)
        return redirect(url_for("admin.edit_post", id=id))

    form.to_form(post, category=post.category_name)
    return render_template(
        "admin/edit_post.html", form=form, post=post, title="编辑文章"
    )


@admin_bp.route("/page/write", methods=["GET", "POST"])
@login_required
def add_page():
    form = AddPageForm()
    if form.validate_on_submit():
        page = form.new_model(Page)

        commit.add(page)
        flash("Posted successfully.")

        if page.show_nav:
            cache_operate.clean(CacheType.GLOBAL, CacheKey.PAGES)
        return redirect(url_for("admin.add_page"))
    return render_template(
        "admin/edit_page.html", form=form, title="添加页面"
    )


@admin_bp.route("/page/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_page(id):
    page = Page.query.get_or_404(id)
    form = AddPageForm()
    prev = page.show_nav

    if form.validate_on_submit():
        form.to_model(page)
        commit.add(page)
        flash("Update successfully.")

        cache_operate.clean(CacheType.PAGE, page.url_name)
        if prev != page.show_nav:
            cache_operate.clean(CacheType.GLOBAL, CacheKey.PAGES)
        return redirect(url_for("admin.edit_page", id=page.id))

    form.to_form(page)
    return render_template(
        "admin/edit_page.html", title="编辑页面", form=form, page=page
    )


@admin_bp.route("/page/delete/<int:id>")
@login_required
def delete_page(id):
    page = Page.query.get_or_404(id)
    commit.delete(page)
    flash("Deleted successfully.")

    cache_operate.clean(CacheType.PAGE, page.url_name)
    if page.show_nav:
        cache_operate.clean(CacheType.GLOBAL, CacheKey.PAGES)

    return redirect(url_for("admin.pages"))


@admin_bp.route("/post/draft")
@login_required
def post_draft():
    return render_template(
        "admin/draft.html",
        drafts=Post.query
                   .filter_by(draft=True)
                   .order_by(Post.id.desc())
                   .all(),
        title="管理草稿"
    )


@admin_bp.route("/pages")
@login_required
def pages():
    return render_template(
        "admin/page.html",
        pages=Page.query.order_by(Page.id.desc()).all(),
        title="管理页面"
    )


@admin_bp.route("/posts")
@login_required
def posts():
    page = request.args.get("page", 1, type=int)
    pagination = Post.query \
                     .filter_by(draft=False) \
                     .order_by(Post.id.desc()) \
                     .paginate(
                        page,
                        per_page=current_app.config["ADMIN_POSTS_PER_PAGE"],
                        error_out=False
                     )

    return render_template(
        "admin/post.html",
        title="管理文章",
        posts=pagination.items,
        pagination=pagination
    )


@admin_bp.route("/post/delete/<int:id>")
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    _category = post.category
    if _category.posts.count() == 1:
        commit.delete(_category)

    commit.delete(post)
    flash("Deleted successfully.")

    # update cache
    if post.draft is False:
        cache_operate.decr(CacheType.GLOBAL, CacheKey.POST_COUNT)

    return redirect(url_for("admin.posts"))


@admin_bp.route("/comments")
@login_required
def comments():
    page = request.args.get("page", 1, type=int)
    pagination = Comment.query \
                        .order_by(Comment.timestamp.desc()) \
                        .paginate(
                            page,
                            per_page=current_app.config["ADMIN_COMMENTS_PER_PAGE"],
                            error_out=False
                        )

    return render_template(
        "admin/comment.html",
        title="管理评论",
        comments=pagination.items,
        pagination=pagination
    )


@admin_bp.route("/comment/delete/<int:id>")
@login_required
def delete_comment(id):
    comment = Comment.query.get_or_404(id)

    if comment.disabled:
        update_comment_cache(comment, is_incr=False)

    commit.delete(comment)
    flash("Deleted successfully.")
    return redirect(url_for("admin.comments"))


@admin_bp.route("/allow/comment/<int:id>")
@login_required
def allow_comment(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    commit.add(comment)
    flash("Allow comment.")

    # send mail
    if comment.replied_id:
        reply_to_comment = Comment.query.get_or_404(comment.replied_id)
        reply_email = reply_to_comment.email
        if reply_email != current_app.config["ADMIN_MAIL"]:
            msg = render_template(
                "user_mail.html",
                nickname=reply_to_comment.author,
                comment=comment.comment,
                url=get_comment_url(comment)
            )
            send_mail(reply_email, msg)

    update_comment_cache(comment)

    return redirect(url_for("admin.comments"))


@admin_bp.route("/unable/comment/<int:id>")
@login_required
def unable_comment(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    commit.add(comment)
    flash("Hide successfully.")

    update_comment_cache(comment, is_incr=False)

    return redirect(url_for("admin.comments"))


@admin_bp.route("/talk/write", methods=["GET", "POST"])
@login_required
def write_talk():
    form = TalkForm()
    if form.validate_on_submit():
        _talk = Talk(talk=form.talk.data)
        commit.add(_talk)
        flash("Posted successfully.")

        cache_operate.set(
            CacheType.GLOBAL, CacheKey.LAST_TALK, _talk.body_to_html
        )
        cache_operate.clean(CacheType.TALK)
        return redirect(url_for("admin.write_talk"))
    return render_template(
        "admin/edit_talk.html", title="写说说", form=form
    )


@admin_bp.route("/talk")
@login_required
def talk():
    return render_template(
        "admin/talk.html",
        title="管理说说",
        talks=Talk.query.order_by(Talk.timestamp.desc()).all()
    )


@admin_bp.route("/talk/delete/<int:id>")
@login_required
def delete_talk(id):
    if Talk.query.count() == 1:
        flash("There must be one talk.")
        return redirect(url_for("admin.talk"))

    commit.delete(Talk.query.get_or_404(id))
    flash("Deleted successfully.")

    # update cache
    cache_operate.clean(CacheType.GLOBAL, CacheKey.LAST_TALK)
    return redirect(url_for("admin.talk"))


# 管理主题
@admin_bp.route("/column/write", methods=["GET", "POST"])
@login_required
def write_column():
    form = ColumnForm()
    if form.validate_on_submit():
        _column = form.new_model(Column)
        if form.password.data:
            _column.password = form.password.data
        commit.add(_column)
        flash("Posted successfully.")
        return redirect(url_for("admin.column", id=_column.id))

    return render_template(
        "admin_column/edit_column.html", form=form, title="编辑专题"
    )


@admin_bp.route("/column/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_column(id):
    _column = Column.query.get_or_404(id)
    form = ColumnForm()
    if form.validate_on_submit():
        form.to_model(_column)
        if password := form.password.data:
            _column.password = password

        commit.add(_column)
        flash("Update successfully.")
        cache_operate.clean(CacheType.COLUMN, _column.url_name)
        return redirect(url_for("admin.column", id=id))

    form.to_form(_column)
    return render_template(
        "admin_column/edit_column.html",
        title="更新专题",
        form=form,
        column=_column
    )


@admin_bp.route("/columns")
@login_required
def columns():
    return render_template(
        "admin_column/columns.html",
        columns=Column.query.all(),
        title="管理专题"
    )


@admin_bp.route("/column/<int:id>")
@login_required
def column(id):
    _column = Column.query.get_or_404(id)
    return render_template(
        "admin_column/column.html",
        column=_column,
        articles=_column.articles
                        .order_by(Article.id.desc())
                        .all(),
        title=_column.title
    )


@admin_bp.route("/column/delete/<int:id>")
@login_required
def delete_column(id):
    _column = Column.query.get_or_404(id)

    commit.delete(_column)
    flash("Deleted successfully.")

    cache_operate.clean(CacheType.COLUMN, _column.url_name)
    return redirect(url_for("admin.columns"))


@admin_bp.route("/column/<int:id>/write/article", methods=["GET", "POST"])
@login_required
def write_column_article(id):
    _column = Column.query.get_or_404(id)
    form = ColumnArticleForm()
    if form.validate_on_submit():
        article = form.new_model(Article, column=_column)
        commit.add(article)
        flash("Added successfully.")

        cache_operate.clean(CacheType.COLUMN, _column.url_name)
        return redirect(url_for("admin.column", id=id))

    return render_template(
        "admin_column/edit_article.html",
        title="编辑文章",
        form=form,
        column=_column
    )


@admin_bp.route(
    "/column/<int:cid>/edit/article/<int:aid>",
    methods=["GET", "POST"]
)
@login_required
def edit_column_article(cid, aid):
    _column = Column.query.get_or_404(cid)
    article = Article.query.get_or_404(aid)

    form = ColumnArticleForm()
    if form.validate_on_submit():
        form.to_model(article)
        commit.add(article)
        flash("Update successfully.")

        cache_operate.clean(CacheType.COLUMN, _column.url_name)
        return redirect(url_for("admin.column", id=cid))

    form.to_form(article)
    return render_template(
        "admin_column/edit_article.html",
        title="更新文章",
        form=form,
        column=_column,
        article=article
    )


@admin_bp.route("/column/<int:cid>/delete/article/<int:aid>")
@login_required
def delete_column_article(cid, aid):
    _column = Column.query.get_or_404(cid)
    article = Article.query.get_or_404(aid)
    commit.delete(article)
    flash("Deleted successfully.")

    cache_operate.clean(CacheType.COLUMN, _column.url_name)
    return redirect(url_for("admin.column", id=cid))


@admin_bp.route("/upload/file", methods=["GET", "POST"])
@login_required
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        file.save(os.path.join(
            current_app.config["UPLOAD_PATH"],
            file.filename
        ))

        flash("Upload successfully.")
        return redirect(url_for("admin.index"))
    return render_template("admin/upload_file.html", title="上传文件")


@admin_bp.route("/box/add", methods=["GET", "POST"])
@login_required
def add_side_box():
    form = SideBoxForm()
    if form.validate_on_submit():
        box = form.new_model(SideBox)
        commit.add(box)
        flash("Added successfully.")

        cache_operate.clean(
            CacheType.GLOBAL,
            (CacheKey.ADS_BOXES if box.is_advertising else CacheKey.SITE_BOXES)
        )
        return redirect(url_for("admin.side_box"))
    return render_template(
        "admin/edit_sidebox.html", title="添加插件", form=form
    )


@admin_bp.route("/box/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_side_box(id):
    box = SideBox.query.get_or_404(id)
    form = SideBoxForm()
    if form.validate_on_submit():
        form.to_form(box)
        commit.add(box)
        flash("Update successfully.")

        cache_operate.clean(
            CacheType.GLOBAL,
            (CacheKey.ADS_BOXES if box.is_advertising else CacheKey.SITE_BOXES)
        )
        return redirect(url_for("admin.side_box"))

    form.to_form(box)
    return render_template(
        "admin/edit_sidebox.html", title="更新插件", form=form, box=box
    )


@admin_bp.route("/boxes")
@login_required
def side_box():
    return render_template(
        "admin/sidebox.html",
        title="管理插件",
        boxes=SideBox.query.order_by(SideBox.id.desc()).all(),
    )


@admin_bp.route("/box/<int:id>/unable")
@login_required
def unable_side_box(id):
    box = SideBox.query.get_or_404(id)
    box.unable = not box.unable

    commit.add(box)

    cache_operate.clean(
        CacheType.GLOBAL,
        (CacheKey.ADS_BOXES if box.is_advertising else CacheKey.SITE_BOXES)
    )
    return redirect(url_for("admin.side_box"))


@admin_bp.route("/box/<int:id>/delete")
@login_required
def delete_side_box(id):
    box = SideBox.query.get_or_404(id)
    commit.delete(box)
    flash("Deleted successfully.")

    cache_operate.clean(
        CacheType.GLOBAL,
        (CacheKey.ADS_BOXES if box.is_advertising else CacheKey.SITE_BOXES)
    )
    return redirect(url_for("admin.side_box"))


@admin_bp.route("/qiniu/picbed", methods=["GET", "POST"])
@login_required
def qiniu_picbed():
    if not current_app.config["NEED_PIC_BED"]:
        flash("You did not set the configuration of QiNiu.")
        return redirect(url_for("admin.index"))

    if request.method == "POST":
        file = request.files["file"]
        filename = file.filename
        img_stream = file.stream.read()

        if img_name := request.form.get("key"):
            filename = re.sub(r'[\/\\\:\*\?"<>|]', r"_", img_name)
        if file.mimetype.startswith("image") and qn.upload_qn(filename, img_stream):
            flash(f"Upload image {filename} successful")
            return redirect(url_for("admin.qiniu_picbed"))

        flash("Upload image fail")
        return redirect(url_for("admin.qiniu_picbed"))

    images = qn.get_all_images()
    return render_template(
        "plugin/picbed.html",
        title="七牛图床",
        images=images,
        counts=len(images)
    )


@admin_bp.route("/qiniu/delete", methods=["GET", "POST"])
@login_required
def delete_img():
    key = request.get_json()["key"]
    if qn.del_file(key):
        flash(f"Delete image {key} successful")
        return redirect(url_for("admin.qiniu_picbed"))

    flash("Delete image fail")
    return redirect(url_for("admin.qiniu_picbed"))


@admin_bp.route("/qiniu/rename", methods=["GET", "POST"])
@login_required
def rename_img():
    key = request.get_json()["key"]
    key_to = request.get_json()["keyTo"]
    if qn.rename_file(key, key_to):
        flash("Rename image successful")
        return redirect(url_for("admin.qiniu_picbed"))

    flash("Rename image fail")
    return redirect(url_for("admin.qiniu_picbed"))


@admin_bp.route("/cache/clean")
@login_required
def clean_all_cache():
    cache_operate.clean()
    flash("Clean all cache success!")
    return redirect(url_for("admin.index"))


@admin_bp.route("/whooshee/reindex")
@login_required
def whooshee_reindex():
    whooshee.reindex()
    flash("Reindex whooshee success!")
    return redirect(url_for("admin.index"))
