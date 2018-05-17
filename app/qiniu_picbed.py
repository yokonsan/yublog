import os
import re
from datetime import datetime

import qiniu


class QiniuUpload(object):
    """
    集成七牛云存储操作
    """

    def __init__(self, app=None):
        self.app = app
        self.img_suffix = ['jpg', 'jpeg', 'png', 'gif']
        if app: self.init_app(app)

    def init_qiniu(self):
        self.qiniuer = qiniu.Auth(self.app.config.get('QN_ACCESS_KEY', ''),
                                  self.app.config.get('QN_SECRET_KEY', ''))
        self.bucket_manager = qiniu.BucketManager(self.qiniuer)
        self.bucket = self.app.config.get('QN_PIC_BUCKET', '')
        self.domain = self.app.config.get('QN_PIC_DOMAIN', '')

    def init_app(self, app):
        """
        从应用程序设置初始化设置。
    ：param app：Flask app
        """
        self.app = app
        self.init_qiniu()

    def _get_publish_time(self, timestamp):
        if timestamp:
            t = float(timestamp/10000000)
            return datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M')
        return None

    def _get_file_size(self, size):
        if size:
            return float('%.2f' % (size / 1024))
        return 0

    def get_token(self):
        return self.qiniuer.upload_token(self.bucket)

    def parse_img_name(self, file, filename=None):
        """
        解析出合法文件名
        :param file: 文件路径
        :param filename: 文件名
        :return: 文件名
        """
        suffix = os.path.splitext(os.path.basename(file))[1]
        if suffix not in self.img_suffix: return False
        if filename:
            filename = re.sub(r'[\/\\\:\*\?"<>|]', r'_', filename)
            if filename.find('.') == -1:
                filename += suffix
        else:
            filename = os.path.basename(file)
        return filename

    def upload_qn(self, filename, data):
        """
        :param filename: 文件所在路径，如有data则为图片名
        :param data: 图片二进制流

        :return: True or False
        """
        filename, data = filename, data
        token = self.get_token()
        key = filename
        try:
            ret, info = qiniu.put_data(token, key, data)
            return True if info.status_code == 200 else False
        except:
            return False

    def get_img_link(self, filename):
        return self.domain + '/' + filename

    def del_file(self, key):
        ret, info = self.bucket_manager.delete(self.bucket, key)

        return True if ret == {} else False

    def rename_file(self, key, key_to):
        ret, info = self.bucket_manager.rename(self.bucket, key, key_to)

        return True if ret == {} else False

    def upload_status(self, key):
        ret, info = self.bucket_manager.stat(self.bucket, key)

        return True if info.status_code == 200 else False

    def get_all_images(self):
        """
        :return: [{'name':'图片名', 'url': '图片url'}, {}]
        """
        images = []
        # 前缀
        prefix = None
        # 列举条目
        limit = None
        # 列举出除'/'的所有文件以及以'/'为分隔的所有前缀
        delimiter = None
        # 标记
        marker = None
        ret, eof, info = self.bucket_manager.list(self.bucket, prefix, marker, limit, delimiter)
        if ret.get('items', []):
            for i in ret.get('items'):
                if i.get('mimeType', '').startswith('image'):
                    images.append({
                        'name': i.get('key', ''),
                        'url': self.domain + i.get('key', ''),
                        'time': self._get_publish_time(i.get('putTime', '')),
                        'size': self._get_file_size(i.get('fsize', 0))
                    })
        return images
