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

def save_file(sitemap):
    path = os.getcwd().replace('\\', '/')
    filename = path + '/static/sitemap.xml'
    isExists = os.path.exists(filename)
    if not isExists:
        with open(filename, 'w') as f:
            f.write(sitemap)
    else:
        os.remove(filename)
        with open(filename, 'w') as f:
            f.write(sitemap)

def send_mail(from_addr, password, to_addr, smtp_server, mail_port, msg):
    content = MIMEText(msg, 'plain', 'utf-8')
    server = smtplib.SMTP(smtp_server, mail_port)
    server.starttls()
    server.login(from_addr, password)
    server.sendmail(from_addr, [to_addr], content.as_string())
    server.quit()

