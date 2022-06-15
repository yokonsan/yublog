from flask import render_template, current_app, url_for

from yublog import db, cache_operate, CacheType, CacheKey
from yublog.models import Comment, Post, Page, Article
from yublog.utils.as_sync import sync_request_context
from yublog.utils.emails import send_mail
from yublog.utils.validators import regular_url, format_url


class CommentUtils(object):
    COMMENT_TARGET_TYPE = {
        "post": Post,
        "page": Page,
        "article": Article
    }

    def __init__(self, target_type, form):
        self._target_type = target_type
        self._data = self.comment_data(form)

    @staticmethod
    def comment_data(form):
        return {
            "nickname": form["nickname"],
            "email": form["email"],
            "website": form.get("website", None),
            "body": form["comment"],
            "reply_to": form.get("replyTo", ""),
            "reply_author": form.get("replyName", "")
        }

    def _generate_comment(self):
        website = format_url(self._data["website"])
        nickname = self._data["nickname"]
        body = self._data["body"]
        email = self._data["email"]
        comment = Comment(comment=body, author=nickname, email=email, website=website)
        if self._data["reply_to"]:
            reply_author = self._data["reply_author"]
            if website and regular_url(website):
                nickname_p_tag = "<a class='comment-user' href='{website}' target='_blank'>{nickname}</a>".format(
                    website=website, nickname=nickname)
                comment_html = "<p class='reply-header'>{nickname_p_tag}<span>回复</span> {reply_author}：</p>\n\n" \
                               "{body}".format(website=website, nickname_p_tag=nickname_p_tag,
                                               reply_author=reply_author, body=body)
            else:
                comment_html = "<p class='reply-header'>{nickname}<span>回复</span>  {reply_author}：" \
                               "</p>\n\n{body}".format(nickname=nickname, reply_author=reply_author, body=body)

            comment = Comment(comment=comment_html, author=nickname, email=email, website=website)
            comment.comment = comment_html
            comment.replied_id = int(self._data["reply_to"])
            self._data["body"] = comment_html

        return comment

    def save_comment(self, target_id):
        if self._target_type not in self.COMMENT_TARGET_TYPE:
            current_app.logger.warning("评论保存失败：未获取到目标类型")
            return None

        target = self.COMMENT_TARGET_TYPE.get(self._target_type).query.get_or_404(target_id)
        url = self._get_comment_post(target)
        if not url:
            current_app.logger.warning("评论保存失败：未获取到目标url")
            return self._data

        # 生成评论
        comment = self._generate_comment()
        setattr(comment, self._target_type, target)

        # 发送邮件
        # self._send_mail(target.title, url)
        db.session.add(comment)
        db.session.commit()
        return self._data

    @staticmethod
    def _get_comment_post(target):
        if isinstance(target, Post):
            return url_for("main.post", year=target.year, month=target.month, post_url=target.url_name)

        if isinstance(target, Page):
            return url_for("main.page", page_url=target.url_name)

        if isinstance(target, Article):
            return url_for("column.article", url_name=target.column.url_name, id=target.id)

        return None

    def _send_mail(self, title, url):
        to_mail_address = current_app.config.get("ADMIN_MAIL", "")
        if self._data["email"] != to_mail_address:
            msg = render_template("admin_mail.html", nickname=self._data["nickname"],
                                  title=title, comment=self._data["body"],
                                  email=self._data["email"], website=self._data["website"], url=url)
            send_mail(to_mail_address, msg)


def get_comment_url(comment):
    base_url = current_app.config["WEB_URL"]
    url = ""
    if post := comment.post:
        path = [base_url, post.year, post.month, post.url_name]
        url = f"https://{'/'.join(str(i) for i in path)}"
    elif page := comment.page:
        url = f"https://{base_url}/page/{page.url_name}"
    elif article := comment.article:
        url = f"https://{base_url}/column/{article.column.url_name}/{article.id}"

    return url


def update_comment_cache(comment, is_incr=True):
    if page := comment.page:
        cache_operate.clean(CacheType.PAGE, page.url_name)
        cache_operate.clean(CacheType.COMMENT, f"page:{page.id}")
        if page.url_name == "guest-book":
            (cache_operate.incr if is_incr else cache_operate.decr)(
                CacheType.GLOBAL, CacheKey.GUEST_BOOK_COUNT
            )

    elif (post := comment.post) and isinstance(post, Post):
        cache_operate.clean(
            CacheType.POST, f"{post.year}_{post.month}_{post.url_name}"
        )
        cache_operate.clean(CacheType.COMMENT, f"post:{post.id}")


def commit_comment(typ, form, tid):
    @sync_request_context
    def _commit_comment():
        CommentUtils(typ, form).save_comment(tid)

    return _commit_comment()
