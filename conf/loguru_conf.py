# -*- coding:utf-8 -*-
"""
    :author: Albert Li
    :time: 2019/11/13 17:57
"""

import os

from loguru import logger


def init(module="app"):
    """初始化日志配置"""
    # 日志文件的存储目录
    if module == "app":
        log_dir = os.getcwd() + "/logs"
        logger.add(
            log_dir + "/file_{time}.log",  # 日志所在路径
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} [ {level} ] {file}:{function}:{line} ===>  {message}",  # 日志信息格式
            level="INFO",  # 日志级别
            rotation="00:00",  # 每天00:00时，创建一个新日志文件
            retention="10 days",  # 日志文件存在超过 10 天自动清除
            encoding="utf-8",  # 设置编码格式为 utf-8，否则中文日志会乱码
        )
    elif module == "proxy":
        proxy_log_dir = os.getcwd() + "/proxy_logs"
        logger.add(
            proxy_log_dir + "/proxy_{time}.log",  # 日志所在路径
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} [ {level} ] {file}:{function}:{line} ===>  {message}",  # 日志信息格式
            level="INFO",  # 日志级别
            rotation="00:00",  # 每天00:00时，创建一个新日志文件
            retention="10 days",  # 日志文件存在超过 10 天自动清除
            encoding="utf-8",  # 设置编码格式为 utf-8，否则中文日志会乱码
        )
