# -*- coding:utf-8 -*-
"""
    :author: Albert Li
    :time: 2019/11/13 14:40 
"""
import json


def parse_inter_flights(data, trip_type, round_query_type) -> list:
    """解析国际航班列表
    :param data: 网络请求响应数据
    :param trip_type: 1: 单程  2: 往返 - 去程  3: 往返 - 返程
    :return: 国际航班列表
    """
    if data is None:
        return None

    def minute2hour(minutes):
        """将分钟转为小时+分钟模式，如：1小时35分钟"""
        if minutes < 60:
            return minutes + "分钟"
        else:
            hour = minutes // 60
            left_minute = minutes % 60
            return "{hour}小时{min}分钟".format(hour=hour, min=left_minute) if left_minute > 0 else "{hour}小时".format(
                hour=hour)

    def parse_seat_class(json_str):
        """
        解析 seat class
        """
        if json_str is None:
            return None, None
        info = json.loads(json_str)
        routes = info['criteria']['FlightInfoList']
        seat_classes = []
        for item in routes:
            if trip_type == 1 or trip_type == 2:
                if item['SegmentNo'] == 1:
                    seat_classes.append(item['SeatClass'])
            else:
                if item['SegmentNo'] == 2:
                    seat_classes.append(item['SeatClass'])
        return "/".join(seat for seat in seat_classes)

    def parse_flight(segment, prices):
        """航班信息解析
        :param segment: 去程/返程
        :param prices 产品价格信息
        :return: 航班信息
        """
        routes = []  # 行程中的所有航班
        for item in segment.get('flightList'):
            route = {
                'airline': item.get('marketAirlineName'),  # 航空公司
                'airline_code': item.get('marketAirlineCode'),  # 航空公司代码
                'flight_no': item.get('flightNo'),  # 航班号
                'plane_model': item.get('aircraftName'),  # 飞机型号
                'duration': minute2hour(item.get('duration')),
                'duration_minutes': item.get('duration'),  # 飞行时间
                'dep_date': item.get('departureDateTime')[0:10],  # 起飞日期
                'dep_time': item.get('departureDateTime')[11:16],  # 起飞时间
                'dep_airport': item.get('departureAirportName'),  # 起飞机场
                'dep_airport_code': item.get('departureAirportCode'),  # 起飞机场三字码
                'dep_airport_terminal': item.get('departureTerminal'),  # 起飞机场航站楼信息
                'dep_city': item.get('departureCityName'),  # 起飞城市
                'dep_city_code': item.get('departureCityCode'),  # 起飞城市三字码
                'dep_country': item.get('departureCountryName'),  # 起飞国家
                'arr_date': item.get('arrivalDateTime')[0:10],  # 到达日期
                'arr_time': item.get('arrivalDateTime')[11:16],  # 到达时间
                'arr_airport': item.get('arrivalAirportName'),  # 到达机场
                'arr_airport_code': item.get('arrivalAirportCode'),  # 到达机场三字码
                'arr_airport_terminal': item.get('arrivalTerminal'),  # 到达机场航站楼信息
                'arr_city': item.get('arrivalCityName'),  # 到达城市
                'arr_city_code': item.get('arrivalCityCode'),  # 到达城市三字码
                'arr_country': item.get('arrivalCountryName'),  # 到达国家
            }
            routes.append(route)
        products = []
        for index, item in enumerate(prices):
            product = {
                'source': 'ctrip',
                'source_desc': '携程',
                'index': index,  # 本产品在产品列表中的位置
                'position': index,  # ERP 要用的排序
                'cabin_class': item.get('itineraryCabin'),  # 舱型
                'booking_class': parse_seat_class(item.get('luggageVisaKey')),  # 预定舱位
                'booking_class_desc': None,  # 预定舱位描述
                'adult_price': item.get('adultPrice'),  # 成人价
                'adult_tax': item.get('adultTax'),  # 成人税,
                'child_price': item.get('childPrice'),  # 儿童价
                'child_tax': item.get('childTax'),  # 儿童税
                'infant_price': item.get('infantPrice'),  # 婴儿价
                'infant_tax': item.get('infantTax'),  # 婴儿税
                'price': item.get('adultPrice') + item.get('adultTax'),  # 显示价格，含税
                'ticket_count': item.get('ticketCount'),  # 剩余票数
                'notes': item.get('purchaseNotes'),  # 备注
                'rule': None,
                'round_query_type': round_query_type
            }
            products.append(product)
            if trip_type == 2 and index == 0:
                break
        flight = {
            'airline': segment.get('airlineName'),  # 航空公司
            'airline_code': segment.get('airlineCode'),  # 航空公司代码
            'from_date': routes[0]['dep_date'],  # 出发日期
            'from_time': routes[0]['dep_time'],  # 出发时间
            'from_airport': routes[0]['dep_airport'],  # 出发机场
            'from_airport_code': routes[0]['dep_airport_code'],  # 出发机场三字码
            'from_airport_terminal': routes[0]['dep_airport_terminal'],  # 出发机场航站楼信息
            'from_city': routes[0]['dep_city'],  # 出发城市
            'from_city_code': routes[0]['dep_city_code'],  # 出发城市三字码
            'to_date': routes[-1]['arr_date'],  # 到达日期
            'to_time': routes[-1]['arr_time'],  # 到达时间
            'to_airport': routes[-1]['arr_airport'],  # 到达机场
            'to_airport_code': routes[-1]['arr_airport_code'],  # 到达机场三字码
            'to_airport_terminal': routes[-1]['arr_airport_terminal'],  # 到达机场航站楼信息
            'to_city': routes[-1]['arr_city'],  # 到达城市
            'to_city_code': routes[-1]['arr_city_code'],  # 到达城市三字码
            'cross_days': segment.get('crossDays'),
            'duration': minute2hour(segment.get('duration')),
            'duration_minutes': segment.get('duration'),  # 行程总时间
            'routes': routes,  # 行程的航班列表
            'products': products  # 舱位产品列表
        }
        return flight

    trips = []
    itineraries = data.get('flightItineraryList')
    for itinerary in itineraries:
        segments = itinerary.get('flightSegments')
        prices = itinerary.get('priceList')
        if len(segments) == 1:
            # 单程/去程
            trip = {'source': 'ctrip', 'source_desc': '携程', 'flights': parse_flight(segments[0], prices)}
        else:
            # 返程
            trip = {'source': 'ctrip', 'source_desc': '携程', 'flights': parse_flight(segments[1], prices)}
        trips.append(trip)
    return trips
