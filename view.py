import os
import shutil
import hashlib
import builtins
import traceback

from redis.exceptions import WatchError
from bottle import request, static_file

from utils import *
from image_matcher import web_api

app = builtins.app

pwd = os.path.dirname(__file__)


def passes(count=None):
    app.logger.debug("start request in %s"%passes.__name__)
    try:
        addr = request.remote_addr.replace(".", "_")
        path = request.path
        _lst, csvs = app.data_dict.get(addr, (None, None))
        if _lst:
            lst = _lst[:count] if count else _lst
            app.data_dict[addr] = (_lst[count:] if count else [], csvs)
            if path.startswith("/api"):
                data = map(lambda group:
                           map(lambda path:
                               {
                                   "I%s"%hashlib.md5(path).hexdigest():
                                       dict(zip(csvs.get("p", []), csvs.get(cut_path(path), [])))
                               }, group), lst)
                return {"groups":lst, "datas":data}
            else:
                return {"groups":lst}
        else:
            return {"groups":[], "datas":[]}
    except Exception:
        app.logger.error("error in %s Error:%s" % (passes.__name__, traceback.format_exc()))
        return {"groups":[], "datas":[]}


def remove(name):
    app.logger.debug("start request in %s" % remove.__name__)
    try:
        addr = request.remote_addr.replace(".", "_")
        # app.del_dict.setdefault(addr, {}).\
        #     setdefault(name[:name.rfind("/")], []).\
        #     append(name[name.rfind("/")+1:-4])
        while True:
            with app.redis_conn.pipeline() as pipe:
                try:
                    pipe.watch(app.del_dict.redis_key)  # ---- LOCK
                    pipe.multi()
                    del_dict = app.del_dict.get(addr, {})
                    del_dict.setdefault(name[:name.rfind("/")], []). \
                        append(name[name.rfind("/") + 1:-4])
                    app.del_dict[addr] = del_dict
                    pipe.execute()
                    break
                except WatchError:
                    # watch was changed, another thread just messed with the key
                    app.logger.error("Watch was changed, another thread just messed with the key, try again. ")

        return {"success": True}
    except Exception:
        app.logger.error("error in %s Error:%s" % (remove.__name__, traceback.format_exc()))
        return {"success": False}


def reset(path):
    app.logger.debug("start request in %s" % reset.__name__)
    try:
        addr = request.remote_addr.replace(".", "_")
        #app.del_dict[addr][path[:path.rfind("/")]].remove(path[path.rfind("/")+1:-4])
        while True:
            with app.redis_conn.pipeline() as pipe:
                try:
                    pipe.watch(app.del_dict.redis_key)  # ---- LOCK
                    pipe.multi()
                    del_dict = app.del_dict.get(addr, {})
                    del_dict[path[:path.rfind("/")]].remove(path[path.rfind("/")+1:-4])
                    app.del_dict[addr] = del_dict
                    pipe.execute()
                    break
                except WatchError:
                    # watch was changed, another thread just messed with the key
                    app.logger.error("Watch was changed, another thread just messed with the key, try again. ")
        return {"success":True}
    except Exception:
        app.logger.error("error in %s Error:%s" % (reset.__name__, traceback.format_exc()))
        return {"success": False}


def temp_file(name):
    return static_file(name, "%s/temp"%pwd)


def stop(ad=None):
    app.logger.debug("start request in %s" % stop.__name__)
    try:
        addr = ad or request.remote_addr.replace(".", "_")
        if addr in app.data_dict:
            del app.data_dict[addr]
        if addr in app.del_dict:
            remove_record(app.del_dict[addr])
            del app.del_dict[addr]
        if not ad:
            os.system("cd %s/temp/temp_%s && rm -rf result_%s.zip && zip -rq result_%s.zip ./ " % (pwd, addr, addr, addr))
        return {"finished": True, "filename": "result_%s" % addr}
    except Exception:
        app.logger.error("error in %s Error:%s" % (stop.__name__, traceback.format_exc()))
        return {"finished": False}


def download(name):
    addr = request.remote_addr.replace(".", "_")
    dir = "%s/temp/temp_%s"%(pwd, addr)
    return static_file("%s.zip"%name, dir, download=True)


def index():
    app.logger.debug("start request in %s" % index.__name__)
    try:
        return open("%s/index.html"%pwd).read()
    except Exception:
        app.logger.error("error in %s Error:%s" % (index.__name__, traceback.format_exc()))


def upload():
    app.logger.debug("start request in %s" % upload.__name__)
    try:
        addr = request.remote_addr.replace(".", "_")
        file = request.POST.get("file")
        if not os.path.exists("temp"):
            os.mkdir("temp")

        temp_file_name = "temp_%s.zip" % (addr)
        if os.path.exists("%s/temp/%s" % (pwd, temp_file_name)):
            os.remove("%s/temp/%s" % (pwd, temp_file_name))
        if os.path.exists("%s/temp/%s" % (pwd, temp_file_name[:-4])):
            shutil.rmtree("%s/temp/%s" % (pwd, temp_file_name[:-4]))
        file.save("%s/temp/%s" % (pwd, temp_file_name))
        os.system("unzip -q -O CP936 -o %s/temp/%s  -d %s/temp/%s" % (pwd, temp_file_name, pwd, temp_file_name[:-4]))
        path = ["%s/temp/%s" % (pwd, temp_file_name[:-4])]
        gen = web_api(path)
        csvs = csv_load("%s/temp/%s" % (pwd, temp_file_name[:-4]))
        lst = []
        s = set()
        for i in gen:
            path1 = i[2]
            path2 = i[3]
            if path1 in s and path2 in s:
                continue
            elif path1 not in s and path2 not in s:
                lst.append([path1, path2])
                s.add(path1)
                s.add(path2)
            elif path1 in s and path2 not in s:
                for inner_lst in lst:
                    if path1 in inner_lst:
                        inner_lst.append(path2)
                        s.add(path2)
                        break
            else:
                for inner_lst in lst:
                    if path2 in inner_lst:
                        inner_lst.append(path1)
                        s.add(path1)
                        break

        app.data_dict[addr] = (lst, csvs)
        return {"success":True}
    except Exception:
        app.logger.error("error in %s Error:%s" % (upload.__name__, traceback.format_exc()))
        return {"success": False}
