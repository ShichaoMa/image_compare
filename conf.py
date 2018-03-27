# -*- coding:utf-8 -*-
from view import *


app.post(["/api/upload", "/upload"], upload)
app.get("/", index)
app.get(["/api/pass", "/api/pass/<count:int:>", "/pass/<count:int:>",], passes)
app.get(["/remove/<name:path:>", "/api/remove/<name:path:>"], remove)
app.get(["/reset/<path:path:>", "/api/reset/<path:path:>"], reset)
app.get("%s/temp/<name:path:>"%pwd, temp_file)
app.get(["/stop", "/api/stop"], stop)
app.get(["/download/<name::>", "/api/download/<name::>"], download)