# -*-coding:utf-8 -*-

from flask_mail import Message
from . import mail, app
from flask import render_template
from .config import ADMINS
from .decorators import async


@async
def send_async_email(app, msg):
    """异步发送提醒邮件"""
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    """发送邮件"""
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    # Thread(target=send_async_email,args=[app, msg]).start()
    send_async_email(app, msg)


def follower_notification(followed, follower):
    send_email(
        "[microblog] %s is now following your!" % follower.nickname,
        ADMINS[0],
        [followed.email],
        render_template("follower_email.txt",
                        user=followed, follower=follower),
        render_template("follower_email.txt",
                        user=followed, follower=follower))
