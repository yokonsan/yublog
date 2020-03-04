#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import smtplib
from threading import Thread
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

from markdown import Markdown


# 拼接站点地图
def get_sitemap(posts):
    if not posts:
        return None

    header = """
    <?xml version="1.0" encoding="UTF-8"?> 
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    """
    footer, body = '</urlset>', ''

    for post in posts:
        content = """
            <url>
                <loc>http://www.yukunweb.com/{post.timestampInt}/{post.url_name}/</loc>
                <lastmod>{post.timestamp}</lastmod>
            </url>
        """.format(post=post)
        body += '\n{0}'.format(content)
    sitemap = '\n'.join([header, body, footer])
    return sitemap


# 保存xml文件到静态文件目录
def save_file(sitemap, file):
    path = os.getcwd().replace('\\', '/')
    filename = path + '/app/static/' + file
    is_exists = os.path.exists(filename)
    if not is_exists:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(sitemap)
            return True
    os.remove(filename)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(sitemap)
        return True


# 发送邮件
def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


def send_mail(from_addr, password, to_addr, smtp_server, mail_port, msg):
    content = MIMEText(msg, 'html', 'utf-8')
    content['Subject'] = Header('博客评论……', 'utf-8').encode()
    server = smtplib.SMTP_SSL(smtp_server, mail_port)
    server.login(from_addr, password)
    server.sendmail(from_addr, [to_addr], content.as_string())
    server.quit()


def asyncio_send(from_addr, password, to_addr, smtp_server, mail_port, msg):
    t = Thread(target=send_mail,
               args=(from_addr, password, to_addr, smtp_server, mail_port, msg))
    t.start()
    return t


# 生成 rss xml
def get_rss_xml(name, protocol, url, title, subtitle, _time, update_time, posts):
    if not posts:
        return None

    header = """
    <?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>{title}</title>
            <subtitle>{subtitle}</subtitle>
            <link rel="alternate" type="text/html" href="{protocol}://{url}/"/>
            <link href="{protocol}://{url}/atom.xml" rel="self"/>
            <id>tag:{url},{time}://1</id>
            <updated>{update_time}T00:00:00Z</updated>
            <generator uri="https://github.com/Blackyukun/YuBlog">YuBlog</generator>
    """.format(title=title, subtitle=subtitle,
               protocol=protocol, url=url, time=_time, update_time=update_time)
    body, footer = '', '</feed>'

    for p in posts:
        item = """
            <entry>
                <title>{p.title}</title>
                <link rel="alternate" type="text/html" href="{protocol}://{url}/{p.year}/{p.month}/{p.url_name}"/>
                <id>tag:{url},{p.year}://1.{p.id}</id>
                <published>{p.timestamp}T00:00:00Z</published>
                <updated>{update_time}T00:00:00Z</updated>
                <summary>{p.title}</summary>
                <author>
                <name>{name}</name>
                <uri>{protocol}://{url}</uri>
                </author>
                <category term="{p.category.category}" scheme="{protocol}://{url}/category/{p.category.category}"/>
                <content type="html"><![CDATA[{p.body_to_html}]]></content>
            </entry>
        """.format(p=p, url=url, name=name, protocol=protocol, update_time=update_time)
        body += '{0}\n'.format(item)
    rss_xml = '\n'.join([header, body, footer])
    return rss_xml


# 解析markdown
def markdown_to_html(body):
    md = Markdown(extensions=[
        'fenced_code',
        'codehilite(css_class=highlight,linenums=None)',
        'admonition', 'tables', 'extra'])
    content = md.convert(body)
    return content

