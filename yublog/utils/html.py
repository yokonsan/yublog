import os

from flask import current_app, url_for
from markdown import Markdown


def md2html(body):
    """解析markdown"""
    if not body:
        return ''

    md = Markdown(extensions=[
        'fenced_code',
        'codehilite(css_class=highlight,linenums=None)',
        'admonition',
        'tables',
        'extra'
    ])
    content = md.convert(body)

    return content


def get_sitemap(posts):
    """拼接站点地图"""
    if not posts:
        return None

    header = """<?xml version="1.0" encoding="UTF-8"?> 
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    """
    footer, body = "</urlset>", ""
    for post in posts:
        content = f"""
            <url>
                <loc>{url_for('main.post', year=post.year, month=post.month, post_url=post.url_name)}/</loc>
                <lastmod>{post.create_time}</lastmod>
            </url>
        """
        body += f"\n{content}"

    return "\n".join([header, body, footer])


def save_file(sitemap, file):
    """保存xml文件到静态文件目录"""
    filename = os.path.join(os.getcwd(), "yublog", "static", file)
    if os.path.exists(filename):
        os.remove(filename)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(sitemap)
        return True


def gen_rss_xml(update_time, posts):
    """生成 rss xml"""
    if not posts:
        return None

    # 配置参数
    name = current_app.config["ADMIN_NAME"]
    title = current_app.config["SITE_NAME"]
    subtitle = current_app.config["SITE_TITLE"]
    protocol = current_app.config["WEB_PROTOCOL"]
    url = current_app.config["WEB_URL"]
    web_time = current_app.config["WEB_START_TIME"]
    header = f"""<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>{title}</title>
            <subtitle>{subtitle}</subtitle>
            <link rel="alternate" type="text/html" href="{protocol}://{url}/"/>
            <link href="{protocol}://{url}/atom.xml" rel="self"/>
            <id>tag:{url},{web_time}://1</id>
            <updated>{update_time}T00:00:00Z</updated>
            <generator uri="https://github.com/Blackyukun/YuBlog">YuBlog</generator>
    """
    body, footer = "", "</feed>"
    for p in posts:
        body += f"""
            <entry>
                <title>{p.title}</title>
                <link rel="alternate" type="text/html" href="{protocol}://{url}/{p.year}/{p.month}/{p.url_name}"/>
                <id>tag:{url},{p.year}://1.{p.id}</id>
                <published>{p.create_time}T00:00:00Z</published>
                <updated>{update_time}T00:00:00Z</updated>
                <summary>{p.title}</summary>
                <author>
                <name>{name}</name>
                <uri>{protocol}://{url}</uri>
                </author>
                <category term="{p.category.category}" scheme="{protocol}://{url}/category/{p.category.category}"/>
                <content type="html"><![CDATA[{p.body_to_html}]]></content>
            </entry>\n
        """

    return "\n".join([header, body, footer])

