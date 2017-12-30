import requests
import json
import re
import random
import time
import sys
import db.dbhelper as dbhelper
import logging
from util.LogHandler import LogHandler

requests.packages.urllib3.disable_warnings()

gzh_logger = LogHandler('gzh')
article_logger = LogHandler('article')
logging.basicConfig()


class gzh():
    '''公众号API'''

    def __init__(self, _ua, _cookie):
        self.ua = _ua
        self.cookie = json.loads(_cookie)
        self.token = gzh.fetch_token(self.ua, self.cookie)
        self.nap_limit_time = 10
        self.freq_limit_time = 600

    @staticmethod
    def fetch_token(ua, cookie):
        """
        获取本用户的标志token
        :param ua:模拟的UserAgent
        :param cookie:登录的Cookie
        :return:
        """
        header = {
            'Host': 'mp.weixin.qq.com',
            'User-Agent': ua,
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': "https://mp.weixin.qq.com/cgi-bin/home?t=home/index&token=&lang=zh_CN",
        }
        url = 'https://mp.weixin.qq.com'
        response = requests.get(url=url, headers=header, cookies=cookie)
        return re.findall(r'token=(\d+)', str(response.url))[0]

    def query_gzh(self, gzh_name):
        """
        依据公众号的名称查询相关的公众号id

        :param gzh_name:需要查询的公众号名称
        :return:本次查询所有的gzh list并写入数据库
        """
        header = {
            'Host': 'mp.weixin.qq.com',
            'User-Agent': self.ua,
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=10&token=" + self.token + "&lang=zh_CN",
        }
        start = 0
        per_page = 10
        while True:
            query_params = {
                'action': 'search_biz',
                'token': self.token,
                'lang': 'zh_CN',
                'f': 'json',
                'ajax': '1',
                'random': random.random(),
                'query': gzh_name,
                'begin': start,
                'count': per_page,
            }
            search_url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz?'
            search_response = requests.get(search_url, cookies=self.cookie, headers=header,
                                           params=query_params).json()
            gzh_base_ret = search_response.get('base_resp').get('ret')
            if gzh_base_ret == 0:
                gzh_lists = search_response.get('list')
                gzh_total = search_response.get('total')
                start += per_page
                for gzh_item in gzh_lists:
                    if dbhelper.test_is_exists(
                            "SELECT ISNULL((SELECT fakeid FROM `gzh` WHERE fakeid = '{}'))".format(gzh_item['fakeid'])):
                        gzh_logger.info("{}已经存在".format(gzh_item['nickname']))
                    else:
                        dbhelper.insert_dict("gzh", gzh_item)
                # 每次处理完List，需要休眠5秒
                time.sleep(self.nap_limit_time)
                if gzh_total == 0 or start >= gzh_total:
                    gzh_logger.info("已处理完公众号{}的查询，共计{}个结果".format(gzh_name, gzh_total))
                    break
            else:
                gzh_logger.warning("【警告】查询出现错误，休眠{}秒继续尝试。错误代码为：{}".format(self.freq_limit_time,
                                                                          search_response.get('base_resp').get(
                                                                              'err_msg')))
                time.sleep(self.freq_limit_time)

    def gzh_mirror_articles_by_gzh(self, fakeid):
        """
        依据公众号ID获取该公众号的所有文章
        :param fakeid:公众号的ID
        :return:
        """
        header = {
            'Host': 'mp.weixin.qq.com',
            'User-Agent': self.ua,
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=10&token=" + self.token + "&lang=zh_CN",
        }
        start = 0
        per_page = 5
        appmsg_url = 'https://mp.weixin.qq.com/cgi-bin/appmsg?'
        appmsg_id_max = dbhelper.get_max_appmsgid_by_fakeid(fakeid)
        signal_stop = False
        while True:
            query_id_data = {
                'token': self.token,
                'lang': 'zh_CN',
                'f': 'json',
                'ajax': '1',
                'random': random.random(),
                'action': 'list_ex',
                'begin': start,
                'count': per_page,
                'query': '',
                'fakeid': fakeid,
                'type': '9'
            }
            appmsg_response = requests.get(appmsg_url, cookies=self.cookie, headers=header,
                                           params=query_id_data).json()
            appmsg_ret = appmsg_response.get('base_resp').get('ret')
            if appmsg_ret == 0:
                appmsg_total = appmsg_response.get('app_msg_cnt')
                appmsg_list = appmsg_response.get('app_msg_list')
                start += per_page
                for item in appmsg_list:
                    if int(appmsg_id_max) >= int(item['appmsgid']):
                        signal_stop = True
                        break
                    dbhelper.insert_dict("article", item, add_kvs={"fakeid": fakeid}, drop_keys=['aid'])
                    article_logger.info(item.get('appmsgid'))
                if appmsg_total == 0 or start >= appmsg_total or signal_stop:
                    article_logger.info("已处理完公众号{}的历史文章的镜像工作，共计{}个结果".format(fakeid, appmsg_total))
                    return
                time.sleep(self.nap_limit_time)
            else:
                article_logger.warning("【警告】镜像文章出现错误，休眠{}秒继续尝试。错误代码为：{}".format(self.freq_limit_time,
                                                                                appmsg_response.get('base_resp').get(
                                                                                    'err_msg')))
                time.sleep(self.freq_limit_time)
                self.freq_limit_time = self.freq_limit_time * 2

    def init_gzh_queue(self, maxid, multi_factor=1000):
        """
        依据处理的最大的ID与每次的步进来获取公众号的列表
        :param maxid:
        :param multi_factor:
        :return:
        """
        sql = "SELECT fakeid FROM `gzh` WHERE id < {} ORDER BY id DESC LIMIT {}".format(maxid, multi_factor)
        gzh_list = dbhelper.execute_query(sql)
        for gzh_item in gzh_list:
            self.gzh_mirror_articles_by_gzh(gzh_item[0])


if __name__ == '__main__':
    # gzh = gzh()
    # gzh.query_gzh('aiai')
    # gzh.init_gzh_queue(sys.maxsize)
    pass
