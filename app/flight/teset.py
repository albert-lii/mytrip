# -*- coding:utf-8 -*-
"""
    :author: Albert Li
    :time: 2019/11/18 17:02 
"""
# 定位策略
from selenium.webdriver.common.by import By

# expected_conditions 类，负责条件触发
from selenium.webdriver.support import expected_conditions as EC

# WebDriverWait 库，负责循环等待
from selenium.webdriver.support.wait import WebDriverWait
from app.utils.browser import BrowserHelper

helper = BrowserHelper()
helper.create_browser()
# 必须先加载网站，selenium 才知道添加的 cookie 是属于哪个网站的，否则会报  unable to set cookie
helper.open_page('https://hotels.ctrip.com/hotel/shanghai2#ctm_ref=hod_hp_sb_lst')
WebDriverWait(helper.get_browser(), 20, 0.5).until(
        EC.presence_of_element_located((By.ID, "hotel_list"))
    )
helper.get_browser().find_element_by_id("txtCheckOut").clear()
helper.get_browser().find_element_by_id("txtCheckOut").send_keys("2019-11-25")