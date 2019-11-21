# -*- coding:utf-8 -*-
"""
    机票数据结构
    :author: Albert Li
    :time: 2019/11/20 10:28
"""


class Route(object):
    """
    航段信息模型
    """

    def __init__(
        self,
        index: int,
        airline: str = None,
        airline_code: str = None,
        flight_no: str = None,
        plane_model: str = None,
        duration: str = None,
        dep_day: str = None,
        dep_time: str = None,
        dep_airport: str = None,
        dep_city: str = None,
        arr_day: str = None,
        arr_time: str = None,
        arr_airport: str = None,
        arr_city: str = None,
    ):
        self.index = index  # 航班序号
        self.airline = airline  # 航空公司
        self.airline_code = airline_code  # 航空公司
        self.flight_no = flight_no  # 航班号
        self.plane_model = plane_model  # 飞机型号
        self.duration = duration  # 飞行时间
        self.dep_date = dep_day  # 起飞日期
        self.dep_day = dep_day  # 起飞日期
        self.dep_time = dep_time  # 起飞时间
        self.dep_airport = dep_airport  # 起飞机场
        self.dep_city = dep_city  # 起飞城市
        self.arr_date = arr_day  # 到达日期
        self.arr_day = arr_day  # 到达日期
        self.arr_time = arr_time  # 到达时间
        self.arr_airport = arr_airport  # 到达机场
        self.arr_city = arr_city  # 到达城市

    def to_dict(self):
        return self.__dict__


class Product(object):
    """
    产品信息模型
    """

    def __init__(
        self,
        source: str,
        source_desc: str,
        index: int,
        position: int,
        cabin_class: str = None,
        booking_class: str = None,
        booking_class_desc: str = None,
        adult_price: str = None,
        adult_tax: str = None,
        notes: list = None,
        penalty_rule: dict = None,
        trip_type: int = 1,
    ):
        self.source = source
        self.source_desc = source_desc
        self.index = index  # 产品的位置
        self.position = position  # 在 ERP 中的位置
        self.cabin_class = cabin_class  # 舱型
        self.booking_class = booking_class  # 预订的舱位
        self.booking_class_desc = booking_class_desc  # 预订的舱位描述
        self.adult_price = adult_price  # 成人价
        self.adult_tax = adult_tax  # 成人税
        if adult_tax is None:
            self.adult_tax = 0
            self.price = int(adult_price)
        else:
            self.adult_tax = adult_tax
            self.price = int(adult_price) + int(adult_tax)  # 显示价格，含税
        self.penalty_rule = penalty_rule  # 退改签字典
        self.notes = notes  # 备注
        self.trip_type = trip_type

    def to_dict(self):
        return self.__dict__


class Flight(object):
    """航班信息模型"""

    def __init__(
        self,
        from_time: str = None,
        from_airport: str = None,
        to_time: str = None,
        to_airport: str = None,
        duration: str = None,
        routes: list = None,
        products: list = None,
    ):
        self.from_time = from_time  # 起飞时间
        self.from_airport = from_airport  # 起飞机场
        self.to_time = to_time  # 到达时间
        self.to_airport = to_airport  # 到达机场
        self.duration = duration  # 行程总时间
        self.routes = routes  # 航段列表
        self.products = products  # 当前查询的舱位产品列表

    def to_dict(self):
        return self.__dict__


def to_result(flight: Flight = None) -> dict:
    """
    结构最终返回的数据结构
    :param go_flight: 去程
    :param back_flight: 返程
    :param source: 来源
    :param source_desc: 来源描述
    :return:
    """
    return {
        "flights": go_flight if go_flight is not None else None,
        "back_flight": back_flight if back_flight is not None else None,
    }
