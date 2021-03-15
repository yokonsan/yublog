# coding: utf-8

from yublog import cache


class CacheScheme(object):
    SCHEME = {
        'posts': [],
        'pages': [],
        'columns': [],
        'articles': []
    }


class GlobalCacheKey(object):
    ADMIN = 'admin'
    TAGS = 'tags'
    CATEGORIES = 'categories'
    PAGES = 'pages'
    LOVE_COUNT = 'love_count'
    POST_COUNT = 'post_count'
    TALK = 'talk'
    GUEST_BOOK_COUNT = 'guest_book_count'
    SOCIAL_LINKS = 'social_links'
    FRIEND_COUNT = 'friend_count'
    ADS_BOXES = 'ads_boxes'
    MY_BOXES = 'my_boxes'


class CacheTools(object):
    ALL_KEY = 'all'
    GLOBAL_KEY = 'global'
    ADD = '+'
    REMOVE = '-'

    @staticmethod
    def get(key):
        return cache.get(key)

    @staticmethod
    def set(key, value, **kwargs):
        cache.set(key, value, **kwargs)

    def clean(self, key):
        """
        在发布文章后删除首页，归档，分类，标签缓存，
        在更新文章后删除对应文章缓存
        在添加说说，更改友链页后删除对应缓存
        :param key: cache key
        """
        if key == self.ALL_KEY:
            cache.clear()
        elif cache.get(key):
            cache.delete(key)
        else:
            return False

    def update_global(self, key, value, method=None):
        """
        update sidebar global cache
        : param key: dict key
        : param kwargs: key, value, method
        """
        global_cache = cache.get(self.GLOBAL_KEY)
        if global_cache is None:
            return False
        if method == self.ADD:
            value = value if isinstance(value, int) else 1
            global_cache[key] += value
        elif method == self.REMOVE:
            value = value if isinstance(value, int) else 1
            global_cache[key] -= value
        else:
            global_cache[key] = value
        cache.set(self.GLOBAL_KEY, global_cache)

        return True


global_cache_key = GlobalCacheKey()
cache_tool = CacheTools()
