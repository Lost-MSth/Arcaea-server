import sqlite3
from flask import current_app
import traceback


class Connect():
    # 数据库连接类，上下文管理

    def __init__(self, file_path='./database/arcaea_database.db'):
        """
        数据库连接，默认连接arcaea_database.db
        接受：文件路径
        返回：sqlite3连接操作对象
        """
        self.file_path = file_path

    def __enter__(self):
        self.conn = sqlite3.connect(self.file_path)
        self.c = self.conn.cursor()
        return self.c

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.commit()
            self.conn.close()

        if exc_type is not None:
            current_app.logger.error(
                traceback.format_exception(exc_type, exc_val, exc_tb))

        return True
