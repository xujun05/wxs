import requests
import util.config as config
import json
import os
import uuid
import db.dbhelper as dbhelper

proxy_dict = config.get_dict_by_section("wx.conf", "proxy")


def getExchange(code):
    first = code[:1]
    return 'SZ' if first in ['0', '1', '2', '3'] else 'SH'


def symbold_id(full_code):
    exchange_code = full_code[:2]
    if exchange_code == "SH":
        return int("10" + full_code[2:])
    elif exchange_code == "SZ":
        return int("11" + full_code[2:])
    else:
        return int("12" + full_code[2:])


def get_proxy():
    return str(requests.get("http://{}:{}/get/".format(proxy_dict['ip'], proxy_dict['port'])).content, encoding="utf-8")


def delete_proxy(proxy):
    requests.get("http://{}:{}/delete/?proxy={}".format(proxy_dict['ip'], proxy_dict['port'], proxy))


def get_all_proxy():
    return json.loads(requests.get("http://{}:{}/get_all/".format(proxy_dict['ip'], proxy_dict['port'])).content)


def get_proxy_count():
    return json.loads(requests.get("http://{}:{}/get_status/".format(proxy_dict['ip'], proxy_dict['port'])).content)


def random_string(n):
    return (''.join(map(lambda xx: (hex(ord(xx))[2:]), os.urandom(n))))[0:16]


def get_uuid():
    return str(uuid.uuid4()).replace('-', '')


def get_ua_cookie_list():
    return dbhelper.execute_query("SELECT ua, cookie FROM wechat_cookie WHERE ua !=''")


def get_all_thread_list_base_n(m, base_n):
    """
    获取除以n之后的余数的thread_id
    :param m:余数
    :param base_n:基数
    :return:
    """
    return dbhelper.execute_query(
        "SELECT DISTINCT thread_id FROM `{}` WHERE thread_id % {} = {}".format("xueqiu_rs_stockcode_threads", base_n, m))


def get_all_user_list_base_n(m, base_n):
    """
    获取除以n之后的余数的thread_id
    :param m:余数
    :param base_n:基数
    :return:
    """
    return dbhelper.execute_query(
        "SELECT id FROM `{}` WHERE id % {} = {}".format("xueqiu_user", base_n, m))


if __name__ == '__main__':
    # print(get_ua_cookie_list())
    # print(get_proxy())
    # proxy_list = get_all_proxy()
    # proxy_count = get_proxy_count()
    # print(proxy_count)
    # print(random_string(16))
    print(get_uuid())
