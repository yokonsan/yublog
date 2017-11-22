from flask import render_template, redirect, url_for, g, request, flash
from flask_login import login_required, current_user, login_user, logout_user

from .. import db
from ..models import *
from . import admin
from .forms import *


@admin.route('/', methods=['GET', 'POST'])
@admin.route('/index', methods=['GET', 'POST'])
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

@admin.route('/edit-site')
@login_required
def edit_site():
    pass

def save_tags(tags, id):
    """
    保存标签到模型
    :param tags: 标签集合，创建时间，文章ID
    """
    for tag in tags:
        tag = Tag(tag=tag, post_id=id)
        db.session.add(tag)
    db.session.commit()

def save_post(form, draft=False):
    """
    封装保存文章到数据库的重复操作
    :param form: write or edit form
    :param draft: article is or not draft
    :return: post object
    """
    tags = [tag for tag in form.tags.data.split(',')]
    post = Post(body=form.body.data,
                title=form.title.data,
                url_name=form.url_name.data,
                category=form.category.data,
                timestamp=form.time.data)
    if draft == True:
        Post.draft = True
    else:
        Post.draft = False
    # 保存标签模型
    save_tags(tags, post.id)

    return post

@admin.route('/write', methods=['GET', 'POST'])
@login_required
def write():
    form = AdminWrite()
    print('1')
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

@admin.route('/draft')
@login_required
def admin_draft():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    drafts = [post for post in posts if post.draft]
    return render_template('drafts.html',
                           drafts=drafts,
                           title='管理草稿')

@admin.route('/pages')
@login_required
def add_page():
    pages = Page.query.order_by(Page.timestamp.desc()).all()
    return render_template('pages.html',
                           pages=pages,
                           title='管理页面')

@admin.route('/posts')
@login_required
def admin_posts():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['ADMIN_POSTS_PER_PAGE'],
        error_out=False
    )
    posts = [post for post in pagination.items if post.draft == False]
    return render_template('admin_posts.html',
                           title='管理文章',
                           posts=posts,
                           pagination=pagination)


