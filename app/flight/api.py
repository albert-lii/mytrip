# -*- coding:utf-8 -*-
"""
    机票接口

    :author: Albert Li
    :time: 2019/11/12 15:51 
"""
from flask import request, jsonify
from app.flight import flight_api_bp
from app.flight.ctrip_spider import (
    crawl_ctrip_inter_flights,
    crawl_ctrip_inter_flight_by_number,
)
from app.flight.ceair_spider import crawl_ceair_flights, crawl_ceair_flight_by_number
from app.response.response_code import ResponseCode
from app.response.response import make_response_error


@flight_api_bp.route("/ctrip", methods=["POST"])
def fetch_ctrip_inter_flights():
    """抓取携程国际航班数据"""
    args = request.json
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
    resp = crawl_ctrip_inter_flights(
        trip_type,
        dep_city,
        arr_city,
        date,
        cabin,
        goflight_airline,
        goflight_deptime,
        goflight_arrtime,
    )
    # 再次请求一下，因为有时会发生因超时而返回不了数据的情况
    if trip_type == 3 and resp["msg"] == "没有找到对应的去程航班":
        resp = crawl_ctrip_inter_flights(
            trip_type,
            dep_city,
            arr_city,
            date,
            cabin,
            goflight_airline,
            goflight_deptime,
            goflight_arrtime,
        )
    return jsonify(resp)


@flight_api_bp.route("/ctrip/one", methods=["POST"])
def fetch_ctrip_inter_flight_by_number():
    """根据航班号从携程抓取对应的航班信息"""
    args = request.json
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
    if any([dep_city is None, arr_city is None, date is None, flight_no is None]):
        return make_response_error(ResponseCode.ERROR_MISS_PARAMETER, "缺少查询航班的必需信息")
    resp = crawl_ctrip_inter_flight_by_number(
        trip_type,
        dep_city,
        arr_city,
        date,
        cabin,
        flight_no,
        goflight_airline,
        goflight_deptime,
        goflight_arrtime,
    )
    return jsonify(resp)


@flight_api_bp.route("/ceair", methods=["POST"])
def fetch_ceair_flights():
    """从东方航空抓取航班列表信息"""
    args = request.json
    trip_type = args.get("trip_type", 1)
    dep_city = args.get("dep_city")
    arr_city = args.get("arr_city")
    date = args.get("date")
    cabin = args.get("cabin")
    goflight_no = args.get("goflight_no")  # 去程航班号
    goflight_pindex = args.get("goflight_pindex", 0)  # 去程航班选择的产品 index
    if any([dep_city is None, arr_city is None, date is None]):
        return make_response_error(ResponseCode.ERROR_MISS_PARAMETER, "缺少查询航班的必需信息")
    if trip_type == 3 and goflight_no == None:
        return make_response_error(ResponseCode.ERROR_MISS_PARAMETER, "缺少去程航班号参数")
    resp = crawl_ceair_flights(
        trip_type, dep_city, arr_city, date, cabin, goflight_no, goflight_pindex
    )
    return jsonify(resp)


@flight_api_bp.route("/ceair/one", methods=["POST"])
def fetch_ceair_flight_by_number():
    """根据航班号从东方航空抓取对应的航班信息"""
    args = request.json
    trip_type = args.get("trip_type", 1)
    dep_city = args.get("dep_city")
    arr_city = args.get("arr_city")
    date = args.get("date")
    cabin = args.get("cabin")
    flight_no = args.get("flight_no")
    goflight_no = args.get("goflight_no")  # 去程航班号
    goflight_pindex = args.get("goflight_pindex", 0)  # 去程航班选择的产品 index

    if any([dep_city is None, arr_city is None, date is None, flight_no is None]):
        return make_response_error(ResponseCode.ERROR_MISS_PARAMETER, "缺少查询航班的必需信息")
    if trip_type == 3 and goflight_no is None:
        return make_response_error(ResponseCode.ERROR_MISS_PARAMETER, "缺少去程航班号参数")
    resp = crawl_ceair_flight_by_number(
        trip_type,
        dep_city,
        arr_city,
        date,
        cabin,
        flight_no,
        goflight_no,
        goflight_pindex,
    )
    return jsonify(resp)
