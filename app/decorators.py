# -*-coding:utf-8 -*-


from threading import Thread


def async(f):
    """异步多线程装饰器"""
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper
