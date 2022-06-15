from flask import current_app

from yublog import cache
from yublog.exceptions import NoCacheTypeException
from yublog.utils.as_sync import as_sync
from yublog.utils.log import log_time


class CacheKey:
    GLOBAL = "global"
    ADMIN = "admin"
    TAGS = "tags"
    CATEGORIES = "categories"
    PAGES = "pages"
    LOVE_COUNT = "love_count"
    POST_COUNT = "post_count"
    LAST_TALK = "last_talk"
    GUEST_BOOK_COUNT = "guest_book_count"
    SOCIAL_LINKS = "social_links"
    FRIEND_COUNT = "friend_count"
    FRIEND_LINKS = "friend_links"
    ADS_BOXES = "ads_boxes"
    SITE_BOXES = "site_boxes"
    POSTS = "posts"
    COLUMNS = "columns"
    TALKS = "talks"
    IMAGE_PATH = "paths"
    IMAGES = "images"
    ARTICLES = "articles"


class CacheType:
    GLOBAL = "global"
    POST = "post"
    ARTICLE = "article"
    COLUMN = "column"
    PAGE = "page"
    COMMENT = "comment"
    TALK = "talk"
    LINK = "link"
    IMAGE = "image"


class Operate:
    PREFIX = "_cache"
    TYPES = set()

    def join_key(self, typ, key):
        """拼接缓存key"""
        assert typ in self.TYPES, \
            NoCacheTypeException(f"type must in {self.TYPES}, current type[{typ}]")

        return f"{self.PREFIX}:{typ}:{key}".lower()

    def get(self, typ, key):
        """查询"""
        return cache.get(self.join_key(typ, key))

    def set(self, typ, key, value, timeout=60*60*24*30, **kwargs):
        """设置"""
        return cache.set(self.join_key(typ, key), value, timeout=timeout, **kwargs)

    def clean(self, typ=None, key="*"):
        """删除"""
        if typ:
            if key != "*":
                return cache.delete(self.join_key(typ, key))
            # 模糊取所有key

            plugin_prefix = current_app.config["CACHE_KEY_PREFIX"]
            keys = cache.cache._read_clients.keys(  # noqa
                plugin_prefix + self.join_key(typ, key)
            )
            return cache.delete_many(*[k.decode().lstrip(plugin_prefix) for k in keys])

        return cache.clear()

    def incr(self, typ, key, delta=1):
        """数字类型自增"""
        cache.cache.inc(self.join_key(typ, key), delta)

    def decr(self, typ, key, delta=1):
        """数字类型自减"""
        cache.cache.dec(self.join_key(typ, key), delta)

    def add(self, typ, key, item):
        """保留当前数据，增加缓存数据"""
        key = self.join_key(typ, key)
        current = cache.get(key)
        if isinstance(current, list):
            current.append(item)
        elif isinstance(current, dict):
            current.update(item)

        return cache.set(key, current)

    def get_many(self, typ, *keys):
        keys = [self.join_key(typ, key) for key in keys]
        return cache.get_many(*keys)


class CacheOperate(Operate):
    TYPES = [attr.lower() for attr in dir(CacheType) if not attr.startswith("__")]

    @log_time
    def getset(self, typ, key, callback=None, **kwargs):
        """缓存存在则返回，不存在则设置并返回"""
        val = self.get(typ, key)
        if not val and callable(callback):
            val = callback()
            if val:
                self.set(typ, key, val, **kwargs)

        return val


cache_operate = CacheOperate()
