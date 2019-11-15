# -*- coding:utf-8 -*-
"""
    :author: Albert Li
    :time: 2019/11/12 15:51 
"""
import json

# 定位策略
from selenium.webdriver.common.by import By

# expected_conditions 类，负责条件触发
from selenium.webdriver.support import expected_conditions as EC

# WebDriverWait 库，负责循环等待
from selenium.webdriver.support.wait import WebDriverWait

from lxml import html

from app.db.redis_helper import RedisClient
from app.utils.browser import BrowserHelper

etree = html.etree

redis_client = RedisClient()


def _save_cookies(value):
    """保存携程登录后的 cookie 信息"""
    redis_client.set_data_with_expire("ctrip-cookies", value, 2592000)


def _get_cookies():
    """获取携程登录后的 cookie 信息"""
    return redis_client.get_data("ctrip-cookies")


def _load_cookies(helper: BrowserHelper):
    """加载 cookies"""
    # 一旦加载网站，即使没登录，也会产生一个 cookie，所以先删除这个 cookie
    helper.get_browser().delete_all_cookies()
    cookies = _get_cookies()
    if cookies is not None:
        for item in json.loads(cookies):
            # https://www.cnblogs.com/CYHISTW/p/11685846.html invalid 'expiry' 的解決方案
            if isinstance(item.get("expiry"), float):
                item["expiry"] = int(item["expiry"])
            helper.get_browser().add_cookie(cookie_dict=item)
            # 刷新页面后，cookie 才会生效
        helper.get_browser().refresh()


def _open_inter_flight_page(
    trip_type: int, dep_city: str, arr_city: str, date: str, cabin: str
) -> BrowserHelper:
    """访问携程国际航班页面
    :param trip_type: 1: 单程  2: 往返-单程
    :param dep_city: 出发城市
    :param arr_city: 到达城市
    :param date: 出发日期
    :param cabin: 舱型
    :return BrowserHelper
    """
    if trip_type == 1:
        # 国际单程航班页面 url
        url = (
            "https://flights.ctrip.com/international/search/oneway-"
            "{dep_city}-{arr_city}?depdate={date}&cabin={cabin}&adult=1&child=0&infant=0".format(
                dep_city=dep_city.lower(),
                arr_city=arr_city.lower(),
                date=date,
                cabin=cabin.lower(),
            )
        )
    elif trip_type == 2:
        # 国际往返航班页面 url
        url = (
            "https://flights.ctrip.com/international/search/round-"
            "{dep_city}-{arr_city}?depdate={date}&cabin={cabin}&adult=1&child=0&infant=0&directflight=".format(
                dep_city=dep_city.lower(),
                arr_city=arr_city.lower(),
                date=date,
                cabin=cabin.lower(),
            )
        )
    helper = BrowserHelper()
    helper.create_browser("127.0.0.1:8889")
    # 必须先加载网站，selenium 才知道添加的 cookie 是属于哪个网站的，否则会报  unable to set cookie
    helper.open_page(url)
    return helper


def _open_inter_round_back_flight_page(
    dep_city: str, arr_city: str, date: str, cabin: str, go_flight: dict
) -> BrowserHelper:
    """访问国际往返行航班的返程航班页面
    :param dep_city: 出发城市
    :param arr_city: 到达城市
    :param date: 出发日期
    :param cabin: 舱型
    :param go_flight: 去程航班信息
    :return BrowserHelper
    """
    helper = _open_inter_flight_page(2, dep_city, arr_city, date, cabin)
    # 页面循环等待，每隔 0.5s 检查一次航空公司内容是否加载出来，当航空公司加载出来时停止等待，最多等待 20s
    WebDriverWait(helper.get_browser(), 20, 0.5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "flight-list"))
    )
    helper.scroll_to_footer()
    flight_els = helper.get_browser().find_elements_by_css_selector("div.flight-item")
    for el in flight_els:
        airline = el.find_element_by_css_selector("div.airline-name").text
        dep_time = (
            el.find_element_by_css_selector("div.depart-box")
            .find_element_by_css_selector("div.time")
            .text
        )
        arr_time = (
            el.find_element_by_css_selector("div.arrive-box")
            .find_element_by_css_selector("div.time")
            .text
        )
        if all(
            [
                go_flight.get("airline") in airline,
                go_flight.get("dep_time") in dep_time,
                go_flight.get("arr_time") in arr_time,
            ]
        ):
            # 点击去程航班订票按钮，开始请求返程航班
            helper.scroll_to_view(el)
            btn_book = el.find_element_by_css_selector("div.btn.btn-book")
            if btn_book is None:
                helper.click_view_by_js(el)
            else:
                helper.click_view_by_js(btn_book)
            return helper
    # 没有在页面中找到对应的去程，所以直接关闭浏览器，并返回 None
    helper.close_all()
    return None


def _open_flight_order_page(
    trip_type: int,
    dep_city: str,
    arr_city: str,
    date: str,
    cabin: str,
    go_flight: dict,
    back_flight: dict,
) -> BrowserHelper:
    """访问填写乘机人订单页面，页面出现，关闭浏览器
    :param trip_type: 1: 单程  2: 往返
    :param dep_city: 出发城市
    :param arr_city: 到达城市
    :param date: 出发日期
    :param cabin: 舱型
    :param go_flight: 去程航班信息
    :param back_flight: 返程航班信息
    :return BrowserHelper
    """
    helper = _open_inter_flight_page(
        1 if trip_type == 1 else 2, dep_city, arr_city, date, cabin
    )
    # 页面循环等待，每隔 0.5s 检查一次航空公司内容是否加载出来，当航空公司加载出来时停止等待，最多等待 20s
    WebDriverWait(helper.get_browser(), 20, 0.5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "flight-list"))
    )
    helper.scroll_to_footer()
    go_flight_els = helper.get_browser().find_elements_by_css_selector(
        "div.flight-item"
    )
    for go_el in go_flight_els:
        go_airline = (
            go_el.find_element_by_css_selector("div.airline-name")
            .find_element_by_tag_name("span")
            .text
        )
        go_dep_time = (
            go_el.find_element_by_css_selector("div.depart-box")
            .find_element_by_css_selector("div.time")
            .text
        )
        go_arr_time = (
            go_el.find_element_by_css_selector("div.arrive-box")
            .find_element_by_css_selector("div.time")
            .text
        )
        if all(
            [
                go_flight.get("airline") in go_airline,
                go_flight.get("dep_time") in go_dep_time,
                go_flight.get("arr_time") in go_arr_time,
            ]
        ):
            helper.scroll_to_view(go_el)
            if trip_type == 1:
                go_seats = go_el.find_elements_by_css_selector(
                    "div.seat-row.seat-row-v3"
                )
                # 点击对应价格的产品
                btn_book = go_seats[go_flight["index"]].find_element_by_css_selector(
                    "div.btn.btn-book"
                )
                if btn_book is None:
                    helper.click_view_by_js(go_el)
                else:
                    helper.click_view_by_js(btn_book)
                login_name_input_el = helper.get_browser().find_element_by_id(
                    "nloginname"
                )
                # 判断登录框是否出现
                if (
                    helper.get_browser()
                    .find_element_by_id("maskloginbox")
                    .is_displayed()
                    and login_name_input_el is not None
                ):
                    login_name_input_el.send_keys("18013862580")
                    helper.get_browser().find_element_by_id("npwd").send_keys(
                        "jmj641020"
                    )
                    btn_login = helper.get_browser().find_element_by_id("nsubmit")
                    # 点击登录按钮
                    helper.click_view_by_js(btn_login)
                    # 进入填写乘机人信息页面
                    WebDriverWait(helper.get_browser(), 20, 0.5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "contact-box"))
                    )
                    # 获取浏览器中所有的cookie
                    cookies = helper.get_browser()._get_cookies()
                    ctrip_cookies = []
                    for item in cookies:
                        # 筛选出所有的 ctrip 的 cookie
                        if "ctrip" in item["domain"]:
                            ctrip_cookies.append(item)
                    # 保存 ctrip cookie 一个月
                    _save_cookies(json.dumps(ctrip_cookies))
                return helper
            else:
                # 点击去程航班订票按钮，开始请求返程航班
                btn_book = go_el.find_element_by_css_selector("div.btn.btn-book")
                if btn_book is None:
                    helper.click_view_by_js(go_el)
                else:
                    helper.click_view_by_js(btn_book)
                # 判断是否已经进入到返程航班页面
                WebDriverWait(helper.get_browser(), 20, 0.5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "select-flight"))
                )
                helper.scroll_to_footer()
                back_flight_els = helper.get_browser().find_elements_by_css_selector(
                    "div.flight-item"
                )
                for back_el in back_flight_els:
                    back_airline = (
                        back_el.find_element_by_css_selector("div.airline-name")
                        .find_element_by_tag_name("span")
                        .text
                    )
                    back_dep_time = (
                        back_el.find_element_by_css_selector("div.depart-box")
                        .find_element_by_css_selector("div.time")
                        .text
                    )
                    back_arr_time = (
                        back_el.find_element_by_css_selector("div.arrive-box")
                        .find_element_by_css_selector("div.time")
                        .text
                    )
                    if all(
                        [
                            back_flight.get("airline") in back_airline,
                            back_flight.get("dep_time") in back_dep_time,
                            back_flight.get("arr_time") in back_arr_time,
                        ]
                    ):
                        helper.scroll_to_view(back_el)
                        back_seats = back_el.find_elements_by_css_selector(
                            "div.seat-row.seat-row-v3"
                        )
                        # 点击对应价格的产品
                        btn_book = back_seats[
                            back_flight["index"]
                        ].find_element_by_css_selector("div.btn.btn-book")
                        if btn_book is None:
                            helper.click_view_by_js(back_el)
                        else:
                            helper.click_view_by_js(btn_book)
                        login_name_input_el = helper.get_browser().find_element_by_id(
                            "nloginname"
                        )
                        # 判断登录框是否出现
                        if (
                            helper.get_browser()
                            .find_element_by_id("maskloginbox")
                            .is_displayed()
                            and login_name_input_el is not None
                        ):
                            login_name_input_el.send_keys("18013862580")
                            helper.get_browser().find_element_by_id("npwd").send_keys(
                                "jmj641020"
                            )
                            btn_login = helper.get_browser().find_element_by_id(
                                "nsubmit"
                            )
                            # 点击登录按钮
                            helper.click_view_by_js(btn_login)
                            # 进入填写乘机人信息页面
                            WebDriverWait(helper.get_browser(), 20, 0.5).until(
                                EC.presence_of_element_located(
                                    (By.CLASS_NAME, "contact-box")
                                )
                            )
                            WebDriverWait(helper.get_browser(), 20, 0.5).until(
                                EC.presence_of_element_located(
                                    (By.CLASS_NAME, "flight-notices")
                                )
                            )
                            # 获取浏览器中所有的cookie
                            cookies = helper.get_browser()._get_cookies()
                            ctrip_cookies = []
                            for item in cookies:
                                # 筛选出所有的 ctrip 的 cookie
                                if "ctrip" in item["domain"]:
                                    ctrip_cookies.append(item)
                            # 保存 ctrip cookie 一个月
                            _save_cookies(json.dumps(ctrip_cookies))
                        return helper
    return helper


def _crawl_flights_in_page(helper):
    """抓取页面中的航班列表信息"""
    helper.scroll_to_footer()
    html_text = (
        helper.get_browser()
        .find_element_by_css_selector("div.flight-list")
        .get_attribute("innerHTML")
    )
    dom = etree.HTML(html_text, etree.HTMLParser())
    flight_els = dom.xpath('//div[contains(@class,"flight-item")]')
    flights = []
    for el in flight_els:
        airline = el.xpath('.//div[@class="airline-name"]/span/text()')[0]
        from_time = el.xpath('.//div[@class="depart-box"]/div[@class="time"]/text()')[0]
        to_time = el.xpath('.//div[@class="arrive-box"]/div[@class="time"]/text()')[0]
        flights.append({"airline": airline, "from_time": from_time, "to_time": to_time})
    return flights


def call_inter_oneway_flights(
    dep_city: str, arr_city: str, date: str, cabin: str
) -> (BrowserHelper, list):
    """请求国际单程航班
    :param dep_city: 出发城市
    :param arr_city: 到达城市
    :param date: 出发日期
    :param cabin: 舱型
    :return BrowserHelper,list
    """
    helper = _open_inter_flight_page(1, dep_city, arr_city, date, cabin)
    WebDriverWait(helper.get_browser(), 20, 0.5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "flight-item"))
    )
    page_flights = _crawl_flights_in_page(helper)
    return helper, page_flights


def call_inter_round_go_flights(
    dep_city: str, arr_city: str, date: str, cabin: str
) -> (BrowserHelper, list):
    """请求国际往返航班中的去程航班
    :param dep_city: 出发城市
    :param arr_city: 到达城市
    :param date: 出发日期
    :param cabin: 舱型
    :return BrowserHelper,list
    """
    helper = _open_inter_flight_page(2, dep_city, arr_city, date, cabin)
    WebDriverWait(helper.get_browser(), 20, 0.5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "flight-item"))
    )
    page_flights = _crawl_flights_in_page(helper)
    return helper, page_flights


def call_inter_round_back_flights(
    dep_city: str, arr_city: str, date: str, cabin: str, go_flight: dict
) -> (BrowserHelper, list):
    """请求国际往返航班中的返程航班
    :param dep_city: 出发城市
    :param arr_city: 到达城市
    :param date: 出发日期
    :param cabin: 舱型
    :param go_flight: 去程航班信息
    :return BrowserHelper,list
    """
    helper = _open_inter_round_back_flight_page(
        dep_city, arr_city, date, cabin, go_flight
    )
    # 如果 helper 为 None，则代表未能找到对应的去程，直接返回 None
    if helper is None:
        return None, None
    WebDriverWait(helper.get_browser(), 20, 0.5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "flight-seats"))
    )
    page_flights = _crawl_flights_in_page(helper)
    return helper, page_flights
