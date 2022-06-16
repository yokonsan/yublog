from flask import current_app

from yublog.extensions import db
from yublog.models import Tag, Category, Post
from yublog.utils.as_sync import sync_request_context
from yublog.utils.html import get_sitemap, save_file, gen_rss_xml


def save_tags(tags):
    @sync_request_context
    def _save_tags():
        for tag in tags:
            exist_tag = Tag.query.filter_by(tag=tag).first()
            if not exist_tag:
                tag = Tag(tag=tag)
                db.session.add(tag)
        db.session.commit()

    return _save_tags()


def save_post(form, is_draft=False):
    category = save_category(form.category.data, is_show=not is_draft)

    tags = form.tags.data.split(",")
    post = Post(body=form.body.data, title=form.title.data,
                url_name=form.url_name.data, category=category,
                tags=form.tags.data, create_time=form.create_time.data, draft=is_draft)
    if not is_draft:
        save_tags(tags)
        save_xml(post.create_time)

    return post


def save_category(old_category, new_category=None, is_show=True):
    if new_category:
        category = Category.query.filter_by(category=old_category).first()
        if category.posts.count() == 1:
            # new one replace old one
            db.session.delete(category)
            db.session.commit()

        old_category = new_category

    category = Category.query.filter_by(category=old_category).first()
    if not category:
        # add new category
        category = Category(category=old_category, is_show=is_show)
        db.session.add(category)
        db.session.commit()
    return category


def save_xml(update_time):
    @sync_request_context
    def _save_xml():
        posts = Post.query.filter_by(draft=False).order_by(Post.create_time.desc()).all()
        # sitemap
        sitemap = get_sitemap(posts)
        save_file(sitemap, "sitemap.xml")
        # rss
        rss_posts = posts[:current_app.config["RSS_COUNTS"]]
        rss = gen_rss_xml(update_time, rss_posts)
        save_file(rss, "atom.xml")

    return _save_xml()
