# PROJECT
├── conf.py                 # 路由<br>
├── image_matcher.py        # 图片比较api<br>
├── image_process.py        # web服务主程序<br>
├── index.html              # web页面<br>
├── logs                    # 日志<br>
│   ├── image_process.lock  # 进程pid<br>
│   └── image_process.log   # 日志<br>
├── README.md<br>
├── settings.py             # 配置文件<br>
├── temp                    # 临时文件存放<br>
├── utils.py                # 工具<br>
└── view.py                 # 视图<br>

# INSTALL

## Linux

    1 安装PHASH C语言包 http://www.phash.org/
    2 下载安装phash ./configure, make && make install（注意将动态链接库加入环境变量中export LD_LIBRARY_PATH=/usr/local/lib)
    3 将项目克隆到本地目录
    4 进入项目目录
    5 执行python image_process --host 127.0.0.1 --port 4567

# SETTINGS and CONF
```
    setting.py:
        LOG_LEVEL = 'DEBUG'     # 日志级别
        LOG_STDOUT = True       # 是否标准输出
        LOG_JSON = False        # 是否输出json格式
        LOG_DIR = "logs"        # 日志保存目录
        LOG_MAX_BYTES = '10MB'  # 日志最大字节数
        LOG_BACKUPS = 5         # 日志备份个数
    conf.py:
        app.get("/", index)     # route回调函数
```

# START
- 访问http://127.0.0.1:4567
- 上传图片压缩包，服务器对图片进行处理，回显相似图片，不同组使用不同颜色标记
- 将鼠标悬浮在图片之上，可显示图片所属分类
- 双击图片进行删除， 右击撤销上一步删除操作
- 点击pass，对下页图片进行去图处理
- 点击stop,下载处理完毕的图片压缩包

# API
### 上传压缩包
    METHOD：post
    url:http://127.0.0.1:4567/api/upload
    输入要素
    file:要上传的zip格式压缩包
    输出要素
    json:{"success":True/False}
### 获取压缩包中做对比的指定组数的数据
    METHOD:get
    url:http://127.0.0.1:4567/api/pass
    输入要素:
    count:要获取的组数
    输出要素
    json:{"groups":
    [
        [path1, path2, path3 ...],
        [path4, path5, path6 ...]
    ], "datas":
    [
        "I"+md5(path1):{"price": 1234, "features": "...", ...},
        "I"+md5(path2):{"price": 1234, "features": "...", ...},
        ...
    ]
    }
### 删除指定图片
    METHOD:get
    url:http://127.0.0.1:4567/api/remove/src
    输入要素:
    src:图片的src
    输出要素
    json:{"success":True/False}
### 撤销删除之前图片
    METHOD:get
    url:http://127.0.0.1:4567/api/reset
    输入要素:图片的src
    输出要素
    json:{"success":True/False}
### 停止对比并生成下载包
    METHOD:get
    url:http://127.0.0.1:4567/api/stop
    输入要素：无
    输出要素：
    json:{"finished": true, "filename": "xxxx"}
### 下载处理完毕的压缩包
    METHOD:get
    url:http://127.0.0.1:4567/api/download/压缩包名字(不带扩展名)
    输入要素:压缩包名字(不带扩展名) 以url的方式
    输出要素：要下载的文件
