#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from abc import ABC

from html.parser import HTMLParser


class XssHtml(HTMLParser, ABC):
    """xss"""
    allow_tags = ['a', 'img', 'br', 'strong', 'b', 'code', 'pre',
                  'p', 'div', 'em', 'span', 'h1', 'h2', 'h3', 'h4',
                  'h5', 'h6', 'blockquote', 'ul', 'ol', 'tr', 'th', 'td',
                  'hr', 'li', 'u', 'embed', 's', 'table', 'thead', 'tbody',
                  'caption', 'small', 'q', 'sup', 'sub']
    common_attrs = ["style", "class", "name"]
    nonend_tags = ["img", "hr", "br", "embed"]
    tags_own_attrs = {
        "img": ["src", "width", "height", "alt", "align"],
        "a": ["href", "target", "rel", "title"],
        "embed": ["src", "width", "height", "type", "allowfullscreen", "loop", "play", "wmode", "menu"],
        "table": ["border", "cellpadding", "cellspacing"],
    }

    _regex_url = re.compile(r'^(http|https|ftp)://.*', re.I | re.S)
    _regex_style_1 = re.compile(r'(\\|&#|/\*|\*/)', re.I)
    _regex_style_2 = re.compile(r'e.*x.*p.*r.*e.*s.*s.*i.*o.*n', re.I | re.S)

    def __init__(self, allows=None):
        HTMLParser.__init__(self)
        self.allow_tags = allows if allows and isinstance(allows, list) else self.allow_tags
        self.result = []
        self.start = []
        self.data = []

    def get_html(self):
        """
        Get the safe html code
        """
        for i in range(0, len(self.result)):
            self.data.append(self.result[i])
        return ''.join(self.data)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_starttag(self, tag, attrs):
        if tag not in self.allow_tags:
            return
        end_diagonal = ' /' if tag in self.nonend_tags else ''
        if not end_diagonal:
            self.start.append(tag)
        attdict = {}
        for attr in attrs:
            attdict[attr[0]] = attr[1]

        attdict = self._wash_attr(attdict, tag)
        if hasattr(self, "node_{}".format(tag)):
            attdict = getattr(self, "node_{}".format(tag))(attdict)
        else:
            attdict = self.node_default(attdict)

        attrs = []
        for (key, value) in attdict.items():
            attrs.append('{0}="{1}"'.format(key, self._htmlspecialchars(value)))
        attrs = (' {}'.format(' '.join(attrs))) if attrs else ''
        self.result.append('<{0}{1}{2}>'.format(tag, attrs, end_diagonal))

    def handle_endtag(self, tag):
        if self.start and tag == self.start[len(self.start) - 1]:
            self.result.append('</{}>'.format(tag))
            self.start.pop()

    def handle_data(self, data):
        self.result.append(self._htmlspecialchars(data))

    def handle_entityref(self, name):
        if name.isalpha():
            self.result.append("&{};".format(name))

    def handle_charref(self, name):
        if name.isdigit():
            self.result.append("&#{};".format(name))

    def node_default(self, attrs):
        attrs = self._common_attr(attrs)
        return attrs

    def node_a(self, attrs):
        attrs = self._common_attr(attrs)
        attrs = self._get_link(attrs, "href")
        attrs = self._set_attr_default(attrs, "target", "_blank")
        attrs = self._limit_attr(attrs, {
            "target": ["_blank", "_self"]
        })
        return attrs

    def node_embed(self, attrs):
        attrs = self._common_attr(attrs)
        attrs = self._get_link(attrs, "src")
        attrs = self._limit_attr(attrs, {
            "type": ["application/x-shockwave-flash"],
            "wmode": ["transparent", "window", "opaque"],
            "play": ["true", "false"],
            "loop": ["true", "false"],
            "menu": ["true", "false"],
            "allowfullscreen": ["true", "false"]
        })
        attrs["allowscriptaccess"] = "never"
        attrs["allownetworking"] = "none"
        return attrs

    def _true_url(self, url):
        if self._regex_url.match(url):
            return url
        else:
            return "http://{}".format(url)

    def _true_style(self, style):
        if style:
            style = self._regex_style_1.sub('_', style)
            style = self._regex_style_2.sub('_', style)
        return style

    def _get_style(self, attrs):
        if "style" in attrs:
            attrs["style"] = self._true_style(attrs.get("style"))
        return attrs

    def _get_link(self, attrs, name):
        if name in attrs:
            attrs[name] = self._true_url(attrs[name])
        return attrs

    def _wash_attr(self, attrs, tag):
        if tag in self.tags_own_attrs:
            other = self.tags_own_attrs.get(tag)
        else:
            other = []

        _attrs = {}
        if attrs:
            for (key, value) in attrs.items():
                if key in self.common_attrs + other:
                    _attrs[key] = value
        return _attrs

    def _common_attr(self, attrs):
        attrs = self._get_style(attrs)
        return attrs

    def _set_attr_default(self, attrs, name, default=''):
        if name not in attrs:
            attrs[name] = default
        return attrs

    def _limit_attr(self, attrs, limit={}):
        for (key, value) in limit.items():
            if key in attrs and attrs[key] not in value:
                del attrs[key]
        return attrs

    def _htmlspecialchars(self, html):
        return html.replace("<", "&lt;")\
            .replace(">", "&gt;")\
            .replace('"', "&quot;")\
            .replace("'", "&#039;")


parser = XssHtml()

if __name__ == '__main__':
    parser = XssHtml()
    parser.feed("""
    <pre>
        <script>alert('xss');</script>
    </pre>
    <script>alert('xss');</script>
    """)
    parser.close()
    print(parser.get_html())
