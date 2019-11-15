# -*- coding:utf-8 -*-
"""
    :author: Albert Li
    :time: 2019/11/13 17:57 
"""
import json
from loguru import logger
from mitmproxy import http

from conf import loguru_conf
from proxy.ctrip_flight_parser import parse_inter_flights, parse_penalty_rule
from app.db.redis_helper import RedisClient
from app.utils import key_helper
from app.response.response_code import ResponseCode
from app.response.response import (
    make_flights_response_ok_as_str,
    make_penalty_rule_response_ok_as_str,
    make_response_error_as_str,
)

loguru_conf.init("proxy")
redis_client = RedisClient()


class CtripFlightMonitor(object):
    """监听携程国际航班 api 调用"""

    def request(self, flow: http.HTTPFlow):
        """监听携程网的机票请求"""
        # if flow.live:
        #     # 动态设置上游代理，防止ip被封
        #     proxy = ('http://121.228.53.238', '8080')
        #     flow.live.change_upstream_proxy_server(proxy)

    def response(self, flow: http.HTTPFlow):
        """监听携程网的机票请求响应"""
        # 国际单程/去程和国际往返的去程的 url
        inter_go_url = "flights.ctrip.com/international/search/api/search/batchSearch"
        # 国际往返的返程的 url
        inter_back_url = "flights.ctrip.com/international/search/api/search/routeSearch"
        # 退改签说明接口的 url
        penalty_rule_url = "https://flights.ctrip.com/international/search/api/penalty/getOrderPenaltyRule"
        if any([inter_go_url in flow.request.url, inter_back_url in flow.request.url]):
            """国际航班监听"""
            # 请求提交参数
            req_data = json.loads(str(flow.request.content, encoding="utf-8"))
            req_segments = req_data.get("flightSegments")  # 请求参数中的航班列表
            if flow.response.status_code == 200:
                # 国际航班请求的响应处理
                res_json = json.loads(flow.response.text)
                # 判断请求是否成功
                if res_json.get("status") != 0:
                    # 请求未成功，打印错误信息
                    if inter_go_url in flow.request.url:
                        if len(req_segments) == 1:
                            # 单程
                            key = key_helper.generate_ctrip_flights_key(
                                1,
                                dep_city=req_segments[0].get("departureCityCode"),
                                arr_city=req_segments[0].get("arrivalCityCode"),
                                date=req_segments[0].get("departureDate"),
                                cabin=req_data.get("cabin"),
                            )
                            redis_client.set_data_with_expire(
                                key,
                                make_response_error_as_str(
                                    ResponseCode.FAIL,
                                    res_json.get("status") + " " + res_json.get("msg"),
                                ),
                            )
                            logger.error(
                                "国际单程航班列表获取失败: %s  >>>  %s",
                                res_json.get("status"),
                                res_json.get("msg"),
                            )
                        else:
                            # 往返 - 去程
                            key = key_helper.generate_ctrip_flights_key(
                                2,
                                dep_city=req_segments[0].get("departureCityCode"),
                                arr_city=req_segments[0].get("arrivalCityCode"),
                                date=req_segments[0].get("departureDate")
                                + "_"
                                + req_segments[1].get("departureDate"),
                                cabin=req_data.get("cabin"),
                            )
                        redis_client.set_data_with_expire(
                            key,
                            make_response_error_as_str(
                                ResponseCode.FAIL,
                                res_json.get("status") + " " + res_json.get("msg"),
                            ),
                        )
                        logger.error(
                            "国际去程航班列表获取失败: %s  >>>  %s",
                            res_json.get("status"),
                            res_json.get("msg"),
                        )
                    else:
                        # 因为无法知道是根据去程航班列表中的哪一班航班来选择返程的，所以无法构造 key 来缓存请求结果来及时给服务器返回响应
                        logger.error(
                            "国际返程航班列表获取失败: %s  >>>  %s",
                            res_json.get("status"),
                            res_json.get("msg"),
                        )
                else:
                    if inter_go_url in flow.request.url:
                        if len(req_segments) == 1:
                            # 单程
                            flights, extra = parse_inter_flights(
                                res_json.get("data"), 1
                            )
                            key = key_helper.generate_ctrip_flights_key(
                                1,
                                dep_city=req_segments[0].get("departureCityCode"),
                                arr_city=req_segments[0].get("arrivalCityCode"),
                                date=req_segments[0].get("departureDate"),
                                cabin=req_data.get("cabin"),
                            )
                            redis_client.set_data_with_expire(
                                key, make_flights_response_ok_as_str(flights)
                            )
                        else:
                            # 往返-去程
                            flights, extra = parse_inter_flights(
                                res_json.get("data"), 2
                            )
                            key = key_helper.generate_ctrip_flights_key(
                                2,
                                dep_city=req_segments[0].get("departureCityCode"),
                                arr_city=req_segments[0].get("arrivalCityCode"),
                                date=req_segments[0].get("departureDate")
                                + "_"
                                + req_segments[1].get("departureDate"),
                                cabin=req_data.get("cabin"),
                            )
                            redis_client.set_data_with_expire(
                                key, make_flights_response_ok_as_str(flights)
                            )
                    else:
                        # 往返-返程
                        flights, go_flight = parse_inter_flights(
                            res_json.get("data"), 3
                        )
                        key = key_helper.generate_ctrip_flights_key(
                            3,
                            dep_city=req_segments[0].get("departureCityCode"),
                            arr_city=req_segments[0].get("arrivalCityCode"),
                            date=req_segments[0].get("departureDate")
                            + "_"
                            + req_segments[1].get("departureDate"),
                            cabin=req_data.get("cabin"),
                            goflight_airline=go_flight.get("airline"),
                            goflight_deptime=go_flight.get("from_time"),
                            goflight_arrtime=go_flight.get("to_time"),
                        )
                        redis_client.set_data_with_expire(
                            key, make_flights_response_ok_as_str(flights)
                        )
            else:
                if inter_go_url in flow.request.url:
                    if len(req_segments) == 1:
                        key = key_helper.generate_ctrip_flights_key(
                            1,
                            dep_city=req_segments[0].get("departureCityCode"),
                            arr_city=req_segments[0].get("arrivalCityCode"),
                            date=req_segments[0].get("departureDate"),
                            cabin=req_data.get("cabin"),
                        )
                        redis_client.set_data_with_expire(
                            key,
                            make_response_error_as_str(
                                flow.response.status_code + " " + flow.response.reason
                            ),
                        )
                        logger.error(
                            "国际单程航班列表请求失败: %s  >>>  %s",
                            flow.response.status_code,
                            flow.response.reason,
                        )
                    else:
                        key = key_helper.generate_ctrip_flights_key(
                            2,
                            dep_city=req_segments[0].get("departureCityCode"),
                            arr_city=req_segments[0].get("arrivalCityCode"),
                            date=req_segments[0].get("departureDate")
                            + "_"
                            + req_segments[1].get("departureDate"),
                            cabin=req_data.get("cabin"),
                        )
                        redis_client.set_data_with_expire(
                            key,
                            make_response_error_as_str(
                                flow.response.status_code + " " + flow.response.reason
                            ),
                        )

                        logger.error(
                            "国际去程航班列表请求失败: %s  >>>  %s",
                            flow.response.status_code,
                            flow.response.reason,
                        )
                else:
                    logger.error(
                        "国际返程航班列表请求失败: %s  >>>  %s",
                        flow.response.status_code,
                        flow.response.reason,
                    )
        elif penalty_rule_url in flow.request.url:  # 退改签说明监听
            """退改签说明接口"""
            # 请求提交参数
            req_data = json.loads(str(flow.request.content, encoding="utf-8"))
            req_luggage_visa = req_data.get("luggageVisaKey")
            key = key_helper.generate_ctrip_flight_penalty_rule_key(req_luggage_visa)
            if flow.response.status_code == 200:
                res_json = json.loads(flow.response.text)
                if res_json.get("status") != 0:
                    redis_client.set_data_with_expire(
                        key,
                        make_response_error_as_str(
                            res_json.get("status") + " " + res_json.get("msg")
                        ),
                    )
                    logger.error(
                        "获取退改签说明失败: %s  >>>  %s",
                        res_json.get("status"),
                        res_json.get("msg"),
                    )
                else:
                    # 有效期三天
                    redis_client.set_data_with_expire(
                        key,
                        make_penalty_rule_response_ok_as_str(
                            parse_penalty_rule(res_json.get("data").get("dataList"))
                        ),
                        259200,
                    )
            else:
                redis_client.set_data_with_expire(
                    key,
                    make_response_error_as_str(
                        flow.response.status_code + " " + flow.response.reason
                    ),
                )
                logger.error(
                    "获取退改签说明失败: %s  >>>  %s",
                    flow.response.status_code,
                    flow.response.reason,
                )
