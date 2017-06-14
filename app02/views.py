# -*-coding:utf-8 -*-
from flask import render_template, redirect,request
from . import app02, lm
from flask_login import login_required, current_user, login_user, logout_user
from .models import User


@lm.user_loader  # 用来从会话中通过user_id寻找到用户对象，在每次验证过程中适用
def user_loader(user_id):
    return User(id=int(user_id), nickname='hello', email='abc@163.com')

@lm.unauthorized_handler  # 自定义登入函数
def unauthorized():
    # do stuff
    return render_template('index.html')
@app02.route('/login', methods=['GET', 'POST'])
def login():
    if request.method != 'GET':
        user = User(id=1, nickname='hello', email='abc@163.com')
        login_user(user)  # 将用户对象赋给current_user
    return redirect('index')


@app02.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()  # 将session的user_id字段清空
    return redirect('index')


@app02.route('/index/')
@login_required
def index():
    return render_template('index.html')


@app02.errorhandler(404)
def internal_error(error):
    return render_template('404.html'), 404


@app02.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500
