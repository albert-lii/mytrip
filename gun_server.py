# -*- coding:utf-8 -*-
"""
    :author: Albert Li
    :time: 2019/11/13 15:45
"""

import os
import multiprocessing

path_of_current_file = os.path.abspath(__file__)  # 获取当前该配置文件的绝对路径
path_of_current_dir = os.path.split(path_of_current_file)[0]
chdir = path_of_current_dir  # 项目的根目录，加载应用程序之前将chdir目录切换到指定的工作目录

bind = "0.0.0.0:8081"  # 绑定ip和端口号
backlog = 512  # 最大挂起的客户端连接数（即等待服务的客户端数），超过此数量将导致客户端在尝试连接时出错，一般设置范围 64-2048
workers = multiprocessing.cpu_count() * 2 + 1  # worker进程数，会自动分配到你机器上的多CPU，完成简单并行化
worker_class = "gevent"  # worker进程的工作模式
worker_connections = 500  # 最大并发的客户端连接数，默认1000
# threads = 2  # 指定每个进程开启的线程数，此设置仅影响gthread工作模式
timeout = 60  # 请求超时时间（秒），超过此时间后，worker将被杀死，被重新创建一个worker

spew = False  # 打印服务器执行过的每一条语句，默认False。此选择为原子性的，即要么全部打印，要么全部不打印
reload = True  # 每当代码发生更改时，work将会自动重启，适用于开发阶段，默认为False
daemon = True  # 是否以守护进程启动，默认False
debug = True

pidfile = "%s/gunicorn.pid" % path_of_current_dir  # 设置pid文件的文件名，如果不设置将不会创建pid文件
accesslog = (
    "%s/logs/gunicorn_access.log" % path_of_current_dir
)  # 访问日志的路径，注意首先需要存在logs文件夹，gunicorn才可自动创建log文件，否则报错
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
)  # 访问日志的格式
loglevel = "info"  # 错误日志输出等级，访问日志的输出等级无法设置
errorlog = "%s/logs/gunicorn_error.log" % path_of_current_dir  # 错误日志的路径，可与访问日志相同
