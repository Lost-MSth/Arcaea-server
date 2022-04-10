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


class Sql():

    @staticmethod
    def select(c, table_name, target_column=[], query=None):
        # 执行查询单句sql语句，返回fetchall数据
        # 使用准确查询，且在单表内

        sql = 'select '
        sql_dict = {}
        if len(target_column) >= 2:
            sql += target_column[0]
            for i in range(1, len(target_column)):
                sql += ',' + target_column[i]
            sql += ' from ' + table_name
        elif len(target_column) == 1:
            sql += target_column[0] + ' from ' + table_name
        else:
            sql += '* from ' + table_name

        where_field = []
        where_value = []
        if query:
            for i in query.query:
                where_field.append(i)
                where_value.append(query.query[i])

        if where_field and where_value:
            sql += ' where '
            sql += where_field[0] + '=:' + where_field[0]
            sql_dict[where_field[0]] = where_value[0]
            if len(where_field) >= 2:
                for i in range(1, len(where_field)):
                    sql_dict[where_field[i]] = where_value[i]
                    sql += ' and ' + where_field[i] + '=:' + where_field[i]

        if query and query.sort:
            sql += ' order by ' + \
                query.sort[0]['column'] + ' ' + query.sort[0]['order']
            for i in range(1, len(query.sort)):
                sql += ', ' + query.sort[i]['column'] + \
                    ' ' + query.sort[i]['order']

        if query and query.limit >= 0:
            sql += ' limit :limit offset :offset'
            sql_dict['limit'] = query.limit
            sql_dict['offset'] = query.offset

        c.execute(sql, sql_dict)

        return c.fetchall()
