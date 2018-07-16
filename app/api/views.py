from flask import jsonify, current_app, request, g
from flask_login import login_required

from . import api
from ..models import *


"""
api 路由：
    get_posts(): 返回所有博客文章
    get_post(id, url): 返回指定 id 的文章
    get_pages(): 返回所有页面
    get_page(id): 返回指定页面
    get_tags(): 返回所有博客标签
    get_tag_posts(tag): 返回指定标签的文章
    get_categories(): 返回所有博客分类
    get_category_posts(cate): 返回指定分类的文章
    get_shuos(): 返回所有说说
"""


@api.route('/posts')
def get_posts():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False)
    posts = [post for post in pagination.items if post.draft is False]
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_posts', page=page - 1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_posts', page=page + 1, _external=True)

    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/post/<int:id>')
def get_post(id):
    post = Post.query.filter_by(id=id).first()
    if post:
        return jsonify({
            'post': post.to_json(),
            'body': post.body,
            'html': post.body_to_html
        })

    return jsonify({'msg': '没有信息...'})


# post请求
@api.route('/post', methods=['POST'])
@login_required
def new_post():
    post = Post.from_json(request.json)
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json()), 201, {'Location': url_for('api.get_post', id=post.id, _external=True)}


# put请求
@api.route('/posts/<int:id>', methods=['PUT'])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)

    post.title = request.json.get('title', post.title)
    post.body = request.json.get('body', post.body)
    db.session.add(post)
    return jsonify(post.to_json())


@api.route('/pages')
def get_pages():
    pages = Page.query.order_by(Page.id.desc()).all()

    return jsonify({
        'pages': [page.to_json() for page in pages],
        'count': len(pages)
    })


@api.route('/page/<int:id>')
def get_page(id):
    page = Page.query.get_or_404(id)
    if page:
        return jsonify({
            'page': page.to_json(),
            'body': page.body,
            'html': page.body_to_html
        })

    return jsonify({'msg': '没有信息...'})


@api.route('/tags')
def get_tags():
    tags = Tag.query.all()

    return jsonify({
        'tags': [tag.to_json() for tag in tags],
        'count': len(tags)
    })


@api.route('/tag/<tag>')
def get_tag_posts(tag):
    tag = Tag.query.filter_by(tag=tag).first()
    if tag:
        posts = [p for p in Post.query.filter_by(draft=False).all() if p.tag_in_post(tag.tag)]
        return jsonify({
            'posts': [post.to_json() for post in posts],
            'count': len(posts)
        })

    return jsonify({'msg': '没有信息...'})


@api.route('/categories')
def get_categories():
    categories = Category.query.all()

    return jsonify({
        'categories': [category.to_json() for category in categories],
        'count': len(categories)
    })


@api.route('/category/<category>')
def get_category_posts(category):
    category = Category.query.filter_by(category=category).first()
    if category:
        posts = Post.query.filter_by(category=category).all()
        return jsonify({
            'posts': [post.to_json() for post in posts],
            'count': len(posts)
        })

    return jsonify({'msg': '没有信息...'})


@api.route('/shuos')
def get_shuos():
    shuos = Shuoshuo.query.order_by(Shuoshuo.timestamp.desc()).all()

    return jsonify({
        'shuoshuo': [shuo.to_json() for shuo in shuos],
        'count': len(shuos)
    })


@api.route('/comments/post/<int:id>')
def get_post_comments(id):
    post = Post.query.filter_by(id=id).first()
    if post:
        comments = Comment.query.filter_by(post=post).all()
        return jsonify({'comments': [comment.to_json() for comment in comments]})

    return jsonify({'msg': '没有信息...'})


@api.route('/comments/page/<int:id>')
def get_page_comments(id):
    page = Page.query.get_or_404(id)
    if page:
        comments = Comment.query.filter_by(page=page).all()
        return jsonify({'comments': [comment.to_json() for comment in comments]})

    return jsonify({'msg': '没有信息...'})

# post views
@api.route('/view/<type>/<int:id>', methods=['GET'])
def views(type, id):
    """浏览量"""
    view = View.query.filter_by(type=type, relationship_id=id).first()
    if not view:
        view = View(type=type, count=1, relationship_id=id)
        db.session.add(view)
        db.session.commit()
        resp = jsonify(count=1)
        resp.set_cookie('post_' + str(id), '1', max_age=1 * 24 * 60 * 60)
        return resp

    if type == 'post':
        if not request.cookies.get('post_' + str(id)):
            view.count += 1
            db.session.add(view)
            db.session.commit()
            resp = jsonify(count=view.count)
            resp.set_cookie('post_' + str(id), '1', max_age=1 * 24 * 60 * 60)
            return resp
        return jsonify(count=view.count)
    elif type == 'column':
        if not request.cookies.get('article_' + str(id)):
            view.count += 1
            db.session.add(view)
            db.session.commit()
            resp = jsonify(count=view.count)
            resp.set_cookie('article_' + str(id), '1', max_age=1 * 24 * 60 * 60)
            return resp
        return jsonify(count=view.count)
