# -*-coding:utf-8 -*-

from wtforms import Form, StringField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length
from .models import User


class LoginForm(Form):
    openid = StringField('openid', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)


class EditForm(Form):
    """用于编辑用户信息"""
    nickname = StringField('nickname', validators=[DataRequired()])
    about_me = TextAreaField('about_me', validators=[Length(min=0, max=140)])

    def validate(self):
        """验证nickname是否合法"""
        if not Form.validate(self):  # ？？？？
            return False
        if self.nickname.data == self.original_nickname:  # ??
            return True
        user = User.query.filter_by(nickname=self.nickname.data).first()
        if user is not None:  # 判断数据库中是否有这个用户名
            self.nickname.errors.append('This nickname is already in use. Please choose another one.')
            return False
        return True


class PostForm(Form):
    """提交post数据"""
    post = StringField('post', validators=[DataRequired()])
