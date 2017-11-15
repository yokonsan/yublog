from flask import Blueprint

main = Blueprint('main', __name__)

from . import views
from ..models import *

@main.app_context_processor
def global_data():
    """
    所有页面共有的，比如侧栏的标签集合，社交链接，博主信息，
    和导航栏的所有分类。
    :return: 
    """
    global_data = {}
    admin = Admin.query.get(1)
    if admin:
        admin_name = admin.name
        profile = admin.profile
        global_data.admin_name = admin_name
        global_data.profile = profile

    all_links = SocialLink.query.order_by(SocialLink.link).all()
    if all_links:
        social_links = [link for link in all_links.link if link.isFriendLink == False]
        friend_links = [link for link in all_links.link if link.isFriendLink == True]
        global_data.social_links = social_links
        global_data.friend_links = friend_links

    all_tags = Tag.query.order_by(Tag.datetime.desc()).all()
    if all_tags:
        tags = [tag for tag in all_tags.tag]
        global_data.tags = tags

    all_categories = Category.query.order_by(Category.datetime.desc()).all()
    if all_categories:
        categories = [category for category in all_categories.category]
        global_data.categories = categories

    return global_data
