# -*- coding:utf-8 -*-
"""
    :author: Albert Li
    :time: 2019/11/13 15:45 
"""
import json


def generate_flights_key(
    source: str,
    trip_type: int,
    dep_city: str,
    arr_city: str,
    date: str,
    cabin: str,
    goflight_no: str = None,
    goflight_pindex: int = 0,
) -> str:
    """生成缓存携程航班数据的 key
    :param trip_type: 行程类型
    :param dep_city: 出发城市
    :param arr_city: 到达城市
    :param date: 出发日期
    :param cabin: 舱型
    :param goflight_airline: 去程航空公司
    :param goflihgt_deptime: 去程航班起飞时间
    :param goflihgt_arrtime: 去程航班到达时间
    :return: 缓存携程航班数据的 key
    """
    prefix = "flights-"
    suffix = "{source}-{dep_city}-{arr_city}-{date}-{cabin}".format(
        source=source,
        dep_city=dep_city.upper(),
        arr_city=arr_city.upper(),
        date=date,
        cabin=cabin,
    )
    if trip_type == 1:
        return prefix + "oneway-" + suffix
    elif trip_type == 2:
        return prefix + "round-go-" + suffix
    else:
        return (
            prefix
            + "round-back-"
            + suffix
            + "-{goflight_no}-{goflight_pindex}".format(
                goflight_no=goflight_no, goflight_pindex=goflight_pindex
            )
        )


def generate_flight_key(
    source: str,
    trip_type: int,
    dep_city: str,
    arr_city: str,
    date: str,
    cabin: str,
    flight_no: str = None,
) -> str:
    """生成缓存携程航班数据的 key
    :param trip_type: 行程类型
    :param dep_city: 出发城市
    :param arr_city: 到达城市
    :param date: 出发日期
    :param cabin: 舱型
    :param goflight_airline: 去程航空公司
    :param goflihgt_deptime: 去程航班起飞时间
    :param goflihgt_arrtime: 去程航班到达时间
    :return: 缓存携程航班数据的 key
    """
    prefix = "oneflight-"
    suffix = "{source}-{dep_city}-{arr_city}-{date}-{cabin}".format(
        source=source,
        dep_city=dep_city.upper(),
        arr_city=arr_city.upper(),
        date=date,
        cabin=cabin,
    )
    if trip_type == 1:
        return prefix + "oneway-" + suffix
    elif trip_type == 2:
        return (
            prefix + "round-go-" + suffix + "-{flight_no}".format(flight_no=flight_no)
        )
    else:
        return (
            prefix + "round-back-" + suffix + "-{flight_no}".format(flight_no=flight_no)
        )


def generate_ctrip_flights_key(
    trip_type: int,
    dep_city: str,
    arr_city: str,
    date: str,
    cabin: str,
    goflight_airline: str = None,
    goflight_deptime: str = None,
    goflight_arrtime: str = None,
) -> str:
    """生成缓存携程航班数据的 key
    :param trip_type: 行程类型
    :param dep_city: 出发城市
    :param arr_city: 到达城市
    :param date: 出发日期
    :param cabin: 舱型
    :param goflight_airline: 去程航空公司
    :param goflihgt_deptime: 去程航班起飞时间
    :param goflihgt_arrtime: 去程航班到达时间
    :return: 缓存携程航班数据的 key
    """
    prefix = "flights-ctrip-inter-"
    suffix = "{dep_city}-{arr_city}-{date}-{cabin}".format(
        dep_city=dep_city.upper(), arr_city=arr_city.upper(), date=date, cabin=cabin
    )
    if trip_type == 1:
        return prefix + "oneway-" + suffix
    elif trip_type == 2:
        return prefix + "round-go-" + suffix
    else:
        return (
            prefix
            + "round-back-"
            + suffix
            + "-{airline}-{dep_time}-{arr_time}".format(
                airline=goflight_airline,
                dep_time=goflight_deptime,
                arr_time=goflight_arrtime,
            )
        )


def generate_ctrip_flight_penalty_rule_key(json_str) -> str:
    """生成缓存携程机票退改签说明数据的 key
    :param json_str: 从代理监听器中拿到的数据
    :return: 缓存携程机票退改签说明数据的 key
    """
    info = json.loads(json_str)
    flight_list = info.get("criteria").get("FlightInfoList")
    goflight_info = ""
    backflight_info = ""
    for item in flight_list:
        if item["SegmentNo"] == 1:
            goflight_info += "{flight_no}-{dep_airport}-{arr_airport}-{date}||".format(
                flight_no=item["MarketingFlightNo"],
                dep_airport=item["DepartureAirportCode"],
                arr_airport=item["ArrivalAirportCode"],
                date=item["TakeOffDateTime"][:16],
            )
        else:
            backflight_info += "{flight_no}-{dep_airport}-{arr_airport}-{date}||".format(
                flight_no=item["MarketingFlightNo"],
                dep_airport=item["DepartureAirportCode"],
                arr_airport=item["ArrivalAirportCode"],
                date=item["TakeOffDateTime"][:16],
            )
    prefix = "flight-ctrip-penalty-rule-"
    return prefix + goflight_info + backflight_info
