# -*-coding:utf-8 -*-

from . import db
from hashlib import md5

# 定义关联表，表内关联
followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
                     )


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    posts = db.relationship('Post', backref='author', lazy='dynamic')  # 1对多的1， author字段在Post对象中隐藏存在
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime)
    followed = db.relationship('User',
                               secondary=followers,  # 关联表
                               primaryjoin=(followers.c.follower_id == id),  # 自己的id
                               secondaryjoin=(followers.c.followed_id == id),  # 对方的id
                               backref=db.backref('followers', lazy='dynamic'),  # ？？？
                               lazy='dynamic')  # 多对多，使用关联表进行表内关联

    def follow(self, user):  # 添加关注
        if not self.is_following(user):
            self.followed.append(user)
            return self

    def unfollow(self, user):  # 删除关注
        if self.is_following(user):
            self.followed.remove(user)
            return self

    def is_following(self, user):  # 判断关注状态
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):  # 查找被关注的人的posts
        return Post.query.join(followers, (followers.c.followed_id == Post.user_id)).filter(
            followers.c.follower_id == self.id).order_by(Post.timestamp.desc())

    def is_authenticated(self):  # 可以直接集成flask_login中的UserMixIn
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):  # 被user_loader调用
        # try:
        #     return unicode(self.id)  # python 2
        # except NameError:
        return str(self.id)  # python 3

    def __repr__(self):  # 打印状态
        return '<User %r>' % self.nickname  # ？？%r?

    def avatar(self, size):
        """gravatar提供的头像服务"""
        return 'http://www.gravatar.com/avatar/' + md5(self.email).hexdigest() + '?d=mm&s=' + str(size)

    @staticmethod
    def make_unique_nickname(nickname):
        """生成独一无二的nickname"""
        if User.query.filter_by(nickname=nickname).first() is None:
            return nickname
        version = 2
        while True:
            new_nickname = nickname + str(version)
            if User.query.filter_by(nickname=new_nickname).first() is None:
                break
            version += 1
        return new_nickname


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 为什么是user.id而不是User.id？？？

    def __repr__(self):
        return '<Post %r>' % self.body
