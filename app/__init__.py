# -*- coding:utf-8 -*-
"""
    :author: Albert Li
    :time: 2019/11/12 15:47 
"""
from flask import Flask
from app.flight import flight_api_bp


def create_app():
    """ 创建 flask app
    :return: app
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.register_blueprint(flight_api_bp, url_prefix="/api/flight")
    app.config["JSON_SORT_KEYS"] = False
    return app
