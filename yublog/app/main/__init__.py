from flask import Blueprint

main = Blueprint('main', __name__)
column = Blueprint('column', __name__)

from yublog.app.main import views, column_views, site
from yublog.app.models import asyncio, Admin, \
    SiteLink, Tag, Page, Post, Category, LoveMe, Shuoshuo, SideBox
from yublog.app.caches import cache_tool


async def _global_data():
    """
    所有页面共有的，比如侧栏的标签集合，社交链接，博主信息，
    和导航栏的所有分类。
    :return: global_data = {
        'admin': admin, // model object
        'social_links': socaial_links, // object list
        'friend_links': friend_links, // ...
        'tags': tags, // ...
        'categories': categories, // ...
        'pages': pages, // ...
    }
    """
    global_data = {}
    admin = await Admin.query.first()
    if admin:
        global_data['admin'] = admin

    all_links = await SiteLink.query.order_by(SiteLink.id.desc()).all()
    if all_links:
        social_links = [link for link in all_links if link.is_friend is False]
        friend_links_counts = len(all_links) - len(social_links)
        global_data['social_links'] = social_links
        global_data['friend_counts'] = friend_links_counts

    all_tags = await Tag.query.all()
    if all_tags:
        global_data['tags'] = all_tags

    all_categories = await Category.query.all()
    if all_categories:
        global_data['categories'] = all_categories

    all_pages = await Page.query.filter_by(is_show=True).all()
    if all_pages:
        global_data['pages'] = all_pages

    love_me_counts = await LoveMe.query.first()
    if love_me_counts:
        global_data['loves'] = love_me_counts.loveMe

    posts = await Post.query.filter_by(draft=False).count()
    if posts:
        global_data['postCounts'] = posts

    shuo = await Shuoshuo.query.order_by(Shuoshuo.timestamp.desc()).first()
    if shuo:
        global_data['newShuo'] = shuo.body_to_html

    guestbook = await Page.query.filter_by(url_name='guestbook').first()
    if guestbook:
        guestbook_counts = guestbook.comments.count()
        global_data['guestbookCounts'] = guestbook_counts

    all_boxes = await SideBox.query.order_by(SideBox.id.desc()).all()
    if all_boxes:
        adv_boxes = [box for box in all_boxes if box.unable is False and box.is_advertising is True]
        global_data['ads_boxes'] = adv_boxes
        my_boxes = [box for box in all_boxes if box.unable is False and box.is_advertising is False]
        global_data['my_boxes'] = my_boxes

    cache_tool.set(cache_tool.GLOBAL_KEY, global_data, timeout=60*60*24*30, unless=None)
    return global_data


@main.app_context_processor
def app_global_data():
    return asyncio.run(_global_data())


"""
add_app_template_global is the problem of legacy slowing down the program.
add_app_template_global is register a custom template global application.
app_context_processor decorator is register a custom template global dict.
"""
