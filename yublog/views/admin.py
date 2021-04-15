import os
import re

from flask import redirect, request, flash, render_template, current_app, url_for
from flask_login import login_required, login_user, logout_user, current_user

from yublog.caches import cache_tool, global_cache_key
from yublog.exceptions import DuplicateEntryException
from yublog.extensions import qn, db, whooshee
from yublog.forms import *
from yublog.models import Admin, Post, Page, SiteLink, SideBox, \
    Column, Comment, Talk, Article, Category
from yublog.utils.tools import asyncio_send
from yublog.views import admin_bp
from yublog.views.utils.model_cache_utils import update_linked_cache
from yublog.views.utils.save_utils import save_post, save_category, save_xml


@admin_bp.route('/')
@admin_bp.route('/index')
@login_required
def index():
    return render_template('admin/index.html')


@admin_bp.route('/login/', methods=['GET', 'POST'])
def login():
    form = AdminLogin()
    if form.validate_on_submit():
        user = Admin.query.filter_by(login_name=form.username.data).first()
        if user and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(url_for('admin.index'))
        flash('Invalid account or password.')
    return render_template('admin/login.html', title='登录', form=form)


@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Successfully logged out.')
    return redirect(url_for('admin.index'))


@admin_bp.route('/setting', methods=['GET', 'POST'])
@login_required
def set_site():
    form = AdminSiteForm()
    user = Admin.query.all()[0]
    if form.validate_on_submit():
        user.name = form.username.data
        user.profile = form.profile.data
        user.site_name = form.site_name.data
        user.site_title = form.site_title.data
        user.record_info = form.record_info.data or None
        db.session.add(user)
        db.session.commit()
        flash('Set successfully.')
        # 清除所有缓存
        cache_tool.clean(cache_tool.GLOBAL_KEY)
        return redirect(url_for('admin.index'))
    form.username.data = user.name
    form.profile.data = user.profile
    form.site_name.data = user.site_name
    form.site_title.data = user.site_title
    form.record_info.data = user.record_info or None
    return render_template('admin/profile.html', title='设置网站信息', form=form)


@admin_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            if form.password.data == form.password2.data:
                current_user.password = form.password.data
                db.session.add(current_user)
                flash('Password changed successfully.')
                return redirect(url_for('admin.index'))
            flash('Please confirm whether the passwords are consistent.')
            return redirect(url_for('admin.change_password'))
        flash('Please enter the correct password.')
        return redirect(url_for('admin.change_password'))
    return render_template('admin/change_password.html', form=form, title='更改密码')


@admin_bp.route('/links', methods=['GET', 'POST'])
@login_required
def add_link():
    form = SocialLinkForm()
    fr_form = FriendLinkForm()
    # 社交链接
    if form.submit.data and form.validate_on_submit():
        exist_link = SiteLink.query.filter_by(link=form.link.data).first()
        if exist_link:
            flash('Link already exists...')
            return redirect(url_for('admin.add_link'))

        url = form.link.data
        name = form.name.data
        link = SiteLink(link=url, name=name, is_friend=False)
        db.session.add(link)
        db.session.commit()
        flash('Added successfully.')
        # update cache
        cache_tool.clean(cache_tool.GLOBAL_KEY)
        return redirect(url_for('admin.add_link'))
    # 友链
    if fr_form.submit2.data and fr_form.validate_on_submit():
        exist_link = SiteLink.query.filter_by(link=fr_form.link.data).first()
        if exist_link:
            flash('Link already exists...')
            return redirect(url_for('admin.add_link'))

        link = SiteLink(link=fr_form.link.data, name=fr_form.name.data,
                        info=fr_form.info.data, is_friend=True)
        db.session.add(link)
        db.session.commit()
        flash('Added successfully.')
        # update cache
        cache_tool.update_global(global_cache_key.FRIEND_COUNT, 1, cache_tool.ADD)
        return redirect(url_for('admin.add_link'))
    return render_template('admin/edit_link.html', title="站点链接",
                           form=form, fr_form=fr_form)


@admin_bp.route('/admin-links')
@login_required
def admin_links():
    social_links = SiteLink.query.filter_by(is_friend=False).order_by(SiteLink.id.desc()).all()
    friend_links = SiteLink.query.filter_by(is_friend=True).order_by(SiteLink.id.desc()).all()
    return render_template('admin/link.html', title="管理链接",
                           social_links=social_links, friend_links=friend_links)


@admin_bp.route('/delete/link/<int:id>')
@login_required
def delete_link(id):
    link = SiteLink.query.get_or_404(id)
    db.session.delete(link)
    db.session.commit()
    # update cache
    if link.is_friend:
        cache_tool.update_global(global_cache_key.FRIEND_COUNT, 1, cache_tool.ADD)
    else:
        cache_tool.clean(cache_tool.GLOBAL_KEY)

    return redirect(url_for('admin.admin_links'))


@admin_bp.route('/great/link/<int:id>')
@login_required
def great_link(id):
    link = SiteLink.query.get_or_404(id)
    link.is_great = not link.is_great

    db.session.add(link)
    db.session.commit()
    # 清除缓存
    cache_tool.clean(cache_tool.GLOBAL_KEY)
    return redirect(url_for('admin.admin_links'))


@admin_bp.route('/write', methods=['GET', 'POST'])
@login_required
def write():
    form = AdminWrite()
    if form.validate_on_submit():
        exist = Post.query.filter_by(url_name=form.url_name.data).first()
        if exist:
            flash('Duplicate articles.')
            raise DuplicateEntryException('Duplicate articles.')

        # 保存草稿
        if 'save_draft' in request.form and form.validate():
            post = save_post(form, True)
            db.session.add(post)
            db.session.commit()
            flash('Saved successfully.')
        # 发布文章
        elif 'submit' in request.form and form.validate():
            post = save_post(form)
            db.session.add(post)
            db.session.commit()
            flash('Posted successfully.')
            # updata cache
            cache_tool.clean(cache_tool.GLOBAL_KEY)
            update_linked_cache(post)
        return redirect(url_for('admin.write'))
    return render_template('admin/edit_post.html', form=form, title='写文章')


# 编辑文章或草稿
@admin_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit(id):
    post = Post.query.get_or_404(id)
    form = AdminWrite()
    if form.validate_on_submit():
        category = post.category
        if form.category.data != post.category.category:
            category = save_category(post.category.category, form.category.data)
        if not category.is_show:
            category.is_show = True

        post.category = category
        post.tags = form.tags.data
        post.url_name = form.url_name.data
        post.timestamp = form.time.data
        post.title = form.title.data
        post.body = form.body.data
        # 编辑草稿
        if post.draft:
            if 'save_draft' in request.form and form.validate():
                db.session.add(post)
                flash('Saved successfully.')
            elif 'submit' in request.form and form.validate():
                post.draft = False
                db.session.add(post)
                db.session.commit()
                flash('Posted successfully.')
                # 清除缓存
                cache_tool.clean(cache_tool.GLOBAL_KEY)
                update_linked_cache(post)
                save_xml(post.timestamp)
        else:
            db.session.add(post)
            db.session.commit()
            flash('Update successfully.')
            # 清除对应文章缓存
            key = '_'.join(map(str, ['post', post.year, post.month, post.url_name]))
            cache_tool.clean(key)
            save_xml(post.timestamp)
        return redirect(url_for('admin.admin_edit', id=post.id))
    form.category.data = post.category.category
    form.tags.data = post.tags
    form.url_name.data = post.url_name
    form.time.data = post.timestamp
    form.title.data = post.title
    form.body.data = post.body
    return render_template('admin/edit_post.html', form=form, post=post, title='编辑文章')


@admin_bp.route('/add-page', methods=['GET', 'POST'])
@login_required
def add_page():
    form = AddPageForm()
    if form.validate_on_submit():
        page = Page(title=form.title.data,
                    url_name=form.url_name.data,
                    body=form.body.data,
                    able_comment=form.can_comment.data,
                    show_nav=form.is_nav.data)
        print(f'form: {form}')
        db.session.add(page)
        db.session.commit()
        flash('Posted successfully.')
        if page.show_nav is True:
            # 清除缓存
            cache_tool.clean(cache_tool.GLOBAL_KEY)
        return redirect(url_for('admin.add_page'))
    return render_template('admin/edit_page.html', form=form, title='添加页面')


@admin_bp.route('/edit-page/<name>', methods=['GET', 'POST'])
@login_required
def edit_page(name):
    page = Page.query.filter_by(url_name=name).first()
    start_title = page.title
    form = AddPageForm()
    if form.validate_on_submit():
        page.title = form.title.data
        page.body = form.body.data
        page.able_comment = form.can_comment.data
        page.show_nav = form.is_nav.data
        page.url_name = form.url_name.data
        db.session.add(page)
        db.session.commit()
        flash('Update successfully.')
        # 清除缓存
        cache_tool.clean(cache_tool.GLOBAL_KEY)
        return redirect(url_for('admin.edit_page', name=page.url_name))
    form.title.data = start_title
    form.body.data = page.body
    form.can_comment.data = page.able_comment
    form.is_nav.data = page.show_nav
    form.url_name.data = page.url_name
    return render_template('admin/edit_page.html', title="编辑页面", form=form, page=page)


@admin_bp.route('/page/delete/<name>')
@login_required
def delete_page(name):
    page = Page.query.filter_by(title=name).first()
    db.session.delete(page)
    db.session.commit()
    flash('Deleted successfully.')
    if page.isNav is True:
        # 清除缓存
        cache_tool.clean(cache_tool.GLOBAL_KEY)
    return redirect(url_for('admin.admin_pages'))


@admin_bp.route('/draft')
@login_required
def admin_drafts():
    drafts = Post.query.filter_by(draft=True).order_by(Post.id.desc()).all()
    return render_template('admin/draft.html', drafts=drafts, title='管理草稿')


@admin_bp.route('/pages')
@login_required
def admin_pages():
    pages = Page.query.order_by(Page.id.desc()).all()
    return render_template('admin/page.html', pages=pages, title='管理页面')


@admin_bp.route('/posts')
@login_required
def admin_posts():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(draft=False).order_by(Post.id.desc()).paginate(
        page, per_page=current_app.config['ADMIN_POSTS_PER_PAGE'],
        error_out=False
    )
    posts = [post for post in pagination.items]
    return render_template('admin/post.html', title='管理文章',
                           posts=posts, pagination=pagination)


@admin_bp.route('/delete/<int:id>')
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    _category = Category.query.get_or_404(post.category_id)
    if _category.posts.count() == 1:
        db.session.delete(_category)

    db.session.delete(post)
    db.session.commit()
    flash('Deleted successfully.')
    # update cache
    if post.draft is False:
        cache_tool.update_global(global_cache_key.POST_COUNT, 1, cache_tool.REMOVE)
    return redirect(url_for('admin.admin_posts'))


@admin_bp.route('/comments')
@login_required
def admin_comments():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['ADMIN_COMMENTS_PER_PAGE'],
        error_out=False
    )
    comments = pagination.items
    return render_template('admin/comment.html', title='管理评论',
                           comments=comments, pagination=pagination)


@admin_bp.route('/delete/comment/<int:id>')
@login_required
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    page = comment.page
    post = comment.post
    db.session.delete(comment)
    db.session.commit()
    flash('Deleted successfully.')

    if comment.disabled is True:
        if page and page.url_name == 'guest-book':
            # 清除缓存
            cache_tool.update_global(global_cache_key.GUEST_BOOK_COUNT, 1, cache_tool.REMOVE)
        elif post and isinstance(post, Post):
            # 删除文章缓存
            cache_key = '_'.join(map(str, ['post', post.year, post.month, post.url_name]))
            post_cache = cache_tool.get(cache_key)
            post_cache['comment_count'] -= 1
            cache_tool.set(cache_key, post_cache)
    return redirect(url_for('admin.admin_comments'))


@admin_bp.route('/allow/comment/<int:id>')
@login_required
def allow_comment(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    flash('允许通过')

    # 发送邮件
    admin_mail = current_app.config['ADMIN_MAIL']

    if comment.replied_id:
        reply_to_comment = Comment.query.get_or_404(comment.replied_id)
        reply_email = reply_to_comment.email
        if reply_email != admin_mail:
            # 邮件配置
            to_addr = reply_email
            # 站点链接
            base_url = current_app.config['WEB_URL']
            # 收件人就是被回复的人
            nickname = reply_to_comment.author
            com = comment.comment

            post_url = ''
            if comment.post:
                post_url = 'http://{}'.format('/'.join(
                    map(str, [base_url, comment.post.year, comment.post.month, comment.post.url_name])))
            elif comment.page:
                post_url = 'http://{0}/page/{1}'.format(base_url, comment.page.url_name)
            elif comment.article:
                post_url = 'http://{0}/column/{1}/{2}'.format(
                    base_url, comment.article.column.url_name, str(comment.article.id))
            # 发送邮件
            msg = render_template('user_mail.html', nickname=nickname, comment=com, url=post_url)
            asyncio_send(to_addr, msg)

    page = comment.page
    post = comment.post
    if page and page.url_name == 'guest-book':
        # 清除缓存
        cache_tool.update_global(global_cache_key.GUEST_BOOK_COUNT, 1, cache_tool.ADD)
    elif post and isinstance(post, Post):
        # 更新文章缓存
        cache_key = '_'.join(map(str, ['post', post.year, post.month, post.url_name]))
        post_cache = cache_tool.get(cache_key)
        if post_cache:
            post_cache['comment_count'] += 1
            cache_tool.set(cache_key, post_cache)
    return redirect(url_for('admin.admin_comments'))


@admin_bp.route('/unable/comment/<int:id>')
@login_required
def unable_comment(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    flash('Hide successfully.')

    page = comment.page
    post = comment.post
    if page and page.url_name == 'guest-book':
        # 清除缓存
        cache_tool.update_global(global_cache_key.GUEST_BOOK_COUNT, 1, cache_tool.REMOVE)
    elif post and isinstance(post, Post):
        # 更新文章缓存
        cache_key = '_'.join(map(str, ['post', post.year, post.month, post.url_name]))
        post_cache = cache_tool.get(cache_key)
        if post_cache:
            post_cache['comment_count'] -= 1
            cache_tool.set(cache_key, post_cache)
    return redirect(url_for('admin.admin_comments'))


@admin_bp.route('/write/talk', methods=['GET', 'POST'])
@login_required
def write_talk():
    form = TalkForm()
    if form.validate_on_submit():
        talk = Talk(talk=form.talk.data)
        db.session.add(talk)
        db.session.commit()
        flash('Posted successfully.')
        # 清除缓存
        cache_tool.update_global(global_cache_key.TALK, talk.body_to_html)
        return redirect(url_for('admin.write_talk'))
    return render_template('admin/edit_talk.html', title='写说说', form=form)


@admin_bp.route('/talk')
@login_required
def admin_talk():
    talks = Talk.query.order_by(Talk.timestamp.desc()).all()
    return render_template('admin/talk.html', title='管理说说', talks=talks)


@admin_bp.route('/delete/talk/<int:id>')
@login_required
def delete_talk(id):
    count = Talk.query.count()
    if count == 1:
        flash('There must be one talk.')
        return redirect(url_for('admin.admin_talk'))
    talk = Talk.query.get_or_404(id)
    db.session.delete(talk)
    db.session.commit()
    flash('Deleted successfully.')

    # update cache
    new_talk = Talk.query.order_by(Talk.timestamp.desc()).first()
    value = new_talk.body_to_html if new_talk else '这家伙啥都不想说...'
    cache_tool.update_global(global_cache_key.TALK, value)
    return redirect(url_for('admin.admin_talk'))


# 管理主题
@admin_bp.route('/write/column', methods=['GET', 'POST'])
@login_required
def write_column():
    form = ColumnForm()
    if form.validate_on_submit():
        column = Column(title=form.column.data, timestamp=form.date.data,
                        url_name=form.url_name.data, body=form.body.data,
                        password=form.password.data)
        db.session.add(column)
        db.session.commit()
        flash('Posted successfully.')
        return redirect(url_for('admin.admin_column', id=column.id))
    return render_template('admin_column/edit_column.html',
                           form=form, title='编辑专题')


@admin_bp.route('/edit/column/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_column(id):
    column = Column.query.get_or_404(id)
    form = ColumnForm()
    if form.validate_on_submit():
        column.title = form.column.data
        column.timestamp = form.date.data
        column.url_name = form.url_name.data
        column.body = form.body.data
        password = form.password.data
        if password:
            column.password = password
        db.session.add(column)
        db.session.commit()
        flash('Update successfully.')
        cache_tool.clean('column_' + column.url_name)
        return redirect(url_for('admin.admin_column', id=column.id))

    form.column.data = column.title
    form.date.data = column.timestamp
    form.url_name.data = column.url_name
    form.body.data = column.body
    return render_template('admin_column/edit_column.html',
                           form=form, title='更新专题', column=column)


@admin_bp.route('/admin/columns')
@login_required
def admin_columns():
    columns = Column.query.all()
    # print(f'columns: {columns}')
    return render_template('admin_column/columns.html',
                           columns=columns, title='管理专题')


@admin_bp.route('/admin/column/<int:id>')
@login_required
def admin_column(id):
    column = Column.query.get_or_404(id)
    articles = column.articles.order_by(Article.timestamp.desc()).all()
    return render_template('admin_column/column.html', column=column,
                           articles=articles, title=column.title)


@admin_bp.route('/delete/column/<int:id>')
@login_required
def delete_column(id):
    column = Column.query.get_or_404(id)
    articles = column.articles.order_by(Article.timestamp.desc()).all()
    db.session.delete(column)
    db.session.commit()
    flash('Deleted successfully.')
    # clean all of this column cache
    cache_tool.clean('column_' + column.url_name)
    return redirect(url_for('admin.admin_columns'))


@admin_bp.route('/<url>/write/article', methods=['GET', 'POST'])
@login_required
def write_column_article(url):
    column = Column.query.filter_by(url_name=url).first()
    form = ColumnArticleForm()
    if form.validate_on_submit():
        article = Article(title=form.title.data, timestamp=form.date.data,
                          body=form.body.data, secrecy=form.secrecy.data, column=column)
        db.session.add(article)
        db.session.commit()
        flash('Added successfully.')
        # clean cache
        cache_tool.clean('column_' + url)
        return redirect(url_for('admin.admin_column', id=column.id))
    return render_template('admin_column/edit_article.html', form=form,
                           title='编辑文章', column=column)


@admin_bp.route('/<url>/edit/article/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_column_article(url, id):
    column = Column.query.filter_by(url_name=url).first()
    article = Article.query.filter_by(id=id).first()
    # _title = article.title

    form = ColumnArticleForm()
    if form.validate_on_submit():
        article.title = form.title.data
        article.timestamp = form.date.data
        article.secrecy = form.secrecy.data
        article.body = form.body.data
        db.session.add(article)
        db.session.commit()
        flash('Update successfully.')
        # clear cache
        cache_tool.clean('column_' + url)
        return redirect(url_for('admin.admin_column', id=column.id))

    form.title.data = article.title
    form.date.data = article.timestamp
    form.body.data = article.body
    form.secrecy.data = article.secrecy
    return render_template('admin_column/edit_article.html', form=form,
                           title='更新文章', column=column, article=article)


@admin_bp.route('/<url>/delete/article/<int:id>')
@login_required
def delete_column_article(url, id):
    column = Column.query.filter_by(url_name=url).first()
    article = Article.query.filter_by(id=id).first()
    db.session.delete(article)
    db.session.commit()
    flash('Deleted successfully.')
    # 清除对于缓存
    cache_tool.clean('column_' + url)
    return redirect(url_for('admin.admin_column', id=column.id))


# 上传文件到静态目录
@admin_bp.route('/upload/file', methods=['GET', 'POST'])
@login_required
def upload_file():
    source_folder = current_app.config['UPLOAD_PATH']
    if request.method == 'POST':
        file = request.files['file']
        filename = file.filename
        path = os.path.join(source_folder, filename)
        file.save(path)
        return redirect(url_for('admin.index'))
    return render_template('admin/upload_file.html', title="上传文件")


# 侧栏box---begin
@admin_bp.route('/add/sidebox', methods=['GET', 'POST'])
@login_required
def add_side_box():
    form = SideBoxForm()
    if form.validate_on_submit():
        is_advertising = form.is_advertising.data
        box = SideBox(title=form.title.data, body=form.body.data,
                      is_advertising=is_advertising)
        db.session.add(box)
        db.session.commit()
        flash('Added successfully.')
        # update cache
        cache_tool.clean(cache_tool.GLOBAL_KEY)
        return redirect(url_for('admin.admin_side_box'))
    return render_template('admin/edit_sidebox.html', form=form,
                           title='添加插件')


@admin_bp.route('/edit/sidebox/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_side_box(id):
    box = SideBox.query.get_or_404(id)
    form = SideBoxForm()
    if form.validate_on_submit():
        box.title = form.title.data
        box.body = form.body.data
        box.is_advertising = form.is_advertising.data
        db.session.add(box)
        db.session.commit()
        flash('Update successfully.')
        # update cache
        cache_tool.clean(cache_tool.GLOBAL_KEY)
        return redirect(url_for('admin.admin_side_box'))

    form.title.data = box.title
    form.body.data = box.body
    form.is_advertising.data = box.is_advertising
    return render_template('admin/edit_sidebox.html', form=form,
                           title='更新插件', box=box)


@admin_bp.route('/sideboxs')
@login_required
def admin_side_box():
    boxes = SideBox.query.order_by(SideBox.id.desc()).all()
    return render_template('admin/sidebox.html', boxes=boxes, title='管理插件')


@admin_bp.route('/unable/box/<int:id>')
@login_required
def unable_side_box(id):
    box = SideBox.query.get_or_404(id)
    box.unable = not box.unable

    db.session.add(box)
    db.session.commit()
    # 清除缓存
    cache_tool.clean(cache_tool.GLOBAL_KEY)
    return redirect(url_for('admin.admin_side_box'))


@admin_bp.route('/delete/box/<int:id>')
@login_required
def delete_side_box(id):
    box = SideBox.query.get_or_404(id)
    db.session.delete(box)
    db.session.commit()
    flash('Deleted successfully.')
    # 清除缓存
    cache_tool.clean(cache_tool.GLOBAL_KEY)
    return redirect(url_for('admin.admin_side_box'))
# 侧栏box---end


# qiniu picture bed begin
@admin_bp.route('/qiniu/picbed', methods=['GET', 'POST'])
@login_required
def qiniu_picbed():
    # 判断是否需要七牛图床
    need_qiniu_picbed = current_app.config['NEED_PIC_BED']
    if not need_qiniu_picbed:
        flash('你没有设置七牛配置...')
        return redirect(url_for('admin.index'))
    if request.method == 'POST':

        img_name = request.form.get('key', None)
        file = request.files['file']
        filename = file.filename
        img_stream = file.stream.read()
        if img_name:
            filename = re.sub(r'[\/\\\:\*\?"<>|]', r'_', img_name)
        if file.mimetype.startswith('image') and qn.upload_qn(filename, img_stream):
            flash('Upload image {0} successful'.format(filename))
            return redirect(url_for('admin.qiniu_picbed'))

        flash('Upload image fail')
        return redirect(url_for('admin.qiniu_picbed'))
    # get all images
    images = qn.get_all_images()
    counts = len(images)

    return render_template('plugin/picbed.html',
                           title="七牛图床", images=images, counts=counts)


@admin_bp.route('/qiniu/delete', methods=['GET', 'POST'])
@login_required
def delete_img():
    key = request.get_json()['key']
    if qn.del_file(key):
        flash('Delete image {0} successful'.format(key))
        return redirect(url_for('admin.qiniu_picbed'))
    flash('Delete image fail')
    return redirect(url_for('admin.qiniu_picbed'))


@admin_bp.route('/qiniu/rename', methods=['GET', 'POST'])
@login_required
def rename_img():
    key = request.get_json()['key']
    key_to = request.get_json()['keyTo']
    if qn.rename_file(key, key_to):
        flash('Rename image {0} successful'.format(key))
        return redirect(url_for('admin.qiniu_picbed'))
    flash('Rename image fail')
    return redirect(url_for('admin.qiniu_picbed'))
# qiniu picture bed end


@admin_bp.route('/clean/cache/all')
@login_required
def clean_all_cache():
    cache_tool.clean(cache_tool.ALL_KEY)
    flash('Clean all cache success!')
    return redirect(url_for('admin.index'))


@admin_bp.route('/reindex')
@login_required
def whooshee_reindex():
    whooshee.reindex()
    flash('Reindex whooshee success!')
    return redirect(url_for('admin.index'))
