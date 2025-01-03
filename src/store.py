import json
import logging

import redis
from retry import retry


class Storage:

    def __init__(self, host="localhost", port=6379, timeout=3):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.server = None

    def connect(self):
        self.server = redis.Redis(
            host=self.host,
            port=self.port,
            socket_connect_timeout=self.timeout,
            socket_timeout=self.timeout,
            decode_responses=True,
        )

    def set(self, key, value, expires=None):
        try:
            return self.server.set(key, value, ex=expires)
        except redis.exceptions.TimeoutError:
            raise TimeoutError
        except redis.exceptions.ConnectionError as error:
            logging.info(error)
            raise ConnectionError

    def get(self, key):
        try:
            value = self.server.get(key)
            if value is not None:
                try:
                    return json.loads(value)
                except json.decoder.JSONDecodeError:
                    return value.decode()
        except redis.exceptions.TimeoutError:
            raise TimeoutError
        except redis.exceptions.ConnectionError:
            raise ConnectionError


class Store:
    max_retries = 5

    def __init__(self, storage):
        self.storage = storage

    def cache_get(self, key):
        return self.storage.get(key)

    def cache_set(self, key, value, expires=None):
        self.storage.set(key, value, expires)

    @retry(tries=max_retries)
    def set(self, key, value):
        return self.storage.set(key, value)

    @retry(tries=max_retries)
    def get(self, key, use_cache_if_error=True):
        if use_cache_if_error:
            try:
                return self.storage.get(key)
            except (TimeoutError, ConnectionError):
                return self.cache_get(key)
        else:
            return self.storage.get(key)
