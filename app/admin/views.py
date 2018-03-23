import os

from flask import render_template, redirect, request, flash, current_app, url_for
from flask_login import login_required, login_user, logout_user

from .. import cache
from ..models import *
from . import admin
from .forms import *
from ..utils import get_sitemap, save_file, get_rss_xml


def clean_cache(key):
    """
    在发布文章后删除首页，归档，分类，标签缓存，
    在更新文章后删除对应文章缓存
    在添加说说，更改友链页后删除对应缓存
    :param key: cache prefix
    """
    if key == 'all':
        cache.clear()
    elif key != 'all' and cache.get(key):
        cache.delete(key)
    else:
        pass


@admin.route('/')
@admin.route('/index')
@login_required
def index():
    return render_template('admin/admin_menu.html')

@admin.route('/login/', methods=['GET', 'POST'])
def login():
    form = AdminLogin()
    if form.validate_on_submit():
        user = Admin.query.filter_by(login_name=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(url_for('admin.index'))
        flash('账号或密码无效。')
    return render_template('admin/login.html',
                           title='登录',
                           form=form)

@admin.route('/logout')
@login_required
def logout():
    logout_user()
    flash('你已经登出账号。')
    return redirect(url_for('admin.index'))

@admin.route('/setting', methods=['GET', 'POST'])
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
        flash('设置成功')
        # 清除所有缓存
        clean_cache('all')
        return redirect(url_for('admin.index'))
    form.username.data = user.name
    form.profile.data = user.profile
    form.site_name.data = user.site_name
    form.site_title.data = user.site_title
    form.record_info.data = user.record_info or None
    return render_template('admin/admin_profile.html',
                           title='设置网站信息',
                           form=form)


@admin.route('/links', methods=['GET', 'POST'])
@login_required
def add_link():
    form = SocialLinkForm()
    fr_form = FriendLinkForm()
    # 社交链接
    if form.submit.data and form.validate_on_submit():
        exist_link = SiteLink.query.filter_by(link=form.link.data).first()
        if exist_link:
            flash('链接已经存在哦...')
            return redirect(url_for('admin.add_link'))
        else:
            link = SiteLink(link=form.link.data, name=form.name.data,
                            isFriendLink=False)
            db.session.add(link)
            db.session.commit()
            flash('添加成功')
            return redirect(url_for('admin.add_link'))
    # 友链
    if fr_form.submit2.data and fr_form.validate_on_submit():
        exist_link = SiteLink.query.filter_by(link=fr_form.link.data).first()
        if exist_link:
            flash('链接已经存在哦...')
            return redirect(url_for('admin.add_link'))
        else:
            link = SiteLink(link=fr_form.link.data, name=fr_form.name.data,
                            info=fr_form.info.data, isFriendLink=True)
            db.session.add(link)
            db.session.commit()
            flash('添加成功')
            # 清除缓存
            clean_cache('friends')
            return redirect(url_for('admin.add_link'))
    return render_template('admin/admin_add_link.html', title="站点链接",
                           form=form, fr_form=fr_form)

@admin.route('/admin-links')
@login_required
def admin_links():
    links = SiteLink.query.order_by(SiteLink.id.desc()).all()
    social_links = [link for link in links if link.isFriendLink is False]
    friend_links = [link for link in links if link.isFriendLink is True]
    return render_template('admin/admin_link.html', title="管理链接",
                           social_links=social_links, friend_links=friend_links)

@admin.route('/delete/link/<int:id>')
@login_required
def delete_link(id):
    link = SiteLink.query.get_or_404(id)
    db.session.delete(link)
    db.session.commit()
    # 清除缓存
    clean_cache('all')
    return redirect(url_for('admin.admin_links'))

@admin.route('/great/link/<int:id>')
@login_required
def great_link(id):
    link = SiteLink.query.get_or_404(id)
    if link.isGreatLink:
        link.isGreatLink = False
    else:
        link.isGreatLink = True
    db.session.add(link)
    db.session.commit()
    # 清除缓存
    clean_cache('friends')
    return redirect(url_for('admin.admin_links'))

def save_tags(tags):
    """
    保存标签到模型
    :param tags: 标签集合，创建时间，文章ID
    """
    for tag in tags:
        exist_tag = Tag.query.filter_by(tag=tag).first()
        if not exist_tag:
            tag = Tag(tag=tag)
            db.session.add(tag)
    db.session.commit()

def save_post(form, draft=False):
    """
    封装保存文章到数据库的重复操作
    :param form: write or edit form
    :param draft: article is or not draft
    :return: post object
    """

    category = Category.query.filter_by(category=form.category.data).first()
    if not category:
        category = Category(category=form.category.data)
        db.session.add(category)

    tags = [tag for tag in form.tags.data.split(',')]
    # print(form.body.data)
    if draft is True:
        post = Post(body=form.body.data, title=form.title.data,
                    url_name=form.url_name.data, category=category,
                    tags=form.tags.data, timestamp=form.time.data, draft=True)
    else:
        post = Post(body=form.body.data, title=form.title.data,
                    url_name=form.url_name.data, category=category,
                    tags=form.tags.data, timestamp=form.time.data, draft=False)
        # 保存标签模型
        save_tags(tags)
        # 更新xml
        update_xml(post.timestamp)

    return post

# 编辑文章后更新sitemap
def update_xml(update_time):
    # 获取配置信息
    author_name = current_app.config['ADMIN_NAME']
    title = current_app.config['SITE_NAME']
    subtitle = current_app.config['SITE_TITLE']
    protocol = current_app.config['WEB_PROTOCOL']
    url = current_app.config['WEB_URL']
    web_time = current_app.config['WEB_START_TIME']
    count = current_app.config['RSS_COUNTS']

    post_list = Post.query.order_by(Post.timestamp.desc()).all()
    posts = [post for post in post_list if post.draft is False]
    # sitemap
    sitemap = get_sitemap(posts)
    save_file(sitemap, 'sitemap.xml')
    # rss
    rss_posts = posts[:count]
    rss = get_rss_xml(author_name, protocol, url, title, subtitle, web_time, update_time, rss_posts)
    save_file(rss, 'atom.xml')

@admin.route('/write', methods=['GET', 'POST'])
@login_required
def write():
    form = AdminWrite()
    if form.validate_on_submit():
        # 保存草稿
        if 'save_draft' in request.form and form.validate():
            post = save_post(form, True)
            db.session.add(post)
            flash('保存成功！')
        # 发布文章
        elif 'submit' in request.form and form.validate():
            post = save_post(form)
            db.session.add(post)
            flash('发布成功！')
            # 清除缓存
            clean_cache('all')
        db.session.commit()
        return redirect(url_for('admin.write'))
    return render_template('admin/admin_write.html',
                           form=form,
                           title='写文章')

# 编辑文章或草稿
@admin.route('/edit/<int:time>/<name>', methods=['GET', 'POST'])
@login_required
def admin_edit(time, name):
    timestamp = str(time)[0:4] + '-' + str(time)[4:6] + '-' + str(time)[6:8]
    post = Post.query.filter_by(timestamp=timestamp, url_name=name).first()

    form = AdminWrite()
    if form.validate_on_submit():
        category = Category.query.filter_by(category=form.category.data).first()
        post.category = category
        post.tags = form.tags.data
        post.url_name = form.url_name.data
        post.timestamp = form.time.data
        post.title = form.title.data
        post.body = form.body.data
        # 编辑草稿
        if post.draft is True:
            if 'save_draft' in request.form and form.validate():
                db.session.add(post)
                flash('保存成功！')
            elif 'submit' in request.form and form.validate():
                post.draft = False
                db.session.add(post)
                db.session.commit()
                flash('发布成功')
                # 清除缓存
                clean_cache('all')
                # 更新 xml
                update_xml(post.timestamp)
            return redirect(url_for('admin.admin_edit', time=post.timestampInt, name=post.url_name))
        # 编辑文章
        else:
            db.session.add(post)
            db.session.commit()
            flash('更新成功')
            # 清除对应文章缓存
            key = 'post/{path}/'.format(path='/'+str(post.year)+'/'+str(post.month)+'/'+str(post.url_name))
            clean_cache(key)
            update_xml(post.timestamp)
            return redirect(url_for('admin.admin_edit', time=post.timestampInt, name=post.url_name))
    form.category.data = post.category.category
    form.tags.data = post.tags
    form.url_name.data = post.url_name
    form.time.data = post.timestamp
    form.title.data = post.title
    form.body.data = post.body
    return render_template('admin/admin_write.html',
                           form=form,
                           post=post,
                           title='编辑文章')

@admin.route('/add-page', methods=['GET', 'POST'])
@login_required
def add_page():
    form = AddPageForm()
    if form.validate_on_submit():
        page = Page(title=form.title.data,
                    url_name=form.url_name.data,
                    body=form.body.data,
                    canComment=form.can_comment.data,
                    isNav=form.is_nav.data)
        db.session.add(page)
        db.session.commit()
        flash('添加成功')
        if page.isNav is True:
            # 清除缓存
            clean_cache('all')
        return redirect(url_for('admin.add_page'))
    return render_template('admin/admin_add_page.html',
                           form=form,
                           title='添加页面')

@admin.route('/edit-page/<name>', methods=['GET', 'POST'])
@login_required
def edit_page(name):
    page = Page.query.filter_by(url_name=name).first()
    start_title = page.title
    form = AddPageForm()
    if form.validate_on_submit():
        page.title = form.title.data
        page.body = form.body.data
        page.canComment = form.can_comment.data
        page.isNav = form.is_nav.data
        page.url_name = form.url_name.data
        db.session.add(page)
        db.session.commit()
        flash('更新成功')
        # 清除缓存
        clean_cache('all')
        return redirect(url_for('admin.edit_page', name=page.url_name))
    form.title.data = start_title
    form.body.data = page.body
    form.can_comment.data = page.canComment
    form.is_nav.data = page.isNav
    form.url_name.data = page.url_name
    return render_template('admin/admin_add_page.html',
                           title="编辑页面",
                           form=form,
                           page=page)

@admin.route('/page/delete/<name>')
@login_required
def delete_page(name):
    page = Page.query.filter_by(title=name).first()
    db.session.delete(page)
    db.session.commit()
    flash('删除成功')
    if page.isNav is True:
        # 清除缓存
        clean_cache('all')
    return redirect(url_for('admin.admin_pages'))

@admin.route('/draft')
@login_required
def admin_drafts():
    posts = Post.query.order_by(Post.id.desc()).all()
    drafts = [post for post in posts if post.draft]
    return render_template('admin/admin_draft.html',
                           drafts=drafts,
                           title='管理草稿')

@admin.route('/pages')
@login_required
def admin_pages():
    pages = Page.query.order_by(Page.id.desc()).all()
    return render_template('admin/admin_page.html',
                           pages=pages,
                           title='管理页面')

@admin.route('/posts')
@login_required
def admin_posts():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.id.desc()).paginate(
        page, per_page=current_app.config['ADMIN_POSTS_PER_PAGE'],
        error_out=False
    )
    posts = [post for post in pagination.items if post.draft is False]
    return render_template('admin/admin_post.html',
                           title='管理文章',
                           posts=posts,
                           pagination=pagination)

@admin.route('/delete/<int:time>/<name>')
@login_required
def delete(time, name):
    timestamp = str(time)[0:4] + '-' + str(time)[4:6] + '-' + str(time)[6:8]
    post = Post.query.filter_by(timestamp=timestamp, url_name=name).first()
    db.session.delete(post)
    db.session.commit()
    flash('删除成功')
    # 清除缓存
    clean_cache('all')
    return redirect(url_for('admin.admin_posts'))

@admin.route('/comments')
@login_required
def admin_comments():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['ADMIN_COMMENTS_PER_PAGE'],
        error_out=False
    )
    comments = pagination.items
    return render_template('admin/admin_comment.html', title='管理评论',
                        comments=comments, pagination=pagination)

@admin.route('/delete/comment/<int:id>')
@login_required
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    flash('删除成功')

    page = comment.page
    if page and page.url_name == 'guestbook':
        # 清除缓存
        clean_cache('all')
    return redirect(url_for('admin.admin_comments'))

@admin.route('/allow/comment/<int:id>')
@login_required
def allow_comment(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    flash('允许通过')

    page = comment.page
    if page and page.url_name == 'guestbook':
        # 清除缓存
        clean_cache('all')
    return redirect(url_for('admin.admin_comments'))

@admin.route('/unable/comment/<int:id>')
@login_required
def unable_comment(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    flash('隐藏成功')

    page = comment.page
    if page and page.url_name == 'guestbook':
        # 清除缓存
        clean_cache('all')
    return redirect(url_for('admin.admin_comments'))

@admin.route('/write/shuoshuo', methods=['GET','POST'])
@login_required
def write_shuoshuo():
    form = ShuoForm()
    if form.validate_on_submit():
        shuo = Shuoshuo(shuo=form.shuoshuo.data)
        db.session.add(shuo)
        db.session.commit()
        flash('发布成功')
        # 清除缓存
        clean_cache('all')
        return redirect(url_for('admin.write_shuoshuo'))
    return render_template('admin/admin_write_shuoshuo.html',
                           title='写说说', form=form)

@admin.route('/shuos')
@login_required
def admin_shuos():
    shuos = Shuoshuo.query.order_by(Shuoshuo.timestamp.desc()).all()
    return render_template('admin/admin_shuoshuo.html',
                           title='管理说说',
                           shuos=shuos)

@admin.route('/delete/shuoshuo/<int:id>')
@login_required
def delete_shuo(id):
    shuo = Shuoshuo.query.get_or_404(id)
    db.session.delete(shuo)
    db.session.commit()
    flash('删除成功')
    # 清除缓存
    clean_cache('all')
    return redirect(url_for('admin.admin_shuos'))


# 管理主题
@admin.route('/write/column', methods=['GET','POST'])
@login_required
def write_column():
    form = ColumnForm()
    if form.validate_on_submit():
        column = Column(column=form.column.data, timestamp=form.date.data,
                        url_name=form.url_name.data, body=form.body.data)
        db.session.add(column)
        db.session.commit()
        flash('专题发布成功！')
        return redirect(url_for('admin.admin_column', id=column.id))
    return render_template('admin_column/edit_column.html',
                           form=form, title='编辑专题')

@admin.route('/edit/column/<int:id>', methods=['GET','POST'])
@login_required
def edit_column(id):
    column = Column.query.get_or_404(id)
    form = ColumnForm()
    if form.validate_on_submit():
        column = Column(column=form.column.data, timestamp=form.date.data,
                        url_name=form.url_name.data, body=form.body.data)
        db.session.add(column)
        db.session.commit()
        flash('专题更新成功！')
        return redirect(url_for('admin.admin_column', id=column.id))

    form.column.data = column.column
    form.date.data = column.timestamp
    form.url_name.data = column.url_name
    form.body.data = column.body
    return render_template('admin_column/edit_column.html',
                           form=form, title='更新专题', column=column)

@admin.route('/admin/columns')
@login_required
def admin_columns():
    columns = Column.query.all()
    return render_template('admin_column/admin_columns.html',
                           columns=columns, title='管理专题')

@admin.route('/admin/column/<int:id>')
@login_required
def admin_column(id):
    column = Column.query.get_or_404(id)
    articles = column.articles.order_by(Article.timestamp.desc()).all()
    return render_template('admin_column/admin_column.html', column=column,
                           articles=articles, title=column.column)

@admin.route('/delete/column/<int:id>')
@login_required
def delete_column(id):
    column = Column.query.get_or_404(id)
    db.session.delete(column)
    db.session.commit()
    flash('删除专题')
    return redirect(url_for('admin.admin_columns'))

@admin.route('/<url>/write/article', methods=['GET','POST'])
@login_required
def write_column_article(url):
    column = Column.query.filter_by(url_name=url).first()
    form = ColumnArticleForm()
    if form.validate_on_submit():
        article = Article(title=form.title.data, timestamp=form.date.data,
                          body=form.body.data, secrecy=form.secrecy.data, column=column)
        db.session.add(article)
        db.session.commit()
        flash('添加文章成功！')
        return redirect(url_for('admin.admin_column', id=column.id))
    return render_template('admin_column/write_article.html', form=form,
                           title='编辑文章', column=column)

@admin.route('/<url>/edit/article/<int:id>', methods=['GET','POST'])
@login_required
def edit_column_article(url, id):
    column = Column.query.filter_by(url_name=url).first()
    article = Article.query.filter_by(id=id).first()

    form = ColumnArticleForm()
    if form.validate_on_submit():
        article = Article(title=form.title.data, timestamp=form.date.data,
                          body=form.body.data, secrecy=form.secrecy.data, column=column)
        db.session.add(article)
        db.session.commit()
        flash('更新文章成功！')
        return redirect(url_for('admin.admin_column', id=column.id))

    form.title.data = article.title
    form.date.data = article.timestamp
    form.body.data = article.body
    form.secrecy.data = article.secrecy
    return render_template('admin_column/write_article.html', form=form,
                           title='更新文章', column=column, article=article)

@admin.route('/<url>/edit/article/<int:id>')
@login_required
def delete_column_article(url, id):
    column = Column.query.filter_by(url_name=url).first()
    article = Article.query.filter_by(id=id).first()
    db.session.delete(article)
    db.session.commit()
    flash('删除文章！')
    return redirect(url_for('admin.admin_column', id=column.id))


# 上传文件到静态目录
@admin.route('/upload/file', methods=['GET', 'POST'])
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



