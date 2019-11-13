# -*- coding:utf-8 -*-
# @Time: 2019/10/15 11:00 
# @Author: albertlii

import os

from loguru import logger


def init():
    """
    初始化日志配置
    """
    # 日志文件的存储目录
    log_dir = os.getcwd() + '/logs'
    logger.add(log_dir + '/file_{time}.log',  # 日志所在路径
               format='{time:YYYY-MM-DD HH:mm:ss.SSS} [ {level} ] {file}:{function}:{line} ===>  {message}',  # 日志信息格式
               filter='',
               level='DEBUG',  # 日志级别
               rotation='00:00',  # 每天00:00时，创建一个新日志文件
               encoding='utf-8'  # 设置编码格式为 utf-8，否则中文日志会乱码
               )
