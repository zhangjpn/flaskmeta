# -*-coding:utf-8 -*-

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
app02 = Flask(__name__)
app02.config.from_object('app02.default_config')  # 配置文件
# app02.config.from_envvar('MYSETTINGS')  # 基于环境变量覆盖配置
db = SQLAlchemy(app=app02)
lm = LoginManager(app02)
lm.login_view = 'login'
lm.session_protection = 'strong'
if not app02.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler('microblog.log', 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app02.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app02.logger.addHandler(file_handler)
    app02.logger.info('microblog startup')

from . import views