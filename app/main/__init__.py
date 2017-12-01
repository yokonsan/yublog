from flask import Blueprint

main = Blueprint('main', __name__)

from . import views
from ..models import *

@main.app_context_processor
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
    admin = Admin.query.get(1)
    if admin:
        global_data['admin'] = admin

    all_links = SocialLink.query.order_by(SocialLink.link).all()
    if all_links:
        social_links = [link for link in all_links if link.isFriendLink == False]
        friend_links = [link for link in all_links if link.isFriendLink == True]
        global_data['social_links'] = social_links
        global_data['friend_links'] = friend_links

    all_tags = Tag.query.all()
    if all_tags:
        tags = [tag for tag in all_tags]
        global_data['tags'] = tags

    all_categories = Category.query.all()
    if all_categories:
        categories = [category for category in all_categories]
        global_data['categories'] = categories

    all_pages = Page.query.all()
    if all_pages:
        pages = [page for page in all_pages if page.isNav==True]
        global_data['pages'] = pages

    return global_data

main.add_app_template_global(global_datas, 'global_datas')
