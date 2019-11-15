# -*- coding:utf-8 -*-
"""
    :author: Albert Li
    :time: 2019/11/13 12:09 
"""
import json

from flask import jsonify

from app.response.response_code import ResponseCode


def make_response_ok_as_dict(data=None):
    """请求成功返回的结果"""
    resp = {
        "code": ResponseCode.SUCCESS.code,
        "msg": ResponseCode.SUCCESS.desc,
        "data": data,
    }
    return resp


def make_response_ok(data=None):
    """请求成功返回的结果"""
    return jsonify(make_response_ok_as_dict(data))


def make_response_ok_as_str(data=None):
    """请求成功返回的字符串格式结果"""
    resp = {
        "code": ResponseCode.SUCCESS.code,
        "msg": ResponseCode.SUCCESS.desc,
        "data": data,
    }
    return json.dumps(resp)


def make_response_error_as_dict(resp_code: ResponseCode, msg=None):
    """请求失败返回的结果"""
    resp = {
        "code": resp_code.code,
        "msg": msg if msg is not None else resp_code.desc,
        "data": None,
    }
    return resp


def make_response_error(resp_code: ResponseCode, msg=None):
    """请求失败返回的结果"""
    return jsonify(make_response_error_as_dict(resp_code, msg))


def make_response_error_as_str(resp_code: ResponseCode, msg=None):
    """请求失败返回的字符串根式结果"""
    resp = {
        "code": resp_code.code,
        "msg": msg if msg is not None else resp_code.desc,
        "data": None,
    }
    return json.dumps(resp)


def make_flights_response_ok(flights=None):
    """航班列表请求成功返回的结果"""
    return make_response_ok({"flights": flights})


def make_flights_response_ok_as_dict(flights=None):
    """航班列表请求成功返回的结果"""
    return make_response_ok_as_dict({"flights": flights})


def make_flights_response_ok_as_str(flights=None):
    """航班列表请求成功返回的字符串格式结果"""
    return make_response_ok_as_str({"flights": flights})


def make_flight_response_ok(flights=None):
    """根据航班号请求航班信息成功返回的结果"""
    return make_response_ok({"flight": flights})


def make_penalty_rule_response_ok(penalty_rules=None):
    """航班退改签说明请求成功返回的结果"""
    return make_response_ok({"penalty_rules": penalty_rules})


def make_penalty_rule_response_ok_as_str(penalty_rules=None):
    """航班退改签说明请求成功返回的字符串格式结果"""
    return make_response_ok_as_str({"penalty_rules": penalty_rules})
