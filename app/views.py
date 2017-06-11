# -*-coding:utf-8 -*-
import datetime
from flask import render_template, flash, redirect, url_for, session, request, g
from flask_login import login_user, logout_user, current_user, login_required
from . import app, lm, oid, db, babel
from .forms import LoginForm, EditForm, PostForm
from .models import User, Post
from .config import POSTS_PER_PAGE, LANGUAGES, DATABASE_QUERY_TIMEOUT
from .emails import follower_notification
from flask_sqlalchemy import get_debug_queries


@babel.localeselector  # 语言国际化与本地化
def get_locale():
    return request.accept_languages.best_match(LANGUAGES.keys())


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler  # ？？
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # flash('Login requested for OpenID="' + form.openid.data + '", remember_me='
        #     + str(form.remember_me.data))
        session['remember_me'] = form.remember_me.data  # 创建会话，session类似于current_user，也是一个普通的对象
        return oid.try_login(form.openid.data, ask_for=['nickname', 'email'])  # 发送到openid服务商尝试登录，返回什么？？
        # return redirect('/login')
    return render_template('login.html', title='Sign In',
                           form=form,
                           provider=app.config['OPENID_PROVIDERS'])


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/index/<int:page>', methods=['GET', 'POST'])
@login_required
def index(page=1):
    form = PostForm()
    if form.validate_on_submit():  # 如果是提交表单，则写入表单，重定向到首页
        post = Post(body=form.post.data, timestamp=datetime.datetime.utcnow(), author=g.user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    # posts = g.user.followed_posts().all()
    # posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False).items  # 分页
    posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False)  # 直接返回分页对象而不是列表项
    return render_template('index.html',
                           title='Home',
                           form=form,
                           posts=posts)


@app.route('/logout')
def logout():
    """登出"""
    logout_user()
    return redirect(url_for('index'))


@lm.user_loader
def load_user(id):  # id是什么？？
    return User.query.get(int(id))  # 这个被装饰的函数所返回的值就是current_user所指向的对象


@app.before_request
def before_request():
    g.user = current_user  # 设置本地代理，也就是将当前用户对象赋值给g.user，current_user是如何被指向登录用户的？>>lm.user_loader
    if g.user.is_authenticated():
        g.user.last_seen = datetime.datetime.utcnow()  # 更新用户最后登录的时间
        db.session.add(g.user)  # 写入数据库
        db.session.commit()


@app.after_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= DATABASE_QUERY_TIMEOUT:
            app.logger.warning("SLOW QUERY: %s\nParameters: %s\nDuration: %fs\nContext: %s\n" % (
                query.statement, query.parameters, query.duration, query.context))
    return response


@oid.after_login
def after_login(resp):
    """resp：从OpenID提供商返回的信息"""
    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        return redirect(url_for('login'))
    user = User.query.filter_by(email=resp.email).first()
    if user is None:  #
        nickname = resp.nickname
        if nickname is None or nickname == "":
            nickname = resp.email.split('@')[0]
        nickname = User.make_unique_nickname(nickname)
        user = User(nickname=nickname, email=resp.email)
        db.session.add(user)
        db.session.commit()
        # make the user follow himself/herself
        db.session.add(user.follow(user))
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember=remember_me)  # 对用户的登录状态进行登录
    return redirect(request.args.get('next') or url_for('index'))  # ？？


@app.route('/user/<nickname>')
@app.route('/user/<nickname>/<int:page>')
@login_required
def user(nickname, page=1):
    """展示用户页面，page=1展示posts的页"""
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User ' + nickname + ' not found.')
        return redirect(url_for('index'))
    posts = user.posts.pageinate(page, POSTS_PER_PAGE, False)
    return render_template('user.html',
                           user=user,
                           posts=posts)


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():  # 如果接收的表单有效，则编辑用户信息
        g.user.nickname = form.nickname.data  # g.user为当前用户
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    return render_template('edit.html', form=form)


@app.route('/follow/<nickname>')  # 添加关注
@login_required
def follow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    if user == g.user:  # user是要关注的人，g.user是当前用户
        flash('You can\'t follow yourself!')
        return redirect(url_for('user', nickname=nickname))
    u = g.user.follow(user)  # 添加关注之后返回自身，是内存对象
    if u is None:
        flash('Cannot follow ' + nickname + '.')
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)  # 更新当前用户的资料
    db.session.commit()
    flash('You are now following ' + nickname + '!')
    follower_notification(user, g.user)  # 发送关注通知，异步线程
    return redirect(url_for('user', nickname=nickname))


@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
    """取消关注某人"""
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t unfollow yourself!')
        return redirect(url_for('user', nickname=nickname))
    u = g.user.unfollow(user)
    if u is None:
        flash('Cannot unfollow ' + nickname + '.')
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You have stopped following ' + nickname + '.')
    return redirect(url_for('user', nickname=nickname))  # 返回已经取消关注的对方


@app.errorhandler(404)
def internal_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
