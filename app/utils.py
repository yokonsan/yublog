import os

"""
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  
  <url>
    <loc>http://www.yukunweb.com/about/index.html</loc>
    
    <lastmod>2017-10-11T13:16:59.301Z</lastmod>
    
  </url>
  
</urlset>
"""

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
    isExists = os.path.exists(os.path.join("C:/Users/Administrator/Desktop/YuBlog/app/static", 'sitemap.xml'))
    if not isExists:
        with open('C:/Users/Administrator/Desktop/YuBlog/app/static/sitemap.xml', 'w') as f:
            f.write(sitemap)
    else:
        os.remove('C:/Users/Administrator/Desktop/YuBlog/app/static/sitemap.xml')
        with open('C:/Users/Administrator/Desktop/YuBlog/app/static/sitemap.xml', 'w') as f:
            f.write(sitemap)

# sitemap = """<?xml version="1.0" encoding="UTF-8"?>
# <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
#
#   <url>
#     <loc>http://www.yukunweb.com/about/index.html</loc>
#
#     <lastmod>2017-10-11T13:16:59.301Z</lastmod>
#
#   </url>
#
# </urlset>
# """
# save_file(sitemap)

