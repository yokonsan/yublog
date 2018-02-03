#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import smtplib
from email.mime.text import MIMEText

def get_sitemap(posts):
    header = '<?xml version="1.0" encoding="UTF-8"?> '+ '\n' + \
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    footer = '</urlset>'
    contents = []
    body = ''
    if posts:
        for post in posts:
            content = '  <url>' + '\n' + \
                '    <loc>http://www.yukunweb.com/' + str(post.timestampInt) + '/' + post.url_name + '/' + '</loc>' + '\n' + \
                '    <lastmod>' + post.timestamp + '</lastmod>' + '\n' + \
                '  </url>'
            contents.append(content)
        for content in contents:
            body = body + '\n' + content
        sitemap = header + '\n' + body + '\n' + footer
        return sitemap
    return None

def save_file(sitemap, file):
    path = os.getcwd().replace('\\', '/')
    filename = path + '/app/static/' + file
    isExists = os.path.exists(filename)
    if not isExists:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(sitemap)
    else:
        os.remove(filename)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(sitemap)

def send_mail(from_addr, password, to_addr, smtp_server, mail_port, msg):
    content = MIMEText(msg, 'plain', 'utf-8')
    server = smtplib.SMTP(smtp_server, mail_port)
    server.starttls()
    server.login(from_addr, password)
    server.sendmail(from_addr, [to_addr], content.as_string())
    server.quit()

def get_rss_xml(name, protocol, url, title, subtitle, time, update_time, posts):
    header = '<?xml version="1.0" encoding="UTF-8"?>' + '\n' + \
    '<feed xmlns="http://www.w3.org/2005/Atom">' + '\n' + \
      '  <title>' + title + '</title>' + '\n' + \
      '  <subtitle>' + subtitle + '</subtitle>' + '\n' + \
      '  <link rel="alternate" type="text/html" href="' + protocol + '://' + url + '/"/>' + '\n' + \
      '  <link href="' + protocol + '://' + url + '/atom.xml" rel="self"/>' + '\n' + \
      '  <id>tag:' + url + ',' + time + '://1</id>' + '\n' + \
      '  <updated>' + update_time + 'T00:00:00Z</updated>' + '\n' + \
      '  <generator uri="https://github.com/Blackyukun/YuBlog">YuBlog</generator>'
    content = []
    item = ''
    footer = '</feed>'
    if posts:
        for p in posts:
            body = '  <entry>' + '\n' + \
              '    <title>' + str(p.title) + '</title>' + '\n' + \
              '    <link rel="alternate" type="text/html" href="' + protocol + '://' + url + '/' + str(p.year) + '/' + str(p.month) + '/' + str(p.url_name) + '"/>' + '\n' + \
              '    <id>tag:' + url + ',' + str(p.year) + '://1.' + str(p.id) + '</id>' + '\n' + \
              '    <published>' + str(p.timestamp) + 'T00:00:00Z</published>' + '\n' + \
              '    <updated>' + update_time + 'T00:00:00Z</updated>' + '\n' + \
              '    <summary>' + str(p.title) + '</summary>' + '\n' + \
              '    <author>' + '\n' + \
              '    <name>' + name + '</name>' + '\n' + \
              '    <uri>' + protocol + '://' + url + '</uri>' + '\n' + \
              '    </author>' + '\n' + \
              '    <category term="' + str(p.category.category) + '" scheme="' + protocol + '://' + url + '/category/' + str(p.category.category) + '"/>' + '\n' + \
              '    <content type="html"><![CDATA[' + str(p.body_to_html) + ']]></content>' + '\n' + \
            '  </entry>'
            content.append(body)
        for c in content:
            item = item + '\n' + c
        rss_xml = header + '\n' + item + '\n' + footer
        return rss_xml
    return None


