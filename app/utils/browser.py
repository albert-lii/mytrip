# -*- coding:utf-8 -*-
"""
    selenium 驱动 chromedriver 封装
    :author: Albert Li
    :time: 2019/11/13 15:45
"""

import time
import platform

from selenium import webdriver
from loguru import logger


class BrowserHelper(object):
    def __init__(self):
        self._browser = None

    def create_browser(self, proxy=None):
        """创建一个浏览器对象"""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--no-sandbox")  # 解决DevToolsActivePort文件不存在报错问题
        chrome_options.add_argument(
            "--disable-gpu"
        )  # 禁用GPU硬件加速。如果软件渲染器没有就位，则GPU进程将不会启动
        chrome_options.add_argument("blink-settings=imagesEnabled=false")  # 禁用加载图片
        chrome_options.add_argument("--ignore-certificate-errors")  # 忽略证书错误
        if proxy is not None:
            chrome_options.add_argument("--proxy-server=http://%s" % proxy)  # 设置代理
        # 使用 selenium 创建浏览器窗口
        if platform.system() == "Windows":
            # Windows 环境
            # chrome_options.add_argument("--headless")  # 设置 chrome 浏览器为无界面模式
            executable_path = r"C:\Users\albertlii\AppData\Local\Google\Chrome\Application\chromedriver.exe"
            self._browser = webdriver.Chrome(
                options=chrome_options, executable_path=executable_path
            )
        else:
            # Linux 环境
            # executable_path = r'/usr/local/bin/chromedriver',
            chrome_options.add_argument("--headless")  # 设置 chrome 浏览器为无界面模式
            self._browser = webdriver.Chrome(options=chrome_options)

    def open_page(self, url):
        """打开网页
        :param url: 目标网页地址
        """
        try:
            # 超时会抛出异常，这里 try 一下
            self._browser.get(url)
        except Exception:
            logger.error("open page failed")

    def get_browser(self):
        """获取浏览器对象
        :return: 浏览器对象
        """
        return self._browser

    def get_scroll_top(self):
        """获取滚动条距离页面顶部的高度
        :return: 滚动条距离页面顶部的高度
        """
        js_get_scroll_height = "return action=document.body.scrollHeight;"
        return self._browser.execute_script(js_get_scroll_height)

    def scroll_to_footer(self):
        """滚动到页面最底部"""
        # 滚动到当前页面的底部的js
        js_scroll_to_bottom = "window.scrollTo(0, document.body.scrollHeight);"
        # 先获取当前的页面高度
        scroll_top = self.get_scroll_top()
        # 是否到达页面最底部的检查次数
        is_at_footer_check_count = 1
        # 判断是否已经到达底部
        is_at_footer = True
        while is_at_footer:
            # 执行滚动到页面底部的js
            self._browser.execute_script(js_scroll_to_bottom)
            time.sleep(0.25)
            # 获取滚动后的页面的高度（滚动后，页面可能会加载，高度会增加）
            new_scroll_top = self.get_scroll_top()
            # 判断滚动过后的高度和之前的高度是否一致
            if new_scroll_top > scroll_top:
                scroll_top = new_scroll_top
            else:
                # 当检查次数大于0时，继续检查，防止页面还没有完全滚动到最底部，直至执行完所有的检查次数
                if is_at_footer_check_count <= 0:
                    is_at_footer = False
                is_at_footer_check_count -= 1

    def scroll_to_view(self, view):
        """滚动动到指定的 view 的位置
        :param view: 指定的 view
        """
        self._browser.execute_script("arguments[0].scrollIntoView()", view)

    def click_view_by_js(self, view):
        """通过 js 执行点击事件直接用 selenium 模拟用户单击元素时，有时会报错 btn_book is not clickable at point (879, 858)
        因为有些元素在鼠标悬浮在上面的时候会对元素进行修改，比如按钮出现蒙层才可点击
        :param view: 要点击的 view
        """
        self._browser.execute_script("arguments[0].click();", view)

    def close(self):
        """关闭当前网页"""
        self._browser.close()

    def close_all(self):
        """关闭所有的网页，退出浏览器"""
        self._browser.quit()
