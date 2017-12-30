from selenium import webdriver
import time
import json
from pprint import pprint
from fake_useragent import UserAgent
from selenium.webdriver.chrome.options import Options
from util import config as config
import sys

##
## 366561968@qq.com wangfusheng1988
ua = UserAgent(verify_ssl=False)
sys.path.append('./')


class wx_login:
    def __init__(self):
        pass

    @staticmethod
    def get_ua_random():
        return ua.random

    @staticmethod
    def get_random_ua_firefox(ua):
        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", ua)
        driver = webdriver.Firefox(profile, executable_path="D:\\WebDriver\\geckodriver.exe")
        return driver

    @staticmethod
    def get_random_ua_chrome(ua):
        opts = Options()
        opts.add_argument(ua)
        driver = webdriver.Chrome(chrome_options=opts, executable_path="D:\\WebDriver\\chromedriver.exe")
        return driver, ua

    @staticmethod
    def get_user_cookies(user, pwd):
        post = {}
        ua = wx_login.get_ua_random()
        driver = wx_login.get_random_ua_firefox(ua)
        driver.get('https://mp.weixin.qq.com/')
        driver.find_element_by_xpath("//input[@name='account']").clear()
        driver.find_element_by_xpath("//input[@name='account']").send_keys(user)
        driver.find_element_by_xpath("//input[@name='password']").clear()
        driver.find_element_by_xpath("//input[@name='password']").send_keys(pwd)
        # 在自动输完密码之后记得点一下记住我
        driver.find_element_by_xpath("//a[@class='btn_login']").click()
        # 拿手机扫二维码！
        time.sleep(15)
        driver.get('https://mp.weixin.qq.com/')
        cookie_items = driver.get_cookies()
        for cookie_item in cookie_items:
            post[cookie_item['name']] = cookie_item['value']
        cookie_str = json.dumps(post)
        with open('cookie.txt', 'w+', encoding='utf-8') as f:
            f.write(cookie_str)
        driver.quit()


if __name__ == '__main__':
    wx_config = config.get_dict_by_section("wx.conf", "wechat")
    user_list = str(wx_config['user']).split(",")
    pwd = wx_config['pwd']
    for user in user_list:
        wx_login.get_user_cookies(user=user.strip(' '), pwd=pwd)
