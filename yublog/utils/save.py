from flask import current_app

from yublog.extensions import db
from yublog.models import Tag, Category, Post
from yublog.utils.cache import cache_operate, CacheType, GlobalCacheKey
from yublog.utils.tools import get_sitemap, save_file, gen_rss_xml


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
    :param form: 表单类
    :param draft: 是否保存草稿
    :return: post object
    """
    category = save_category(form.category.data, is_show=not draft)

    tags = form.tags.data.split(',')
    post = Post(body=form.body.data, title=form.title.data,
                url_name=form.url_name.data, category=category,
                tags=form.tags.data, create_time=form.time.data, draft=draft)
    if not draft:
        # 保存标签模型
        save_tags(tags)
        # 更新xml
        save_xml(post.create_time)

    return post


def save_category(old_category, new_category=None, is_show=True):
    # 是否需要删除旧的分类
    if new_category:
        category = Category.query.filter_by(category=old_category).first()
        if category.posts.count() == 1:
            db.session.delete(category)
            db.session.commit()
            # 更新分类缓存
            cache_operate.clean(CacheType.GLOBAL.name, GlobalCacheKey.CATEGORIES)
        old_category = new_category

    # 是否新的分类需要添加
    category = Category.query.filter_by(category=old_category).first()
    if not category:
        category = Category(category=old_category, is_show=is_show)
        db.session.add(category)
        db.session.commit()
    return category


# 编辑文章后更新sitemap
def save_xml(update_time):
    sitemap_xml = 'sitemap.xml'
    atom_xml = 'atom.xml'
    # 获取配置信息
    count = current_app.config['RSS_COUNTS']

    posts = Post.query.filter_by(draft=False).order_by(Post.create_time.desc()).all()
    # sitemap
    sitemap = get_sitemap(posts)
    save_file(sitemap, sitemap_xml)
    # rss
    rss_posts = posts[:count]
    rss = gen_rss_xml(update_time, rss_posts)
    save_file(rss, atom_xml)
