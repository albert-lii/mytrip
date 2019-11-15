# -*- coding:utf-8 -*-
"""
    :author: Albert Li
    :time: 2019/11/13 14:24 
"""
from flask import Blueprint

flight_api_bp = Blueprint("flight_api", __name__)

from . import api
