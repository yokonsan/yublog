from flask import abort

from yublog.models import Post
from yublog.caches import cache_tool


class PostCacheUtils(object):

    def get_post_cache(self, key):
        """获取博客文章缓存"""
        data = cache_tool.get(key)
        return data if data else self.set_post_cache(key)

    def set_post_cache(self, key):
        """设置博客文章缓存"""
        _, year, month, url = key.split('_')
        time = str(year) + '-' + str(month)
        posts = Post.query.filter_by(url_name=url).all()
        if len(posts) > 1:
            _post = [p for p in posts if time in p.timestamp][0]
        elif len(posts) == 1:
            _post = posts[0]
        else:
            abort(404)

        tags = _post.tags.split(',')
        data = _post.to_dict()
        data['tags'] = tags
        data['next_post'] = self._next_post(_post)
        data['prev_post'] = self._prev_post(_post)

        cache_key = '_'.join(map(str, ['post', year, month, url]))
        cache_tool.set(cache_key, data, timeout=60 * 60 * 24 * 30)
        return data
    
    def update_first_cache():
        """在新文章更新后，清掉最近一篇文章的缓存"""
        posts = Post.query.order_by(Post.timestamp.desc()).all()
        if len(posts) > 1:
            first_post = posts[1]
            cache_key = '_'.join(map(str, ['post', first_post.year, first_post.month, first_post.url_name]))
            cache_tool.clean(cache_key)
        return True

    @staticmethod
    def _next_post(_post):
        """
        获取本篇文章的下一篇
        :param _post: post
        :return: next post
        """
        post_list = Post.query.order_by(Post.timestamp.desc()).all()
        posts = [p for p in post_list if p.draft is False]
        if posts[-1] != _post:
            _next = posts[posts.index(_post) + 1]
            return {
                'year': _next.year,
                'month': _next.month,
                'url': _next.url_name,
                'title': _next.title
            }
        return None

    @staticmethod
    def _prev_post(_post):
        """
        获取本篇文章的上一篇
        :param post: post
        :return: prev post
        """
        post_list = Post.query.order_by(Post.timestamp.desc()).all()
        posts = [p for p in post_list if p.draft is False]
        if posts[0] != _post:
            _prev = posts[posts.index(_post) - 1]
            return {
                'year': _prev.year,
                'month': _prev.month,
                'url': _prev.url_name,
                'title': _prev.title
            }
        return None
