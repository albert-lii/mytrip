# -*- coding:utf-8 -*-
"""
    :author: Albert Li
    :time: 2019/11/12 17:42 
"""
import time

import redis

# 获取一个 redis 连接池
redis_pool = redis.ConnectionPool(host="localhost", port=6379, db=0, password="123456")


class RedisClient(object):
    def __init__(self):
        # 从连接池中获取一个连接
        self._client = redis.StrictRedis(connection_pool=redis_pool)

    def get_data(self, key: str):
        """根据 key 获取数据"""
        return self._client.get(key)

    def set_data(self, key: str, value):
        """缓存数据"""
        self._client.set(key, value)

    def set_data_with_expire(self, key: str, value, expire: int = 300):
        """缓存数据并设置数据过期时间，过期时间默认为 5 分钟"""
        self._client.set(key, value)
        self._client.expire(key, expire)

    def check_data_by_cycle(self, key: str, cycle_time: int = 20):
        """循环检查数据，默认循环检查时间为 20s"""
        data = self._client.get_data(key)
        if data is None:
            # 总的循环检查时间
            total_time = cycle_time
            # 间隔时间
            interval_time = 0.25
            # 每隔 0.25s 去检查一次是否数据库中有值，如果循环时间结束后没有值，则返回 None
            while total_time > 0:
                time.sleep(0.25)
                data = self._client.get_data(key)
                if data is not None:
                    return data
                else:
                    total_time -= interval_time
            return None
        else:
            return data
