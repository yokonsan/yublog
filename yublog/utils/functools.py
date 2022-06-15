from yublog.utils.validators import valid_page_num


def get_pagination(counts, per, cur_page):
    max_page = counts // per + 1 if not counts or counts % per else counts // per
    cur_page = valid_page_num(cur_page, max_page)

    return max_page, cur_page
