from re import A
from flask import render_template, current_app, url_for

from yublog import db
from yublog.models import Comment, Post, Page, Article
from yublog.utils.tools import asyncio_send, regular_url


class CommentUtils(object):
    COMMENT_TARGET_TYPE = {
        'post': Post,
        'page': Page,
        'article': Article
    }

    def __init__(self, target_type, form):
        self._target_type = target_type
        self._data = self.comment_data(form)
    
    @staticmethod
    def comment_data(form):
        return {
            'nickname': form['nickname'],
            'email': form['email'],
            'website': form.get('website', None),
            'body': form['comment'],
            'reply_to': form.get('replyTo', ''),
            'reply_author': form.get('replyName', '')
        }

    def _generate_comment(self):
        website = self._data['website']
        nickname = self._data['nickname']
        body = self._data['body']
        email = self._data['email']
        comment = Comment(comment=body, author=nickname, email=email, website=website)
        if self._data['reply_to']:
            reply_author = self._data['reply_author']
            if website and regular_url(website):
                nickname_p_tag = '<a class="comment-user" href="{website}" target="_blank">{nickname}</a>'.format(
                        website=website, nickname=nickname)
                comment_html = '<p class="reply-header">{nickname_p_tag}<span>回复</span> {reply_author}：</p>\n\n' \
                            '{body}'.format(website=website, nickname_p_tag=nickname_p_tag,
                                            reply_author=reply_author, body=body)
            else:
                comment_html = '<p class="reply-header">{nickname}<span>回复</span>  {reply_author}：' \
                        '</p>\n\n{body}'.format(nickname=nickname, reply_author=reply_author, body=body)

            comment = Comment(comment=comment_html, author=nickname, email=email, website=website)
            comment.comment = comment_html
            comment.replied_id = int(self._data['reply_to'])
            self._data['body'] = comment_html
        
        return comment
            

    def save_comment(self, target_id):
        if self._target_type not in self.COMMENT_TARGET_TYPE:
            current_app.logger.warning('评论保存失败：未获取到目标类型')
            return None

        target = self.COMMENT_TARGET_TYPE.get(self._target_type).query.get_or_404(target_id)
        
        url = self._get_comment_post(target)
        if not url:
            current_app.logger.warning('评论保存失败：未获取到目标url')
            return self._data

        # 生成评论
        comment = self._generate_comment()
        setattr(comment, self._target_type, target)

        # 发送邮件
        self._send_mail(target.title, url)
        db.session.add(comment)
        db.session.commit()
        return self._data

    @staticmethod
    def _get_comment_post(target):
        if isinstance(target, Post):
            return url_for('main.post', year=target.year, month=target.month, post_url=target.url_name)
        
        if isinstance(target, Page):
            return url_for('main.page', page_url=target.url_name)
        
        if isinstance(target, Article):
            return url_for('column.article', url=target.column.url_name, id=target.id)

        return None
    
    def _send_mail(self, title, url):
        to_mail_address = current_app.config.get('ADMIN_MAIL', '')
        if self._data['email'] != to_mail_address:
            msg = render_template('admin_mail.html', nickname=self._data['nickname'],
                                title=title, comment=self._data['body'],
                                email=self._data['email'], website=self._data['website'], url=url)
            asyncio_send(to_mail_address, msg)
