# -*- coding:utf-8 -*-
"""
    :author: Albert Li
    :time: 2019/11/13 15:45 
"""


def generate_ctrip_flight_key(
    trip_type: int,
    dep_city: str,
    arr_city: str,
    date: str,
    cabin: str,
    goflight_airlinecode: str = None,
    goflihgt_deptime: str = None,
    goflihgt_arrtime: str = None,
) -> str:
    """
    生成缓存携程航班数据的 key
    :param trip_type: 行程类型
    :param dep_city: 起飞城市
    :param arr_city: 到达城市
    :param date: 出发日期
    :param cabin: 舱型
    :param goflight_airlinecode: 舱型
    :param goflihgt_deptime: 去程航班起飞时间
    :param goflihgt_arrtime: 去程航班到达时间
    :return: 缓存携程航班数据的 key
    """
    suffix = "{dep_city}-{arr_city}-{date}-{cabin}".format(
        dep_city=dep_city.upper(), arr_city=arr_city.upper(), date=date, cabin=cabin
    )
    if trip_type == 1:
        return "flight-ctrip-inter-oneway-" + suffix
    elif trip_type == 2:
        return "flight-ctrip-inter-round-go-" + suffix
    else:
        return (
            "flight-ctrip-inter-round-back-"
            + suffix
            + "{airline}-{dep_time}-{arr_time}".format(
                airline=goflight_airlinecode,
                dep_time=goflihgt_deptime,
                arr_time=goflihgt_arrtime,
            )
        )
