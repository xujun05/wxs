from spider.gzh import gzh
import util.tools as tools
import sys
import logging
from util.LogHandler import LogHandler
import util.config as config
from multiprocessing import Process
from multi_thread.multi_thread import WorkManager

sys.path.append('./')
logging.basicConfig()
main_logger = LogHandler('main')
ua_cookie_tuple = tools.get_ua_cookie_list()
thread_dict = config.get_dict_by_section("wx.conf", "thread")


def get_gzh_func(worker_no, gzh_query, proxy=''):
    """
    获取每个用户的帖子
    :param worker_no: 线程编号
    :param gzh_query: 需要查询的公众号
    :param proxy:
    :return:
    """
    gzh_crawler = gzh(ua_cookie_tuple[worker_no][0], ua_cookie_tuple[worker_no][1])
    gzh_crawler.query_gzh(gzh_query)


def gzh_spider():
    string = 'abcdefghijklmnopqrstuvwxyz0123456789'
    query_list = list(string)
    query_list.extend(["股票", "stock", "证券", "量化"])
    wm = WorkManager(int(thread_dict['num']))
    for index, query in enumerate(query_list):
        wm.add_job(index, get_gzh_func, index % int(thread_dict['num']), query)
    wm.start()
    wm.wait_for_complete()


def get_article_func(worker_no, fakeid, proxy=''):
    """
    获取每个用户的帖子
    :param worker_no: 线程编号
    :param article_query: 用户编号
    :param proxy:
    :return:
    """
    article_crawler = gzh(ua_cookie_tuple[worker_no][0], ua_cookie_tuple[worker_no][1])
    article_crawler.gzh_mirror_articles_by_gzh(fakeid)


def article_spider():
    base_n = 100
    for i in range (0, base_n):
        fakeid_list = tools.get_all_fakeid(i, base_n)
        wm = WorkManager(int(thread_dict['num']))
        for index, fakeid in enumerate(fakeid_list):
            wm.add_job(index, get_article_func, index % int(thread_dict['num']), fakeid[0])
        wm.start()
        wm.wait_for_complete()
        main_logger.info("article progress {}/{}".format(i, base_n))


def run():
    p_list = list()
    p1 = Process(target=gzh_spider, name='gzh')
    p_list.append(p1)
    p2 = Process(target=article_spider, name='article')
    p_list.append(p2)

    for p in p_list:
        p.daemon = True
        p.start()
    for p in p_list:
        p.join()

if __name__ == '__main__':
    #spider = gzh(ua_cookie_tuple[0][0], ua_cookie_tuple[0][1])
    #spider.query_gzh("股票")
    # spider.gzh_mirror_articles_by_gzh("MjM5NDgxNjkyMA==")
    run()
