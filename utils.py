# -*- coding:utf-8 -*-
import os
import csv
import socket

from socketserver import ForkingMixIn
from wsgiref.simple_server import make_server
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer
from bottle import ServerAdapter


class ForkingWSGIServer(ForkingMixIn, WSGIServer):
    pass


class CustomWSGIRefServer(ServerAdapter):
    """
    wsgiref server adapter
    """
    def __init__(self, app, host, port, **options):
        super(CustomWSGIRefServer, self).__init__(host, port, **options)
        self.app = app
        self.server = None

    def run(self, app): # pragma: no cover

        class FixedHandler(WSGIRequestHandler):

            def address_string(self): # Prevent reverse DNS lookups please.
                return self.client_address[0]

            def log_request(*args, **kw):
                if not self.quiet:
                    return WSGIRequestHandler.log_request(*args, **kw)

        handler_cls = self.options.get('handler_class', FixedHandler)
        server_cls = self.options.get('server_class', WSGIServer)

        if ':' in self.host: # Fix wsgiref for IPv6 addresses.
            if getattr(server_cls, 'address_family') == socket.AF_INET:
                class server_cls(server_cls):
                    address_family = socket.AF_INET6
        server_cls.request_queue_size = 500
        self.server = make_server(self.host, self.port, app, server_cls, handler_cls)
        self.server.serve_forever()

    def close(self):
        if self.server:
            self.server.server_close()
        raise KeyboardInterrupt


def remove_record(del_datas):
    for path, names in del_datas.items():
        for name in names:
            os.remove(os.path.join(path, name + ".tbi"))
        csv_path = path + ".csv"
        try:
            csvfile_r = open(csv_path, "r", encoding="gbk", errors="ignore")
        except IOError:
            return
        reader = csv.reader(csvfile_r)
        lst = list(reader)
        csvfile_r.close()
        csvfile_w = open(csv_path, "w", encoding="gbk", errors="ignore")
        writer = csv.writer(csvfile_w)
        for line in lst:
            try:
                if line[28][:-6] not in names:
                    writer.writerow(line)
            except IndexError:
                writer.writerow(line)
        csvfile_w.close()


def csv_load(path):
    paths = [os.path.join(root, p) for root, dirs, files in os.walk(path)
             for p in files if p.endswith("csv")]
    csvs = {}
    for path in paths:
        csvfile = open(path, "r", encoding="gbk", errors="ignore")
        reader = csv.reader(csvfile)
        for line in reader:
            try:
                csvs[line[28][:-6]] = line
            except Exception as e:
                print("Error in csv_load, Error: %s, line %s, path: %s"%(e, line, path))
        csvfile.close()
    return csvs


def cut_path(path):
    return path[path.rfind("/")+1:-4]
