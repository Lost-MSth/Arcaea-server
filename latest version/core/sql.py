import sqlite3
import traceback
from certifi import where

from flask import current_app

from .constant import Constant
from .error import InputError


class Connect:
    # 数据库连接类，上下文管理

    def __init__(self, file_path=Constant.SQLITE_DATABASE_PATH):
        """
            数据库连接，默认连接arcaea_database.db\ 
            接受：文件路径\ 
            返回：sqlite3连接操作对象
        """
        self.file_path = file_path

    def __enter__(self):
        self.conn = sqlite3.connect(self.file_path)
        self.c = self.conn.cursor()
        return self.c

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is not None:
            if self.conn:
                self.conn.rollback()

            current_app.logger.error(
                traceback.format_exception(exc_type, exc_val, exc_tb))

        if self.conn:
            self.conn.commit()
            self.conn.close()

        return True


class Query:
    '''查询参数类'''

    def __init__(self, query_able: list = None, quzzy_query_able: list = None, sort_able: list = None) -> None:
        self.query_able: list = query_able
        self.quzzy_query_able: list = quzzy_query_able
        self.sort_able: list = sort_able

        self.__limit: int = -1
        self.__offset: int = 0
        self.__query: dict = {}  # {'name': 'admin'}
        self.__fuzzy_query: dict = {}  # {'name': 'dmi'}
        # [{'column': 'user_id', 'order': 'ASC'}, ...]
        self.__sort: list = []

    @property
    def limit(self) -> int:
        return self.__limit

    @limit.setter
    def limit(self, limit: int) -> None:
        if not isinstance(limit, int):
            raise InputError(api_error_code=-101)
        self.__limit = limit

    @property
    def offset(self) -> int:
        return self.__offset

    @offset.setter
    def offset(self, offset: int) -> None:
        if not isinstance(offset, int):
            raise InputError(api_error_code=-101)
        self.__offset = offset

    @property
    def query(self) -> dict:
        return self.__query

    @query.setter
    def query(self, query: dict) -> None:
        self.__query = {}
        self.query_append(query)

    def query_append(self, query: dict) -> None:
        if not isinstance(query, dict):
            raise InputError(api_error_code=-101)
        if self.query_able is not None and query and not set(query).issubset(set(self.query_able)):
            raise InputError(api_error_code=-102)
        if not self.__query:
            self.__query = query
        else:
            self.__query.update(query)

    @property
    def fuzzy_query(self) -> dict:
        return self.__fuzzy_query

    @fuzzy_query.setter
    def fuzzy_query(self, fuzzy_query: dict) -> None:
        self.__fuzzy_query = {}
        self.fuzzy_query_append(fuzzy_query)

    def fuzzy_query_append(self, fuzzy_query: dict) -> None:
        if not isinstance(fuzzy_query, dict):
            raise InputError(api_error_code=-101)
        if self.quzzy_query_able is not None and fuzzy_query and not set(fuzzy_query).issubset(set(self.quzzy_query_able)):
            raise InputError(api_error_code=-102)
        if not self.__fuzzy_query:
            self.__fuzzy_query = fuzzy_query
        else:
            self.__fuzzy_query.update(fuzzy_query)

    @property
    def sort(self) -> list:
        return self.__sort

    @sort.setter
    def sort(self, sort: list) -> None:
        if not isinstance(sort, list):
            raise InputError(api_error_code=-101)
        if self.sort_able is not None and sort:
            for x in sort:
                if not isinstance(x, dict):
                    raise InputError(api_error_code=-101)
                if 'column' not in x or x['column'] not in self.sort_able:
                    raise InputError(api_error_code=-103)
                if 'order' not in x:
                    x['order'] = 'ASC'
                else:
                    if x['order'] not in ['ASC', 'DESC']:
                        raise InputError(api_error_code=-104)
        self.__sort = sort

    def set_value(self, limit=-1, offset=0, query={}, fuzzy_query={}, sort=[]) -> None:
        self.limit = limit
        self.offset = offset
        self.query = query
        self.fuzzy_query = fuzzy_query
        self.sort = sort

    def from_data(self, d: dict) -> 'Query':
        self.set_value(d.get('limit', -1), d.get('offset', 0),
                       d.get('query', {}), d.get('fuzzy_query', {}), d.get('sort', []))
        return self


class Sql:
    '''
        数据库增查删改类
    '''

    def __init__(self, c=None) -> None:
        self.c = c

    def select(self, table_name: str, target_column: 'list' = [], query: 'Query' = None) -> list:
        '''单表内行查询单句sql语句，返回fetchall数据'''

        sql = 'select '
        sql_list = []
        if len(target_column) >= 2:
            sql += target_column[0]
            for i in range(1, len(target_column)):
                sql += ',' + target_column[i]
            sql += ' from ' + table_name
        elif len(target_column) == 1:
            sql += target_column[0] + ' from ' + table_name
        else:
            sql += '* from ' + table_name

        if query is None:
            self.c.execute(sql)
            return self.c.fetchall()

        where_key = []
        where_like_key = []
        for i in query.query:
            where_key.append(i)
            sql_list.append(query.query[i])

        for i in query.fuzzy_query:
            where_like_key.append(i)
            sql_list.append('%' + query.fuzzy_query[i] + '%')

        if where_key or where_like_key:
            sql += ' where '
            if where_key:
                sql += where_key[0] + '=?'
                if len(where_key) >= 2:
                    for i in range(1, len(where_key)):
                        sql += ' and ' + where_key[i] + '=?'
                if where_like_key:
                    for i in where_like_key:
                        sql += ' and ' + i + ' like ?'
            else:
                sql += where_like_key[0] + ' like ?'

                if len(where_like_key) >= 2:
                    for i in range(1, len(where_key)):
                        sql += ' and ' + where_key[i] + ' like ?'

        if query.sort:
            sql += ' order by ' + \
                query.sort[0]['column'] + ' ' + query.sort[0]['order']
            for i in range(1, len(query.sort)):
                sql += ', ' + query.sort[i]['column'] + \
                    ' ' + query.sort[i]['order']

        if query.limit >= 0:
            sql += ' limit ? offset ?'
            sql_list.append(query.limit)
            sql_list.append(query.offset)

        self.c.execute(sql, sql_list)
        return self.c.fetchall()
