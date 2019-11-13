# -*- coding:utf-8 -*-
"""
    :author: Albert Li
    :time: 2019/11/13 12:09 
"""
from flask import jsonify

from app.response.response_code import ResponseCode


def make_response_ok(data=None):
    """请求成功返回的结果"""
    resp = {'code': ResponseCode.SUCCESS.code, 'msg': ResponseCode.SUCCESS.desc, 'data': data}
    return jsonify(resp)


def make_response_error(resp_code: ResponseCode, msg=None):
    """请求失败返回的结果"""
    resp = {'code': resp_code.code, 'msg': msg if msg is not None else resp_code.desc, 'data': None}
    return jsonify(resp)


def make_flights_response_ok(flights=None):
    """机票列表请求成功返回的结果"""
    return make_response_ok({'flights': flights})
