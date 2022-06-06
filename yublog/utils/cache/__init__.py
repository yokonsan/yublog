from yublog import cache
from yublog.exceptions import NoCacheTypeException


class GlobalCacheKey:
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


class Operate:
    PREFIX = "yublog"
    TYPES = set()

    def _join_key(self, typ, key):
        """拼接缓存key"""
        assert typ in self.TYPES, \
            NoCacheTypeException(f"type must in {self.TYPES}")

        return f"{self.PREFIX}:{typ}:{key}"

    def get(self, typ, key):
        """查询"""
        return cache.get(self._join_key(typ, key))

    def set(self, typ, key, value, **kwargs):
        """设置"""
        return cache.set(self._join_key(typ, key), value, **kwargs)

    def clean(self, typ, key=None):
        """删除"""
        if key:
            return cache.delete(self._join_key(typ, key))

        return cache.clear()

    def incr(self, typ, key, delta=1):
        """数字类型自增"""
        cache.inc(self._join_key(typ, key), delta)

    def decr(self, typ, key, delta=1):
        """数字类型自减"""
        cache.dec(self._join_key(typ, key), delta)

    def add(self, typ, key, item):
        """保留当前数据，增加缓存数据"""
        key = self._join_key(typ, key)
        current = cache.get(key)
        if isinstance(current, list):
            current.append(item)
        elif isinstance(current, dict):
            current.update(item)

        return cache.set(key, current)


class CacheOperate(Operate):
    ALL_KEY = 'all'
    GLOBAL_KEY = 'global'
    ADD = '+'
    REMOVE = '-'
    TYPES = {"global", "post", "article", "column", "page"}

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


cache_operate = CacheOperate()
