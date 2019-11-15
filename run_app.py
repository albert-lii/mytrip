# -*- coding:utf-8 -*-
"""
    :author: Albert Li
    :time: 2019/11/12 15:47 
"""

from app import create_app
from conf import loguru_conf

app = create_app()
loguru_conf.init()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
