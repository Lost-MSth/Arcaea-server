import sqlite3
import traceback

from flask import current_app

from .constant import Constant
from .error import ArcError, InputError


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
        self.conn = sqlite3.connect(self.file_path, timeout=10)
        self.c = self.conn.cursor()
        return self.c

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        flag = True
        if exc_type is not None:
            if issubclass(exc_type, ArcError):
                flag = False
            else:
                if self.conn:
                    self.conn.rollback()

                current_app.logger.error(
                    traceback.format_exception(exc_type, exc_val, exc_tb))

        if self.conn:
            self.conn.commit()
            self.conn.close()

        return flag


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

    def from_dict(self, d: dict) -> 'Query':
        self.set_value(d.get('limit', -1), d.get('offset', 0),
                       d.get('query', {}), d.get('fuzzy_query', {}), d.get('sort', []))
        return self


class Sql:
    '''
        数据库增查删改类
    '''

    def __init__(self, c=None) -> None:
        self.c = c

    @staticmethod
    def get_select_sql(table_name: str, target_column: list = [], query: 'Query' = None):
        '''拼接单表内行查询单句sql语句，返回语句和参数列表'''
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
            return sql, sql_list

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

        return sql, sql_list

    @staticmethod
    def get_insert_sql(table_name: str, key: list = [], value_len: int = None, insert_type: str = None) -> str:
        '''拼接insert语句，请注意只返回sql语句，insert_type为replace或ignore'''
        insert_type = 'replace' if insert_type in [
            'replace', 'R', 'r', 'REPLACE'] else 'ignore'
        return ('insert into ' if insert_type is None else 'insert or ' + insert_type + ' into ') + table_name + ('(' + ','.join(key) + ')' if key else '') + ' values(' + ','.join(['?'] * (len(key) if value_len is None else value_len)) + ')'

    @staticmethod
    def get_delete_sql(table_name: str, query: 'Query' = None):
        '''拼接删除语句，query中只有query(where =)会被处理'''
        sql = 'delete from ' + table_name
        sql_list = []

        if query is not None and query.query:
            sql += ' where '
            where_key = []
            for i in query.query:
                where_key.append(i)
                sql_list.append(query.query[i])
            sql += where_key[0] + '=?'

            if len(where_key) >= 1:
                for i in range(1, len(where_key)):
                    sql += ' and ' + where_key[i] + '=?'

        return sql, sql_list

    def select(self, table_name: str, target_column: list = [], query: 'Query' = None) -> list:
        '''单表内行select单句sql语句，返回fetchall数据'''
        sql, sql_list = self.get_select_sql(table_name, target_column, query)
        self.c.execute(sql, sql_list)
        return self.c.fetchall()

    def select_exists(self, table_name: str, target_column: list = [], query: 'Query' = None) -> bool:
        '''单表内行select exists单句sql语句，返回bool值'''
        sql, sql_list = self.get_select_sql(table_name, target_column, query)
        self.c.execute('select exists(' + sql + ')', sql_list)
        return self.c.fetchone() == (1,)

    def insert(self, table_name: str, key: list, value: tuple, insert_type: str = None) -> None:
        '''单行插入或覆盖插入，key传[]则为全部列，insert_type为replace或ignore'''
        self.c.execute(self.get_insert_sql(
            table_name, key, len(value), insert_type), value)

    def insert_many(self, table_name: str, key: list, value_list: list, insert_type: str = None) -> None:
        '''多行插入或覆盖插入，key传[]则为全部列，insert_type为replace或ignore'''
        if not value_list:
            return
        self.c.executemany(self.get_insert_sql(
            table_name, key, len(value_list[0]), insert_type), value_list)

    def delete(self, table_name: str, query: 'Query' = None) -> None:
        '''删除，query中只有query(where =)会被处理'''
        sql, sql_list = self.get_delete_sql(table_name, query)
        self.c.execute(sql, sql_list)

    def get_table_info(self, table_name: str):
        '''得到表结构，返回主键列表和字段名列表'''
        pk = []
        name = []

        self.c.execute('''pragma table_info ("%s")''' % table_name)  # 这里无法参数化
        x = self.c.fetchall()
        if x:
            for i in x:
                name.append(i[1])
                if i[5] != 0:
                    pk.append(i[1])

        return pk, name


class DatabaseMigrator:

    def __init__(self, c1_path: str, c2_path: str) -> None:
        self.c1_path = c1_path
        self.c2_path = c2_path

    @staticmethod
    def update_one_table(c1, c2, table_name: str) -> bool:
        '''从c1向c2更新数据表，c1中存在的信息不变，即c2中的冲突信息会被覆盖'''
        c1.execute(
            '''select * from sqlite_master where type = 'table' and name = :a''', {'a': table_name})
        c2.execute(
            '''select * from sqlite_master where type = 'table' and name = :a''', {'a': table_name})
        if not c1.fetchone() or not c2.fetchone():
            return False

        sql1 = Sql(c1)
        sql2 = Sql(c2)
        db1_pk, db1_name = sql1.get_table_info(table_name)
        db2_pk, db2_name = sql2.get_table_info(table_name)
        if db1_pk != db2_pk:
            return False

        sql2.insert_many(table_name, [], sql1.select(
            table_name, list(filter(lambda x: x in db2_name, db1_name))), insert_type='replace')

        return True

    @staticmethod
    def update_user_char_full(c) -> None:
        '''用character表数据更新user_char_full'''
        c.execute('''select character_id, max_level, is_uncapped from character''')
        x = c.fetchall()
        c.execute('''select user_id from user''')
        y = c.fetchall()
        c.execute('''delete from user_char_full''')
        for i in x:
            exp = 25000 if i[1] == 30 else 10000
            c.executemany('''insert into user_char_full values(?,?,?,?,?,?)''', [
                          (j[0], i[0], i[1], exp, i[2], 0) for j in y])

    @staticmethod
    def update_user_epilogue(c) -> None:
        '''给用户添加epilogue包'''
        c.execute('''select user_id from user''')
        Sql(c).insert_many('user_item', [], [(i[0], 'epilogue', 'pack', 1)
                                             for i in c.fetchall()], insert_type='ignore')

    def update_database(self) -> None:
        '''
        将c1数据库不存在数据加入或覆盖到c2数据库上
        对于c2，更新一些表，并用character数据更新user_char_full
        '''
        with Connect(self.c2_path) as c2:
            with Connect(self.c1_path) as c1:
                [self.update_one_table(c1, c2, i)
                 for i in Constant.DATABASE_MIGRATE_TABLES]

                if not Constant.UPDATE_WITH_NEW_CHARACTER_DATA:
                    self.update_one_table(c1, c2, 'character')

            self.update_user_char_full(c2)  # 更新user_char_full
            self.update_user_epilogue(c2)  # 更新user的epilogue
