from enum import Enum

from yublog import cache
from yublog.exceptions import NoCacheTypeException


class GlobalCacheKey:
    GLOBAL = "global"
    ADMIN = "admin"
    TAGS = "tags"
    CATEGORIES = "categories"
    PAGES = "pages"
    LOVE_COUNT = "love_count"
    POST_COUNT = "post_count"
    TALK = "talk"
    GUEST_BOOK_COUNT = "guest_book_count"
    SOCIAL_LINKS = "social_links"
    FRIEND_COUNT = "friend_count"
    ADS_BOXES = "ads_boxes"
    SITE_BOXES = "site_boxes"


class Operate:
    PREFIX = "_cache"
    TYPES = set()

    def _join_key(self, typ, key):
        """拼接缓存key"""
        assert typ in self.TYPES, \
            NoCacheTypeException(f"type must in {self.TYPES}, current type[{typ}]")

        return f"{self.PREFIX}:{typ}:{key}".lower()

    def get(self, typ, key):
        """查询"""
        return cache.get(self._join_key(typ, key))

    def set(self, typ, key, value, **kwargs):
        """设置"""
        return cache.set(self._join_key(typ, key), value, **kwargs)

    def clean(self, typ=None, key="*"):
        """删除"""
        if typ:
            return cache.delete(self._join_key(typ, key))

        return cache.clear()

    def incr(self, typ, key, delta=1):
        """数字类型自增"""
        cache.cache.inc(self._join_key(typ, key), delta)

    def decr(self, typ, key, delta=1):
        """数字类型自减"""
        cache.cache.dec(self._join_key(typ, key), delta)

    def add(self, typ, key, item):
        """保留当前数据，增加缓存数据"""
        key = self._join_key(typ, key)
        current = cache.get(key)
        if isinstance(current, list):
            current.append(item)
        elif isinstance(current, dict):
            current.update(item)

        return cache.set(key, current)

    def get_many(self, typ, *keys):
        keys = [self._join_key(typ, key) for key in keys]
        return cache.get_many(*keys)


class CacheType(Enum):
    GLOBAL = "global"
    POST = "post"
    ARTICLE = "article"
    COLUMN = "column"
    PAGE = "page"


class CacheOperate(Operate):
    TYPES = CacheType.__members__.keys()


cache_operate = CacheOperate()
