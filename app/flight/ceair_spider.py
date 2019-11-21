# -*- coding:utf-8 -*-
"""
    东方航空机票爬虫

    :author: Albert Li
    :time: 2019/11/20 10:25
"""
import json
from loguru import logger
from lxml import html
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException

# 定位策略
from selenium.webdriver.common.by import By

# expected_conditions 类，负责条件触发
from selenium.webdriver.support import expected_conditions as EC

# WebDriverWait 库，负责循环等待
from selenium.webdriver.support.wait import WebDriverWait

from app.flight import entities
from app.db.redis_helper import RedisClient
from app.utils.browser import BrowserHelper
from app.utils import key_helper
from app.response.response_code import ResponseCode
from app.response.response import (
    make_flights_response_ok_as_dict,
    make_flight_response_ok_as_dict,
    make_response_error_as_dict,
)

redis_client = RedisClient()

etree = html.etree


def _crawl_web_content(
    helper: BrowserHelper,
    trip_type: int,
    dep_city: str,
    arr_city: str,
    go_date: str,
    back_date: str,
) -> (str, list):
    """获取网页内容
    :param helper: 浏览器
    :param trip_type: 1: 单程  2: 往返
    :param dep_city: 出发城市
    :param arr_city: 到达城市
    :param go_date: 去程日期
    :param back_date: 返程日期
    :return: 网页内容 html
    """
    url_go_date: str = go_date
    url_go_date: str = url_go_date.replace("-", "")
    url_go_date: str = url_go_date[-6:]
    base_url: str = "http://www.ceair.com/booking/{dep_city}-{arr_city}-{date}".format(
        dep_city=dep_city.lower(), arr_city=arr_city.lower(), date=url_go_date
    )
    if trip_type == 1:
        # 单程
        url: str = base_url + "_CNY.html"
    else:
        # 往返
        url_back_date: str = back_date
        url_back_date: str = url_back_date.replace("-", "")
        url_back_date: str = url_back_date[-6:]
        url: str = base_url + "-{dep_city}-{arr_city}-{date}_CNY.html".format(
            dep_city=arr_city.lower(), arr_city=dep_city.lower(), date=url_back_date
        )
    helper.open_page(url)
    WebDriverWait(helper.get_browser(), 20, 0.5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "article.flight"))
    )
    return (
        helper.get_browser()
        .find_element_by_css_selector("div.booking-select")
        .get_attribute("innerHTML"),
        helper.get_browser().find_elements_by_css_selector("article.flight"),
    )


def _parse_flights(trip_type: int, cabin: str, html_text: str) -> list:
    """解析航班信息
    :param trip_type: 1: 单程  2: 往返-去程  3: 往返-返程
    :param cabin: 舱位
    :param html_text: 航班部分的 html 内容
    :return: 航班信息列表
    """
    if html_text is None:
        return None
    flights = []
    dom = etree.HTML(html_text, etree.HTMLParser())
    flight_els = dom.xpath('//article[@class="flight"]')
    if len(flight_els) > 0:
        for el in flight_els:
            airport_els = el.xpath('.//div[contains(@class,"airport")]')
            dep_time = airport_els[0].xpath("./time/text()")[0].strip()  # 起飞时间
            arr_time = airport_els[1].xpath("./time/text()")[0].strip()  # 到达时间
            dep_airport = airport_els[0].xpath("./text()")[0]  # 起飞机场
            arr_airport = airport_els[1].xpath("./text()")[0]  # 到达机场
            duration = el.xpath(".//dfn/text()")[0]  # 飞行总时间
            routes = []  # 航段列表
            route_els = el.xpath('.//li[@class="clearfix"]')
            trans_els = el.xpath('.//li[@class="trans"]')
            title_span_els = el.xpath('.//div[@class="title"]/span[not(@class)]')
            # 解析每个航段信息
            for index, route_el in enumerate(route_els):
                route = entities.Route(
                    index=index,
                    airline=title_span_els[index].xpath("./text()")[0],
                    airline_code=route_el.xpath('.//div[@class="flightNo"]/text()')[0][
                        :2
                    ],
                    flight_no=route_el.xpath('.//div[@class="flightNo"]/text()')[0],
                    plane_model=route_el.xpath(
                        './/span[contains(@class,"airplane")]/text()'
                    )[0],
                    duration=route_el.xpath('.//div[@class="zz"]/text()')[0]
                    .replace("行程时间", "")
                    .strip(),
                    dep_day=route_el.xpath(".//time/text()")[0],
                    dep_time=route_el.xpath(".//dt[1]/text()")[0],
                    dep_airport=route_el.xpath('.//div[@class="d11b2"]')[0].xpath(
                        "./text()"
                    )[0],
                    dep_city=route_el.xpath('.//div[@class="d11b1"]')[0].xpath(
                        "./text()"
                    )[0],
                    arr_day=trans_els[index].xpath(".//time/text()")[0],
                    arr_time=route_el.xpath(".//dt[2]/span/text()")[0],
                    arr_airport=route_el.xpath('.//div[@class="d11b2"]')[1].xpath(
                        "./text()"
                    )[0],
                    arr_city=route_el.xpath('.//div[@class="d11b1"]')[1].xpath(
                        "./text()"
                    )[0],
                )
                routes.append(route.to_dict())

            def parse_products(product_els, cabin_class):
                """解析舱位产品
                :param product_els: 舱位产品元素列表
                :param cabin_class: 舱位
                :return: 舱位产品列表
                """
                products = []
                for index, product_el in enumerate(product_els):
                    notes = []
                    note_els = product_el.xpath(
                        './dd[contains(@class,"p-n") and contains(@class,"tags_container")]/em'
                    )
                    for note_el in note_els:
                        note = note_el.xpath("./span/text()")[0]
                        notes.append(note)
                    rule_els = product_el.xpath('.//div[@class="rule-container"]')
                    rule = {}
                    if len(rule_els) > 0:

                        def parse_rule(rule_el):
                            """
                            解析退改签规则
                            :param rule_el: 退改签规则 table 元素
                            :return: 退改签规则
                            """
                            attr_els = rule_el.xpath(".//tr")
                            all_unused_rule = [
                                {
                                    "name": attr_els[0].xpath("./td[2]/text()")[0],
                                    "value": attr_els[1].xpath("./td[2]/text()")[0],
                                },
                                {
                                    "name": attr_els[0].xpath("./td[3]/text()")[0],
                                    "value": attr_els[1].xpath("./td[3]/text()")[0],
                                },
                                {
                                    "name": attr_els[0].xpath("./td[4]/text()")[0],
                                    "value": attr_els[1].xpath("./td[4]/text()")[0],
                                },
                            ]
                            part_unused_rule = [
                                {
                                    "name": attr_els[0].xpath("./td[2]/text()")[0],
                                    "value": attr_els[2].xpath("./td[2]/text()")[0],
                                },
                                {
                                    "name": attr_els[0].xpath("./td[3]/text()")[0],
                                    "value": attr_els[2].xpath("./td[3]/text()")[0],
                                },
                                {
                                    "name": attr_els[0].xpath("./td[4]/text()")[0],
                                    "value": attr_els[2].xpath("./td[4]/text()")[0],
                                },
                            ]
                            return {
                                "all_unused_rule": all_unused_rule,
                                "part_unused_rule": part_unused_rule,
                            }

                        adt_rule_els = rule_els[0].xpath('.//table[@data-rel="ADT"]')
                        rule["adult"] = (
                            None if len(adt_rule_els) == 0 else parse_rule(adt_rule_els)
                        )
                        chd_rule_els = rule_els[0].xpath('.//table[@data-rel="CHD"]')
                        rule["child"] = (
                            None if len(chd_rule_els) == 0 else parse_rule(chd_rule_els)
                        )
                    product = entities.Product(
                        source="ceair",
                        source_desc="东方航空",
                        index=index,
                        position=index,
                        cabin_class=cabin_class,
                        booking_class=product_el.xpath("./dt/span/text()")[0]
                        .strip()
                        .replace("(", "")
                        .replace(")", ""),
                        booking_class_desc=product_el.xpath("./dt/text()")[0].strip(),
                        adult_price=product_el.xpath('.//dd[@class="p-p"]/text()')[0]
                        .replace("起", "")
                        .replace(",", "")
                        .strip(),
                        adult_tax=product_el.xpath(".//span/font/text()")[0].replace(
                            ",", ""
                        )
                        if len(product_el.xpath(".//span/font/text()")) > 0
                        else None,
                        penalty_rule=rule if rule != {} else None,
                        notes=notes if len(notes) > 0 else None,
                        trip_type=trip_type,
                    )
                    products.append(product.to_dict())
                return products

            def parse_product_cards(product_els, cabin_class):
                """
                解析舱位产品，主要针对香港和澳门
                :param product_els: 舱位产品元素列表
                :param cabin_class: 舱位
                :return: 舱位产品列表
                """
                products = []
                for index, product_el in enumerate(product_els):
                    notes = []
                    note_els = product_el.xpath('.//div[@class="content"]/ul/li')
                    for note_el in note_els:
                        note = note_el.xpath('./div[@class="d2"]/text()')[0]
                    notes.append(note)
                    product = entities.Product(
                        source="ceair",
                        source_desc="东方航空",
                        index=index,
                        position=index,
                        cabin_class=cabin_class,
                        booking_class=product_el.xpath(
                            './/div[@class="cabin-name"]/span/text()'
                        )[0]
                        .replace("(", "")
                        .replace(")", "")
                        .strip(),
                        booking_class_desc=product_el.xpath(
                            './/div[@class="cabin-name"]/text()'
                        )[0].strip(),
                        adult_price=product_el.xpath(
                            './/div[@class="price"]/span/text()'
                        )[0]
                        .replace("起", "")
                        .replace(",", "")
                        .strip(),
                        adult_tax=product_el.xpath('.//div[@class="d3"]/text()')[0]
                        .replace("参考税费", "")
                        .replace("￥", "")
                        .strip()
                        if len(product_el.xpath('.//div[@class="d3"]/text()')) > 0
                        else None,
                        notes=notes if len(notes) > 0 else None,
                        penalty_rule=None,
                        trip_type=trip_type,
                    )
                    products.append(product.to_dict())
                return products

            # 经济舱
            economy_els = el.xpath(
                './/div[contains(@class,"product-list") and contains(@data-type,"economy")]'
            )
            if len(economy_els) > 0:
                economy_products = (
                    None
                    if len(economy_els) == 0
                    else parse_products(economy_els[0].xpath("./dl"), "Y")
                )  # 经济舱产品列表
            else:
                # 针对香港、澳门
                economy_els = el.xpath(
                    './/div[contains(@class,"casket") and contains(@data-partition,"economy")]'
                )
                economy_products = (
                    None
                    if len(economy_els) == 0
                    else parse_product_cards(economy_els, "Y")
                )  # 经济舱产品列表

            # 超级经济舱
            super_economy_els = el.xpath(
                './/div[contains(@class,"product-list") and contains(@data-type,"member")]'
            )
            if len(super_economy_els) > 0:
                super_economy_products = (
                    None
                    if len(super_economy_els) == 0
                    else parse_products(super_economy_els[0].xpath("./dl"), "W")
                )  # 超级经济舱产品列表
            else:
                # 针对香港、澳门
                super_economy_els = el.xpath(
                    './/div[contains(@class,"casket") and contains(@data-partition,"member")]'
                )
                super_economy_products = (
                    None
                    if len(super_economy_els) == 0
                    else parse_product_cards(super_economy_els, "W")
                )  # 超级经济舱产品列表

            # 公务舱/头等舱
            luxury_els = el.xpath(
                './/div[contains(@class,"product-list") and contains(@data-type,"luxury")]'
            )
            if len(luxury_els) > 0:
                business_products = (
                    None
                    if len(luxury_els) == 0
                    else parse_products(luxury_els[0].xpath("./dl"), "C")
                )  # 头等舱/公务舱产品列表
            else:
                # 针对香港、澳门
                luxury_els = el.xpath(
                    './/div[contains(@class,"casket") and contains(@data-partition,"luxury")]'
                )
                business_products = (
                    None
                    if len(luxury_els) == 0
                    else parse_product_cards(luxury_els, "C")
                )  # 超级经济舱产品列表

            # 当前查询舱位的产品列表
            products = None
            if cabin == "Y":
                products = economy_products
                if super_economy_products is not None:
                    products += super_economy_products
            elif any([cabin == "C", cabin == "F"]):
                products = business_products
            flight = entities.Flight(
                from_time=dep_time,
                from_airport=dep_airport,
                to_time=arr_time,
                to_airport=arr_airport,
                duration=duration,
                routes=routes,
                products=products,
            )
            flights.append(flight.to_dict())
    return flights


def crawl_ceair_flights(
    trip_type: int,
    dep_city: str,
    arr_city: str,
    date: str,
    cabin: str,
    goflight_no: str = None,
    goflight_pindex: int = 0,
):
    """抓取航班列表
    :param trip_type: 1: 单程  2: 往返 - 去程  3: 往返 - 返程
    :param dep_city: 起飞城市
    :param arr_city: 到达城市
    :param date: 出发日期，有多个用逗号隔开
    :param cabin: 舱位
    :param goflight_no: 查往返航班时，去程航班的航班号
    :param goflight_pindex: 去程航班的的产品的 index
    :return:
    """
    key = key_helper.generate_flights_key(
        "ceair",
        trip_type,
        dep_city,
        arr_city,
        date,
        cabin,
        goflight_no,
        goflight_pindex,
    )
    data = redis_client.get_data(key)
    if data is None or json.loads(data)["code"] != ResponseCode.SUCCESS.code:
        helper = BrowserHelper()
        helper.create_browser()
        date_arr = date.split(",")
        try:
            go_flight_html, flight_els = _crawl_web_content(
                helper,
                trip_type,
                dep_city,
                arr_city,
                date_arr[0],
                date_arr[1] if len(date_arr) == 2 else None,
            )
        except TimeoutException as te:
            logger.error(te.stacktrace)
            helper.close_all()
            return make_response_error_as_dict(ResponseCode.ERROR_TIME_OUT)
        except NoSuchElementException as nse:
            logger.error(nse.msg)
            helper.close_all()
            return make_response_error_as_dict(ResponseCode.ERROR_NO_RESOURCE_FOUND)
        if not flight_els:
            helper.close_all()
            return make_flights_response_ok_as_dict(None)
        go_flights = _parse_flights(trip_type, cabin, go_flight_html)  # 去程航班列表
        if trip_type == 1 or trip_type == 2:
            helper.close_all()
            resp = make_flights_response_ok_as_dict(go_flights)
            redis_client.set_data_with_expire(key, json.dumps(resp))
            return resp
        else:
            goflight_nos = goflight_no.split(",")
            for index, go_flight in enumerate(go_flights):
                tfnos = []
                # 取出当前行程中的所有航班号
                for route in go_flight["routes"]:
                    tfnos.append(route["flight_no"])
                # 判断两个 list 是否有差集
                if len(list(set(tfnos).difference(set(goflight_nos)))) == 0:
                    try:
                        data_type = (
                            "economy"
                            if cabin == "Y"
                            else "member"
                            if cabin == "W"
                            else "luxury"
                        )
                        helper.click_view_by_js(
                            flight_els[index].find_element_by_css_selector(
                                'dd[name="lowest"][data-type="%s"]' % data_type
                            )
                        )
                        helper.click_view_by_js(
                            flight_els[index].find_elements_by_css_selector(
                                'button[name="select"]'
                            )[goflight_pindex]
                        )
                        WebDriverWait(helper.get_browser(), 20, 0.5).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, "article.flight-leaving")
                            )
                        )
                        back_flight_html = (
                            helper.get_browser()
                            .find_element_by_css_selector("hgroup#flight-return")
                            .find_element_by_css_selector("div.booking-select")
                            .get_attribute("innerHTML")
                        )
                    except TimeoutException as te:
                        logger.error(te.msg)
                        helper.close_all()
                        return make_response_error_as_dict(ResponseCode.ERROR_TIME_OUT)
                    except NoSuchElementException as nse:
                        logger.error(nse.msg)
                        helper.close_all()
                        return make_response_error_as_dict(
                            ResponseCode.ERROR_NO_RESOURCE_FOUND
                        )
                    else:
                        back_flights = _parse_flights(
                            trip_type, cabin, back_flight_html
                        )
                        helper.close_all()
                        resp = make_flights_response_ok_as_dict(back_flights)
                        redis_client.set_data_with_expire(key, json.dumps(resp))
                        return resp
            helper.close_all()
            return make_response_error_as_dict(ResponseCode.ERROR_NO_RESOURCE_FOUND)
    else:
        return json.loads(data)


def crawl_ceair_flight_by_number(
    trip_type: int,
    dep_city: str,
    arr_city: str,
    date: str,
    cabin: str,
    flight_no: str,
    goflight_no: str = None,
    goflight_pindex: int = 0,
):
    """根据航班号抓取航班
    :param trip_type: 1: 单程  2: 往返 - 去程  3: 往返 - 返程
    :param dep_city: 起飞城市
    :param arr_city: 到达城市
    :param date: 出发日期，有多个用逗号隔开
    :param cabin: 舱位
    :param flight_no: 当前查询航班的航班号，有多个用逗号隔开
    :param goflight_no: 查往返航班时，去程航班的航班号
    :param goflight_pindex: 去程航班的的产品的 index
    :return:
    """
    key = key_helper.generate_flight_key(
        "ceair", trip_type, dep_city, arr_city, date, cabin, flight_no
    )
    data = redis_client.get_data(key)
    if data is None or json.loads(data)["code"] != ResponseCode.SUCCESS.code:
        flights_resp = crawl_ceair_flights(
            trip_type, dep_city, arr_city, date, cabin, goflight_no, goflight_pindex
        )
        fnos = flight_no.split(",")
        if flights_resp["code"] == 0:
            flights = flights_resp["data"]["flights"]
            if trip_type == 1:
                for item in flights:
                    tfnos = [fno["flight_no"] for fno in item["routes"]]
                    # 取 tfnos 有而 go_flight_nos 没有的值
                    diffs = list(set(tfnos).difference(set(fnos)))
                    if len(diffs) == 0:
                        resp = make_flight_response_ok_as_dict(item)
                        redis_client.set_data_with_expire(key, json.dumps(resp))
                        return resp
                return make_response_error_as_dict(ResponseCode.ERROR_NO_RESOURCE_FOUND)
            else:
                if trip_type == 2:
                    oneway_flights_resp = crawl_ceair_flights(
                        1, dep_city, arr_city, date[:10], cabin
                    )
                else:
                    oneway_flights_resp = crawl_ceair_flights(
                        1, arr_city, dep_city, date[-10:], cabin
                    )
                flight = None
                for item in flights:
                    tfnos = [fno["flight_no"] for fno in item["routes"]]
                    # 取 tfnos 有而 fnos 没有的值
                    diffs = list(set(tfnos).difference(set(fnos)))
                    if len(diffs) == 0:
                        flight = item
                        break
                if oneway_flights_resp["code"] == 0:
                    oneway_flights = oneway_flights_resp["data"]["flights"]
                    for item in oneway_flights:
                        tfnos = [fno["flight_no"] for fno in item["routes"]]
                        # 取 tfnos 有而 fnos 没有的值
                        diffs = list(set(tfnos).difference(set(fnos)))
                        if len(diffs) == 0:
                            if flight is not None:
                                flight["products"] = (
                                    flight["products"] + item["products"]
                                )
                            else:
                                flight = item
                            break
                if flight is not None:
                    resp = make_flight_response_ok_as_dict(flight)
                    redis_client.set_data_with_expire(key, json.dumps(resp))
                    return resp
                else:
                    return make_response_error_as_dict(
                        ResponseCode.ERROR_NO_RESOURCE_FOUND
                    )
        return make_response_error_as_dict(ResponseCode.ERROR_NO_RESOURCE_FOUND)
    else:
        return json.loads(data)
