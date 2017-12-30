from spider.gzh import gzh
import util.tools as tools
import db.dbhelper as dbhelper
import sys
import logging
from util.LogHandler import LogHandler

sys.path.append('./')
logging.basicConfig()
main_logger = LogHandler('main')
ua_cookie_tuple = tools.get_ua_cookie_list()

if __name__ == '__main__':
    spider = gzh(ua_cookie_tuple[0][0], ua_cookie_tuple[0][1])
    spider.query_gzh("股票")
    # spider.gzh_mirror_articles_by_gzh("MjM5NDgxNjkyMA==")