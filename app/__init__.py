# -*-coding:utf-8 -*-

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_openid import OpenID
import os
from flask_mail import Mail
from .momentjs import momentjs
from flask_babel import Babel
from .config import basedir

app = Flask(__name__)
app.config.from_object('config')
app.jinja_env.globals['momentjs'] = momentjs  # 日期转换，在前端转换
db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'  # 指定登录的视图
oid = OpenID(app, os.path.join(basedir, 'tmp'))
mail = Mail(app)  # 邮件服务
babel = Babel(app)  # 国际化与本地化

if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler('tmp/microblog.log', 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('microblog startup')
from . import views, models  # 将app对象直接传给views，然后通过from . import 对其进行执行
