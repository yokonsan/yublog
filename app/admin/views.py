from flask import render_template, redirect, url_for, g, request, flash
from flask_login import login_required, current_user, login_user, logout_user

from .. import db
from ..models import *
from . import admin
from .forms import *


@admin.route('/')
@admin.route('/index')
@login_required
def index():
    return render_template('admin_menu.html')

@admin.route('/login/', methods=['GET', 'POST'])
def login():
    form = AdminLogin()
    if form.validate_on_submit():
        user = Admin.query.filter_by(login_name=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(url_for('admin.index'))
        flash('账号或密码无效。')
    return render_template('login.html',
                           title='登录',
                           form=form)

@admin.route('/logout')
@login_required
def logout():
    logout_user()
    flash('你已经登出账号。')
    return redirect(url_for('admin.index'))

@admin.route('/links', methods=['GET', 'POST'])
@login_required
def add_link():
    form = AddLinkForm()
    if form.validate_on_submit():
        link = SocialLink(link=form.link.data,
                      name=form.name.data,
                      isFriendLink=form.isFriendLink.data)
        db.session.add(link)
        flash('添加成功')
        db.session.commit()
        return redirect(url_for('admin.add_link'))
    return render_template('admin_add_link.html', form=form)

def save_tags(tags, id):
    """
    保存标签到模型
    :param tags: 标签集合，创建时间，文章ID
    """
    for tag in tags:
        tag = Tag(tag=tag)
        db.session.add(tag)
        post_tag = PostTag(tag_id=tag.id, post_id=id)
        db.session.add(post_tag)
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
    if draft == True:
        post = Post(body=form.body.data,
                title=form.title.data,
                url_name=form.url_name.data,
                category=Category(category=form.category.data),
                tags = form.tags.data,
                timestamp=form.time.data,
                draft=True)
    else:
        post = Post(body=form.body.data,
                title=form.title.data,
                url_name=form.url_name.data,
                category=Category(category=form.category.data),
                tags=form.tags.data,
                timestamp=form.time.data,
                draft=False)
    # 保存标签模型
    save_tags(tags, post.id)

    return post

@admin.route('/write', methods=['GET', 'POST'])
@login_required
def write():
    form = AdminWrite()
    if form.validate_on_submit():
        if 'save_draft' in request.form and form.validate():
            post = save_post(form, True)
            db.session.add(post)
            flash('保存成功！')
        elif 'submit' in request.form and form.validate():
            post = save_post(form)
            db.session.add(post)
            flash('发布成功！')
        db.session.commit()
        return redirect(url_for('admin.write'))
    return render_template('admin_write.html',
                           form=form,
                           title='写文章')

@admin.route('/edit/<name>', methods=['GET', 'POST'])
@login_required
def admin_edit(name):
    pass

@admin.route('/draft')
@login_required
def admin_draft():
    posts = Post.query.order_by(Post.id.desc()).all()
    drafts = [post for post in posts if post.draft]
    return render_template('admin_draft.html',
                           drafts=drafts,
                           title='管理草稿')

@admin.route('/pages')
@login_required
def add_page():
    pages = Page.query.order_by(Page.id.desc()).all()
    return render_template('admin_page.html',
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
    posts = [post for post in pagination.items if post.draft == False]
    return render_template('admin_post.html',
                           title='管理文章',
                           posts=posts,
                           pagination=pagination)


