#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import smtplib
from threading import Thread
from email.header import Header
from email.mime.text import MIMEText

from markdown import Markdown
from flask import current_app


def get_sitemap(posts):
    """拼接站点地图"""
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


async def save_file(sitemap, file):
    """保存xml文件到静态文件目录"""
    path = os.getcwd().replace('\\', '/')
    filename = path + '/app/static/' + file
    is_exists = os.path.exists(filename)
    if is_exists: os.remove(filename)

    async with open(filename, 'w', encoding='utf-8') as f:
        await f.write(sitemap)
        return True


def send_mail(to_addr, msg):
    mail_username = current_app.config['MAIL_USERNAME']
    mail_password = current_app.config['MAIL_PASSWORD']
    mail_server = current_app.config['MAIL_SERVER']
    mail_port = current_app.config['MAIL_PORT']
    
    content = MIMEText(msg, 'html', 'utf-8')
    content['Subject'] = Header('博客评论……', 'utf-8').encode()
    server = smtplib.SMTP_SSL(mail_server, mail_port)
    server.login(mail_username, mail_password)
    server.sendmail(mail_username, [to_addr], content.as_string())
    server.quit()


def asyncio_send(to_addr, msg):
    """异步发送邮件"""
    t = Thread(target=send_mail, args=(to_addr, msg))
    t.start()
    return t


def gen_rss_xml(update_time, posts):
    """生成 rss xml"""
    if not posts:
        return None

    # 配置参数
    name = current_app.config['ADMIN_NAME']
    title = current_app.config['SITE_NAME']
    subtitle = current_app.config['SITE_TITLE']
    protocol = current_app.config['WEB_PROTOCOL']
    url = current_app.config['WEB_URL']
    web_time = current_app.config['WEB_START_TIME']
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
               protocol=protocol, url=url, time=web_time, update_time=update_time)
    body, footer = '', '</feed>'
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
    """
    for p in posts:
        body += '{0}\n'.format(item.format(p=p, url=url, name=name, protocol=protocol, update_time=update_time))
    rss_xml = '\n'.join([header, body, footer])
    return rss_xml


async def markdown_to_html(body):
    """解析markdown"""
    md = Markdown(extensions=[
        'fenced_code',
        'codehilite(css_class=highlight,linenums=None)',
        'admonition', 'tables', 'extra'])
    content = await md.convert(body)

    return content
