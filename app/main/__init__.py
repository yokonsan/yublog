from flask import Blueprint

main = Blueprint('main', __name__)
column = Blueprint('column', __name__)

from . import views, site, column_views
from ..models import *
from .. import cache

@main.app_context_processor
@cache.cached(timeout=60*60*24*30, key_prefix='global', unless=None)
def global_datas():
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
    admin = Admin.query.all()
    if admin:
        global_data['admin'] = admin[0]

    all_links = SiteLink.query.order_by(SiteLink.id.desc()).all()
    if all_links:
        social_links = [link for link in all_links if link.isFriendLink == False]
        friend_links_counts = len([link for link in all_links if link.isFriendLink == True])
        global_data['social_links'] = social_links
        global_data['friendCounts'] = friend_links_counts

    all_tags = Tag.query.all()
    if all_tags:
        # tags = [tag for tag in all_tags]
        global_data['tags'] = all_tags

    all_categories = Category.query.all()
    if all_categories:
        #categories = [category for category in all_categories]
        global_data['categories'] = all_categories

    all_pages = Page.query.filter_by(isNav=True).all()
    if all_pages:
        #pages = (page for page in all_pages if page.isNav==True)
        global_data['pages'] = all_pages

    love_me_counts = LoveMe.query.all()[0]
    if love_me_counts:
        global_data['loves'] = love_me_counts.loveMe

    posts = Post.query.filter_by(draft=False).count()
    if posts:
        #post_counts = len([post for post in posts if post.draft==False])
        global_data['postCounts'] = posts

    shuos = Shuoshuo.query.order_by(Shuoshuo.timestamp.desc()).all()
    if shuos:
        global_data['newShuo'] = shuos[0].body_to_html

    guestbook = Page.query.filter_by(url_name='guestbook').first()
    if guestbook:
        guestbook_counts = guestbook.comments.count()
        global_data['guestbookCounts'] = guestbook_counts

    all_boxes = SideBox.query.order_by(SideBox.id.desc()).all()
    if all_boxes:
        adv_boxes = [box for box in all_boxes if box.unable is False and box.is_advertising is True]
        global_data['ads_boxes'] = adv_boxes
        my_boxes = [box for box in all_boxes if box.unable is False and box.is_advertising is False]
        global_data['my_boxes'] = my_boxes

    return global_data


main.add_app_template_global(global_datas, 'global_datas')
