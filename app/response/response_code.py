# -*- coding:utf-8 -*-
"""
    :author: Albert Li
    :time: 2019/11/13 10:30 
"""
import enum


class ResponseCode(enum.Enum):
    SUCCESS = 0, "请求成功"
    FAIL = -1, "请求失败"

    # 4 开头的错误码，分配给 api 参数校验错误
    ERROR_MISS_PARAMETER = 4001, "缺少参数"
    ERROR_INVALID_PARAMETER = 4002, "无效参数"
    # 5 开头的错误码，分配给后台业务错误
    ERROR_NO_RESOURCE_FOUND = 5001, "未找到资源"
    ERROR_TIME_OUT = 5002, "资源查询超时"

    def __init__(self, code: int, desc: str):
        self.__code = code
        self.__desc = desc
        self.__msg = desc

    @property
    def code(self):
        return self.__code

    @property
    def desc(self):
        return self.__desc
