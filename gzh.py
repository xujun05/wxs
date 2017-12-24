import requests
import json
import re
import random
import WechatDB
import time
import sys

gzh_query_lists = ['aiai', 'huxiu_com']


class gzh:
    '''公众号API'''
    header = {
        "HOST": "mp.weixin.qq.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:58.0.1) Gecko/20170101 Firefox/58.0.1"
    }

    def __init__(self):
        self.cookie, self.token = gzh.fetch_token()

    @staticmethod
    def fetch_token():
        url = 'https://mp.weixin.qq.com'
        with open('cookie.txt', 'r', encoding='utf-8') as f:
            cookie = f.read()
        cookies = json.loads(cookie)
        response = requests.get(url=url, cookies=cookies)
        return cookies, re.findall(r'token=(\d+)', str(response.url))[0]

    '依据公众号的名称查询相关的公众号id'
    def query_gzh(self, gzh_name):
        start = 0
        perpage = 5
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
                'count': perpage,
            }
            search_url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz?'
            search_response = requests.get(search_url, cookies=self.cookie, headers=self.header,
                                           params=query_params).json()
            gzh_base_ret = search_response.get('base_resp').get('ret')
            if gzh_base_ret == 0:
                gzh_lists = search_response.get('list')
                gzh_total = search_response.get('total')
                start += perpage
                for gzh_item in gzh_lists:
                    if WechatDB.DBOperation.test_is_exists(
                            "SELECT ISNULL((SELECT fakeid FROM `gzh` WHERE fakeid = '{}'))".format(gzh_item['fakeid'])):
                        print("{}已经存在".format(gzh_item['nickname']))
                    else:
                        WechatDB.DBOperation.insert_dict("gzh", gzh_item)
                # 每次处理完List，需要休眠5秒
                time.sleep(5)
                if gzh_total == 0 or start >= gzh_total:
                    print("已处理完公众号{}的查询，共计{}个结果".format(gzh_name, gzh_total))
                    break
            else:
                print("【警告】查询出现错误，休眠10秒继续尝试。错误代码为：{}".format(search_response.get('base_resp').get('err_msg')))
                time.sleep(60)

    '依据公众号ID获取该公众号的所有文章'
    def gzh_mirror_articles_by_gzh(self, fakeid):
        start = 0
        perpage = 5
        appmsg_url = 'https://mp.weixin.qq.com/cgi-bin/appmsg?'
        appmsg_id_max = WechatDB.DBOperation.get_max_appmsgid_by_fackid(fakeid)
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
                'count': perpage,
                'query': '',
                'fakeid': fakeid,
                'type': '9'
            }
            appmsg_response = requests.get(appmsg_url, cookies=self.cookie, headers=self.header,
                                           params=query_id_data).json()
            appmsg_ret = appmsg_response.get('base_resp').get('ret')
            if appmsg_ret == 0:
                appmsg_total = appmsg_response.get('app_msg_cnt')
                appmsg_list = appmsg_response.get('app_msg_list')
                start += perpage
                for item in appmsg_list:
                    if int(appmsg_id_max)>=int(item['appmsgid']) :
                        signal_stop = True
                        break
                    WechatDB.DBOperation.insert_dict("article", item, add_kvs={"fakeid":fakeid}, drop_keys = ['aid'])
                    print(item.get('link'))
                time.sleep(5)
                if appmsg_total == 0 or start >= appmsg_total or signal_stop:
                    print("已处理完公众号{}的历史文章的镜像工作，共计{}个结果".format(fakeid, appmsg_total))
                    return
            else:
                print("【警告】镜像文章出现错误，休眠10秒继续尝试。错误代码为：{}".format(appmsg_response.get('base_resp').get('err_msg')))
                time.sleep(60)


    '''获取数据库的id'''
    def init_gzh_queue(self, maxid, multi_factor=1000):
        sql = "SELECT fakeid FROM `gzh` WHERE id < {} ORDER BY id DESC LIMIT {}".format(maxid, multi_factor)
        gzh_list = WechatDB.DBOperation.excute_query(sql)
        for gzh_item in gzh_list:
            self.gzh_mirror_articles_by_gzh(gzh_item[0])


if __name__ == '__main__':
    WechatDB.DBOperation.init_pool()
    gzh = gzh()
    gzh.query_gzh('aiai')
    gzh.init_gzh_queue(sys.maxsize)
