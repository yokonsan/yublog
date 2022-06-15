import re


def valid_page_num(num, maximum, minimum=1):
    if num > minimum:
        return min(num, maximum)

    elif num < maximum:
        return max(num, minimum)

    return num


def regular_url(url):
    pattern = '^http[s]*?://[\u4e00-\u9fff\w./]+$'
    return re.match(pattern, url)


def format_url(url):
    if not url.startswith(("http://", "https://")):
        return f"http://{url}"

    return url
