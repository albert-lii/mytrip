# -*- coding:utf-8 -*-
"""
    :author: Albert Li
    :time: 2019/11/12 15:51 
"""
import json
from flask import request, jsonify
from loguru import logger
from app.flight import flight_api_bp, ctrip_spider
from app.db.redis_helper import RedisClient
from app.response.response_code import ResponseCode
from app.response.response import (
    make_flights_response_ok_as_dict,
    make_flight_response_ok,
    make_response_error,
    make_response_error_as_dict,
)
from app.utils import key_helper

redis_client = RedisClient()


@flight_api_bp.route("/ctrip/list", methods=["POST"])
def fetch_ctrip_inter_flights():
    """抓取携程国际航班数据"""
    args = request.json
    flight_type = args.get("flight_type", 2)  # 航班类型 1: 国内航班  2: 国际航班
    trip_type = args.get("trip_type", 1)  # 行程类型 1: 单程  2: 往返-去程  3: 往返-返程
    dep_city = args.get("dep_city")  # 出发城市三字码
    arr_city = args.get("arr_city")  # 到达城市三字码
    date = args.get("date")  # 出发日期，往返日期用逗号连接，例如 2019-09-10,2019-09-20
    cabin = args.get("cabin", "Y_S")  # 舱型  Y/Y_S: 经济舱  C: 公务舱  F: 头等舱
    goflight_airline = args.get("goflight_airline")  # 去程航空公司
    goflight_deptime = args.get("goflight_deptime")  # 去程起飞时间
    goflight_arrtime = args.get("goflight_arrtime")  # 去程到达时间
    if cabin == "Y":
        cabin = "Y_S"
    if any([dep_city is None, arr_city is None, date is None]):
        return make_response_error(ResponseCode.ERROR_MISS_PARAMETER, "缺少查询航班的必需信息")
    resp = _crawl_ctrip_inter_flights(
        trip_type,
        dep_city,
        arr_city,
        date,
        cabin,
        goflight_airline,
        goflight_deptime,
        goflight_arrtime,
    )
    print(resp)
    return jsonify(resp)


@flight_api_bp.route("/ctrip/one", methods=["POST"])
def fetch_ctrip_inter_flight_by_number():
    """根据航班号从携程抓取对应的航班信息"""
    args = request.json
    flight_type = args.get("flight_type", 2)  # 航班类型 1: 国内航班  2: 国际航班
    trip_type = args.get("trip_type", 1)  # 行程类型 1: 单程  2: 往返-去程  3: 往返-返程
    dep_city = args.get("dep_city")  # 出发城市三字码
    arr_city = args.get("arr_city")  # 到达城市三字码
    date = args.get("date")  # 出发日期，往返日期用逗号连接，例如 2019-09-10,2019-09-20
    cabin = args.get("cabin", "Y_S")  # 舱型  Y/Y_S: 经济舱  C: 公务舱  F: 头等舱
    flight_no = args.get("flight_no")  # 航班号，多个航班号用逗号隔开
    goflight_airline = args.get("goflight_airline")  # 去程航空公司
    goflight_deptime = args.get("goflight_deptime")  # 去程起飞时间
    goflight_arrtime = args.get("goflight_arrtime")  # 去程到达时间

    if cabin == "Y":
        cabin = "Y_S"
    if any([dep_city is None, arr_city is None, date is None]):
        return make_response_error(ResponseCode.ERROR_MISS_PARAMETER, "缺少查询航班的必需信息")
    flights_resp = _crawl_ctrip_inter_flights(
        trip_type,
        dep_city,
        arr_city,
        date,
        cabin,
        goflight_airline,
        goflight_deptime,
        goflight_arrtime
    )
    fnos = flight_no.split(",")
    if flights_resp["code"] == 0:
        flights = flights_resp["data"]["flights"]
        if trip_type == 1:
            for item in flights:
                tfnos = [fno for fno in item["routes"]]
                # 取 tfnos 有而 fnos 没有的值
                diffs = list(set(tfnos).difference(set(fnos)))
                if len(diffs) == 0:
                    return make_flight_response_ok(item)
            return make_response_error(ResponseCode.ERROR_NO_RESOURCE_FOUND)
        else:
            if trip_type == 2:
                oneway_flights_resp = _crawl_ctrip_inter_flights(
                    1,
                    dep_city,
                    arr_city,
                    date[:10],
                    cabin,
                    goflight_airline,
                    goflight_deptime,
                    goflight_arrtime
                )
            else:
                oneway_flights_resp = _crawl_ctrip_inter_flights(
                    1,
                    arr_city,
                    dep_city,
                    date[-10],
                    cabin,
                    goflight_airline,
                    goflight_deptime,
                    goflight_arrtime
                )
            flight = None
            for item in flights:
                tfnos = [fno for fno in item["routes"]]
                # 取 tfnos 有而 fnos 没有的值
                diffs = list(set(tfnos).difference(set(fnos)))
                if len(diffs) == 0:
                    flight = item
                    break
            if oneway_flights_resp["code"] == 0:
                oneway_flights = oneway_flights_resp["data"]["flights"]
                for item in oneway_flights:
                    tfnos = [fno for fno in item["routes"]]
                    # 取 tfnos 有而 fnos 没有的值
                    diffs = list(set(tfnos).difference(set(fnos)))
                    if len(diffs) == 0:
                        if flight is not None:
                            flight["products"] = flight["products"] + item["products"]
                        else:
                            flight = item
                        break
            if flight is not None:
                return make_flight_response_ok(flight)
            else:
                return make_response_error(ResponseCode.ERROR_NO_RESOURCE_FOUND)


def _crawl_ctrip_inter_flights(
        trip_type,
        dep_city,
        arr_city,
        date,
        cabin,
        goflight_airline,
        goflight_deptime,
        goflight_arrtime,
):
    if trip_type == 1:
        key = key_helper.generate_ctrip_flights_key(1, dep_city, arr_city, date, cabin)
        data = redis_client.get_data(key)
        if data is None or json.loads(data)["code"] != ResponseCode.SUCCESS.code:
            helper, page_flights = ctrip_spider.call_inter_oneway_flights(
                dep_city, arr_city, date, cabin
            )
            helper.close_all()
            return _get_flights_from_cache(key, page_flights)
        else:
            return json.loads(data)
    elif trip_type == 2:
        date_arr = date.split(",")
        if any([len(date) != 21, len(date_arr) != 2]):
            return make_response_error_as_dict(
                ResponseCode.ERROR_INVALID_PARAMETER, "出发日期无效"
            )
        date = date_arr[0] + "_" + date_arr[1]
        key = key_helper.generate_ctrip_flights_key(2, dep_city, arr_city, date, cabin)
        data = redis_client.get_data(key)
        if data is None or json.loads(data)["code"] != ResponseCode.SUCCESS.code:
            helper, page_flights = ctrip_spider.call_inter_round_go_flights(
                dep_city, arr_city, date, cabin
            )
            helper.close_all()
            return _get_flights_from_cache(key, page_flights)
        else:
            return json.loads(data)
    else:
        if any(
                [
                    goflight_airline is None,
                    goflight_deptime is None,
                    goflight_arrtime is None,
                ]
        ):
            return make_response_error_as_dict(
                ResponseCode.ERROR_MISS_PARAMETER, "缺少去程航班信息"
            )
        date_arr = date.split(",")
        if any([len(date) != 21, len(date_arr) != 2]):
            return make_response_error_as_dict(
                ResponseCode.ERROR_INVALID_PARAMETER, "出发日期无效"
            )
        date = date_arr[0] + "_" + date_arr[1]
        key = key_helper.generate_ctrip_flights_key(
            3,
            dep_city,
            arr_city,
            date,
            cabin,
            goflight_airline,
            goflight_deptime,
            goflight_arrtime,
        )
        data = redis_client.get_data(key)
        if data is None or json.loads(data)["code"] != ResponseCode.SUCCESS.code:
            helper, page_flights = ctrip_spider.call_inter_round_back_flights(
                dep_city,
                arr_city,
                date,
                cabin,
                {
                    "airline": goflight_airline,
                    "dep_time": goflight_deptime,
                    "arr_time": goflight_arrtime,
                },
            )
            if all([helper is None, page_flights is None]):
                return make_response_error_as_dict(
                    ResponseCode.ERROR_NO_RESOURCE_FOUND, "没有找到对应的去程航班"
                )
            helper.close_all()
            return _get_flights_from_cache(key, page_flights)
        else:
            return jsonify(json.loads(data))


def _filter_fake_flights(api_flights, page_flights) -> list:
    """过滤从携程航班 api 中拦截的航班数据中的假数据
    :param api_flights: 携程航班 api 中的航班列表数据
    :param page_flights: 携程航班页面中的航班列表数据
    :return: 过滤后的航班数据
    """
    if any([api_flights is None, len(api_flights) == 0]):
        return None
    if any([page_flights is None, len(page_flights) == 0]):
        return api_flights
    filter_flights = []
    print(api_flights)
    for af in api_flights:
        for pf in page_flights:
            if all(
                    [
                        af["airline"] == pf["airline"],
                        af["from_time"] == pf["from_time"],
                        af["to_time"] == pf["to_time"],
                    ]
            ):
                filter_flights.append(af)
    return filter_flights


def _get_flights_from_cache(key, page_flights) -> dict:
    """从缓存中获取航班列表"""
    data = redis_client.check_data_by_cycle(key)
    if data is not None:
        data = json.loads(data)
        if data["code"] == ResponseCode.SUCCESS.code:
            flights = _filter_fake_flights(data["data"]["flights"], page_flights)
            return make_flights_response_ok_as_dict(flights)
        else:
            return data
    else:
        return make_response_error_as_dict(ResponseCode.ERROR_NO_RESOURCE_FOUND)
