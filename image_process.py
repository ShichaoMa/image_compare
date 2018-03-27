#!/home/longen/.pyenv/shims/python
# -*- coding:utf-8 -*-
import json
import builtins
from redis import Redis
from argparse import ArgumentParser
from bottle import Bottle, HTTPResponse, JSONPlugin, HTTPError, _e, response
from log_to_kafka import Logger
from utils import CustomWSGIRefServer, ForkingWSGIServer


class CustomJSONPlugin(JSONPlugin):
    def apply(self, callback, route):
        dumps = self.json_dumps
        if not dumps: return callback

        def wrapper(*a, **ka):
            try:
                rv = callback(*a, **ka)
            except HTTPError:
                rv = _e()

            if isinstance(rv, dict):
                # Attempt to serialize, raises exception on failure
                try:
                    json_response = dumps(rv)
                except UnicodeDecodeError:
                    json_response = dumps(rv, encoding="gbk")
                # Set content type only if serialization succesful
                response.content_type = 'application/json'
                return json_response
            elif isinstance(rv, HTTPResponse) and isinstance(rv.body, dict):
                rv.body = dumps(rv.body)
                rv.content_type = 'application/json'
            return rv

        return wrapper


class RedisHash(object):

    def __init__(self, redis_conn, primary_key):
        self.redis_conn = redis_conn
        self.primary_key = primary_key
        self.clear()

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.redis_conn.hset(self.primary_key, key, json.dumps(value))

    def get(self, key, default=None):
        k = self.redis_conn.hget(self.primary_key, key)
        return json.loads(k) if k else default

    def setdefault(self, key, default=None):
        d = self.get(key, default)
        if d == default:
            self[key] = default
        return d

    def __str__(self):
        return str(self.redis_conn.hgetall(self.primary_key))

    def clear(self):
        self.redis_conn.delete(self.primary_key)

    __repr__ = __str__


class RedisDict(dict):

    def __init__(self, redis_conn, redis_key):
        self.redis_conn = redis_conn
        self.redis_key = redis_key
        super(RedisDict, self).__init__()

    def __getitem__(self, key):
        return self.get(key)

    def get(self, k, d=None):
        value = self.redis_conn.hget(self.redis_key, k)
        return json.loads(value) if value else d

    def __setitem__(self, key, value):
        self.redis_conn.hset(self.redis_key, key, json.dumps(value))
        self.redis_conn.expire(self.redis_key, 60*60)

    def __delitem__(self, key):
        self.redis_conn.hdel(self.redis_key, key)

    def __contains__(self, key):
        return self.redis_conn.hexists(self.redis_key, key)


class ImageProcess(Logger):

    app = Bottle()

    def __init__(self, settings):
        self.name = "image_process"
        super(ImageProcess, self).__init__(settings)
        self.app.uninstall("json")
        self.app.install(CustomJSONPlugin())
        self.redis_conn = Redis(self.settings.get("REDIS_HOST"), self.settings.get("REDIS_PORT"))
        self.del_dict = RedisDict(self.redis_conn, "del_pic_dict")
        self.data_dict = RedisDict(self.redis_conn, "data_pic_dict")

    @classmethod
    def parse_args(cls):
        parser = ArgumentParser()
        parser.add_argument("-s", "--settings", dest="settings", default="settings.py")
        parser.add_argument("--host", dest="host", required=True)
        parser.add_argument("-p", "--port", dest="port", type=int, default=4567)
        return parser.parse_args()

    @classmethod
    def run(cls):
        args = cls.parse_args()
        IP = cls(args.settings)
        IP.set_logger()
        builtins.__dict__["app"] = IP
        IP.logger.debug("put app to builtin. ")
        IP.logger.debug("route paths. ")
        import conf
        server = CustomWSGIRefServer(
            app=IP.app,
            host=args.host,
            port=args.port,
            server_class=ForkingWSGIServer)
        IP.app.run(server=server, host=args.host, port=args.port)

    def route(self, path, method, callback):
        return self.app.route(path, method, callback)

    def get(self, path, callback):
        return self.route(path, "GET", callback)

    def post(self, path, callback):
        return self.route(path, "POST", callback)


if __name__ == "__main__":
    ImageProcess.run()
