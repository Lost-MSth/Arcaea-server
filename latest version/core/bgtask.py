from atexit import register
from concurrent.futures import ThreadPoolExecutor

from .constant import Constant
from .sql import Connect


class BGTask:
    executor = ThreadPoolExecutor(max_workers=1)

    def __init__(self, func, *args, **kwargs):
        self.future = self.executor.submit(func, *args, **kwargs)

    def result(self):
        return self.future.result()

    def cancel(self) -> bool:
        return self.future.cancel()

    def done(self) -> bool:
        return self.future.done()

    @staticmethod
    def shutdown(wait: bool = True):
        BGTask.executor.shutdown(wait)


@register
def atexit():
    BGTask.shutdown()


def logdb_execute_func(sql, *args, **kwargs):
    with Connect(Constant.SQLITE_LOG_DATABASE_PATH) as c:
        c.execute(sql, *args, **kwargs)


def logdb_execute_many_func(sql, *args, **kwargs):
    with Connect(Constant.SQLITE_LOG_DATABASE_PATH) as c:
        c.executemany(sql, *args, **kwargs)


def logdb_execute(sql: str, *args, **kwargs):
    '''异步执行SQL，日志库写入，注意不会直接返回结果'''
    return BGTask(logdb_execute_func, sql, *args, **kwargs)


def logdb_execute_many(sql: str, *args, **kwargs):
    '''异步批量执行SQL，日志库写入，注意不会直接返回结果'''
    return BGTask(logdb_execute_many_func, sql, *args, **kwargs)
