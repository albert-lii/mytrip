# -*- coding:utf-8 -*-
"""
    :author: Albert Li
    :time: 2019/11/13 17:57 
"""
import json
import log_conf
from loguru import logger
from mitmproxy import http

from monitor.ctrip_flight_parser import parse_inter_flights as parser
from app.response.response_code import ResponseCode
from app.response.response import make_flights_response_ok, make_response_error

log_conf.init()


class CtripFlightMonitor(object):

    def __init__(self):
        pass

    def request(self, flow: http.HTTPFlow):
        """
        监听携程网的机票请求
        """
        # if flow.live:
        #     # 动态设置上游代理，防止ip被封
        #     proxy = ('http://121.228.53.238', '8080')
        #     flow.live.change_upstream_proxy_server(proxy)

    def response(self, flow: http.HTTPFlow):
        """
        监听携程网的机票请求响应
        """
        # 国际单程和国际往返的去程的 url
        inter_go_url = 'flights.ctrip.com/international/search/api/search/batchSearch'
        # 国际往返的返程的 url
        inter_back_url = 'flights.ctrip.com/international/search/api/search/routeSearch'
        if any([inter_go_url in flow.request.url, inter_back_url in flow.request.url]):
            # 请求提交参数
            req_data = json.loads(str(flow.request.content, encoding='utf-8'))
            req_segments = req_data.get('flightSegments')  # 请求参数中的航班列表
            if flow.response.status_code == 200:
                # 国际航班请求的响应处理
                res_json = json.loads(flow.response.text)
                # 判断请求是否成功
                if res_json.get('status') != 0:
                    # 请求未成功，打印错误信息
                    if inter_go_url in flow.request.url:
                        if len(req_segments) == 1:
                            cache_key = 'flight_inter_oneway_{dep_city}_{arr_city}_{date}_{cabin}'.format(
                                dep_city=req_segments[0].get('departureAirportCode').upper() if req_segments[0].get(
                                    'departureAirportCode') is not None else req_segments[0].get('departureCityCode'),
                                arr_city=req_segments[0].get('arrivalAirportCode').upper() if req_segments[0].get(
                                    'arrivalAirportCode') is not None else req_segments[0].get('arrivalCityCode'),
                                date=req_segments[0].get('departureDate'), cabin=req_data.get('cabin'))
                            redis_helper.set_data_in_redis(cache_key, Response(res_json.get('status'),
                                                                               res_json.get('msg')).to_json())
                            logger.error("国际单程航班获取失败: %s  >>>  %s", res_json.get('status'), res_json.get('msg'))
                        else:
                            cache_key = 'flight_inter_round_go_{dep_city}_{arr_city}_{date}_{cabin}'.format(
                                dep_city=req_segments[0].get('departureAirportCode').upper() if req_segments[0].get(
                                    'departureAirportCode') is not None else req_segments[0].get('departureCityCode'),
                                arr_city=req_segments[0].get('arrivalAirportCode').upper() if req_segments[0].get(
                                    'arrivalAirportCode') is not None else req_segments[0].get('arrivalCityCode'),
                                date=req_segments[0].get('departureDate') + '_' + req_segments[1].get('departureDate'),
                                cabin=req_data.get('cabin'))
                            redis_helper.set_data_in_redis(cache_key, Response(res_json.get('status'),
                                                                               res_json.get('msg')).to_json())
                            logger.error("国际去程航班获取失败: %s  >>>  %s", res_json.get('status'), res_json.get('msg'))
                    else:
                        # cache_key = 'flight_inter_round_{dep_city}_{arr_city}_{date}_{cabin}_2'.format(
                        #     dep_city=req_segments[0].get('departureCityCode').upper(),
                        #     arr_city=req_segments[0].get('arrivalCityCode').upper(),
                        #     date=req_segments[0].get('departureDate') + '_' + req_segments[1].get('departureDate'),
                        #     cabin=req_segments[0].get('cabin'))
                        # redis_helper.set_data_in_redis(cache_key, Response.newRes(res_json.get('status'),
                        #                                                           res_json.get('msg')).to_json())
                        logger.error("国际返程航班获取失败: %s  >>>  %s", res_json.get('status'), res_json.get('msg'))
                else:
                    if inter_go_url in flow.request.url:
                        if len(req_segments) == 1:
                            # 单程
                            flights = parser.parse_inter_flights(res_json.get('data'), 1, 2)
                            cache_key = 'flight_inter_oneway_{dep_city}_{arr_city}_{date}_{cabin}'.format(
                                dep_city=req_segments[0].get('departureAirportCode').upper() if req_segments[0].get(
                                    'departureAirportCode') is not None else req_segments[0].get('departureCityCode'),
                                arr_city=req_segments[0].get('arrivalAirportCode').upper() if req_segments[0].get(
                                    'arrivalAirportCode') is not None else req_segments[0].get('arrivalCityCode'),
                                date=req_segments[0].get('departureDate'), cabin=req_data.get('cabin'))
                            logger.info("cache_key  >>> " + cache_key)
                            redis_helper.set_data_in_redis(cache_key,
                                                           Response.newRes(ResponseCode.SUCCESS,
                                                                           {'flights': flights}).to_json())
                        else:
                            # 往返-去程
                            flights = parser.parse_inter_flights(res_json.get('data'), 2, 1)
                            cache_key = 'flight_inter_round_go_{dep_city}_{arr_city}_{date}_{cabin}'.format(
                                dep_city=req_segments[0].get('departureAirportCode').upper() if req_segments[0].get(
                                    'departureAirportCode') is not None else req_segments[0].get('departureCityCode'),
                                arr_city=req_segments[0].get('arrivalAirportCode').upper() if req_segments[0].get(
                                    'arrivalAirportCode') is not None else req_segments[0].get('arrivalCityCode'),
                                date=req_segments[0].get('departureDate') + '_' + req_segments[1].get('departureDate'),
                                cabin=req_data.get('cabin'))
                            redis_helper.set_data_in_redis(cache_key,
                                                           Response.newRes(ResponseCode.SUCCESS,
                                                                           {'flights': flights}).to_json())
                    else:
                        # 往返-返程
                        flights = parser.parse_inter_flights(res_json.get('data'), 3, 1)
                        cache_key = 'flight_inter_round_back_{dep_city}_{arr_city}_{date}_{cabin}_{airline}_{go_flight_deptime}_{go_flight_arrtime}'.format(
                            dep_city=req_segments[0].get('departureAirportCode').upper() if req_segments[0].get(
                                'departureAirportCode') is not None else req_segments[0].get('departureCityCode'),
                            arr_city=req_segments[0].get('arrivalAirportCode').upper() if req_segments[0].get(
                                'arrivalAirportCode') is not None else req_segments[0].get('arrivalCityCode'),
                            date=req_segments[0].get('departureDate') + '_' + req_segments[1].get('departureDate'),
                            cabin=req_data.get('cabin'), airline=flights[0].get('go_flight').get('airline'),
                            go_flight_deptime=flights[0].get('go_flight').get('dep_time'),
                            go_flight_arrtime=flights[0].get('go_flight').get('arr_time'))
                        redis_helper.set_data_in_redis(cache_key,
                                                       Response.newRes(ResponseCode.SUCCESS,
                                                                       {'flights': flights}).to_json())
            else:
                if inter_go_url in flow.request.url:
                    if len(req_segments) == 1:
                        cache_key = 'flight_inter_oneway_{dep_city}_{arr_city}_{date}_{cabin}'.format(
                            dep_city=req_segments[0].get('departureAirportCode').upper() if req_segments[0].get(
                                'departureAirportCode') is not None else req_segments[0].get('departureCityCode'),
                            arr_city=req_segments[0].get('arrivalAirportCode').upper() if req_segments[0].get(
                                'arrivalAirportCode') is not None else req_segments[0].get('arrivalCityCode'),
                            date=req_segments[0].get('departureDate'), cabin=req_data.get('cabin'))
                        redis_helper.set_data_in_redis(cache_key, Response(flow.response.status_code,
                                                                           flow.response.reason).to_json())
                        logger.error("国际单程航班请求失败: %s  >>>  %s", flow.response.status_code, flow.response.reason)
                    else:
                        cache_key = 'flight_inter_round_go_{dep_city}_{arr_city}_{date}_{cabin}'.format(
                            dep_city=req_segments[0].get('departureAirportCode').upper() if req_segments[0].get(
                                'departureAirportCode') is not None else req_segments[0].get('departureCityCode'),
                            arr_city=req_segments[0].get('arrivalAirportCode').upper() if req_segments[0].get(
                                'arrivalAirportCode') is not None else req_segments[0].get('arrivalCityCode'),
                            date=req_segments[0].get('departureDate') + '_' + req_segments[1].get('departureDate'),
                            cabin=req_data.get('cabin'))
                        redis_helper.set_data_in_redis(cache_key,
                                                       Response(flow.response.status_code,
                                                                flow.response.reason).to_json())
                        logger.error("国际去程航班请求失败: %s  >>>  %s", flow.response.status_code, flow.response.reason)
                else:
                    # cache_key = 'flight_inter_round_back_{dep_city}_{arr_city}_{date}_{cabin}'.format(
                    #     dep_city=req_segments[0].get('departureAirportCode').upper() if req_segments[0].get(
                    #         'departureAirportCode') is not None else req_segments[0].get('departureCityCode'),
                    #     arr_city=req_segments[0].get('arrivalAirportCode').upper() if req_segments[0].get(
                    #         'arrivalAirportCode') is not None else req_segments[0].get('arrivalCityCode'),
                    #     date=req_segments[0].get('departureDate') + '_' + req_segments[1].get('departureDate'),
                    #     cabin=req_data.get('cabin'))
                    # redis_helper.set_data_in_redis(cache_key,
                    #                                Response.newRes(flow.response.status_code, flow.response.reason))
                    logger.error("国际返程航班请求失败: %s  >>>  %s", flow.response.status_code, flow.response.reason)
        elif 'https://flights.ctrip.com/international/search/api/penalty/getOrderPenaltyRule' in flow.request.url:
            """
            退改签说明接口
            """
            # 请求提交参数
            req_data = json.loads(str(flow.request.content, encoding='utf-8'))
            req_luggage_visa = req_data.get('luggageVisaKey')
            rule_key = penalty_parser.create_penalty_rule_key(req_luggage_visa)
            logger.error("退改签说明 key >>>  " + rule_key)
            if flow.response.status_code == 200:
                res_json = json.loads(flow.response.text)
                if res_json.get('status') != 0:
                    redis_helper.set_data_in_redis(rule_key, Response(res_json.get('status'),
                                                                      res_json.get('msg')).to_json())
                    logger.error("获取退改签说明失败: %s  >>>  %s", res_json.get('status'), res_json.get('msg'))
                else:
                    # 有效期三天
                    redis_helper.set_data_expire_in_redis(rule_key, Response.newRes(ResponseCode.SUCCESS, {
                        'rules': penalty_parser.parse_penalty_rule(res_json.get('data').get('dataList'))}).to_json(),
                                                          259200)
                pass
            else:
                redis_helper.set_data_in_redis(rule_key,
                                               Response(flow.response.status_code,
                                                        flow.response.reason).to_json())
                logger.error("获取退改签说明失败: %s  >>>  %s", flow.response.status_code, flow.response.reason)
