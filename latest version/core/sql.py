import os
import sqlite3
import traceback
from atexit import register

from .config_manager import Config
from .constant import ARCAEA_LOG_DATBASE_VERSION, Constant
from .error import ArcError, InputError


class Connect:
    # 数据库连接类，上下文管理
    logger = None

    def __init__(self, file_path: str = Constant.SQLITE_DATABASE_PATH, in_memory: bool = False, logger=None) -> None:
        """
            数据库连接，默认连接arcaea_database.db
            接受：文件路径
            返回：sqlite3连接操作对象
        """
        self.file_path = file_path
        self.in_memory: bool = in_memory
        if logger is not None:
            self.logger = logger

        self.conn: sqlite3.Connection = None
        self.c: sqlite3.Cursor = None

    def __enter__(self) -> sqlite3.Cursor:
        if self.in_memory:
            self.conn = sqlite3.connect(
                'file:arc_tmp?mode=memory&cache=shared', uri=True, timeout=10)
        else:
            self.conn = sqlite3.connect(self.file_path, timeout=10)
        self.c = self.conn.cursor()
        return self.c

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        flag = True
        if exc_type is not None:
            if issubclass(exc_type, ArcError):
                flag = False
            else:
                self.conn.rollback()

                self.logger.error(
                    traceback.format_exception(exc_type, exc_val, exc_tb))

        self.conn.commit()
        self.conn.close()

        return flag


class Query:
    '''查询参数类'''

    def __init__(self, query_able: list = None, fuzzy_query_able: list = None, sort_able: list = None) -> None:
        self.query_able: list = query_able  # None表示不限制
        self.fuzzy_query_able: list = fuzzy_query_able  # None表示不限制
        self.sort_able: list = sort_able

        self.__limit: int = -1
        self.__offset: int = 0

        # {'name': 'admin'} or {'name': ['admin', 'user']}
        self.__query: dict = {}
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
        if self.fuzzy_query_able is not None and fuzzy_query and not set(fuzzy_query).issubset(set(self.fuzzy_query_able)):
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

    def set_value(self, limit=-1, offset=0, query=None, fuzzy_query=None, sort=None) -> None:
        self.limit = limit
        self.offset = offset
        self.query = query if query is not None else {}
        self.fuzzy_query = fuzzy_query if fuzzy_query is not None else {}
        self.sort = sort if sort is not None else []

    def from_dict(self, d: dict) -> 'Query':
        self.set_value(d.get('limit', -1), d.get('offset', 0),
                       d.get('query', {}), d.get('fuzzy_query', {}), d.get('sort', []))
        return self

    def from_args(self, query: dict, limit: int = -1, offset: int = 0, sort: list = None, fuzzy_query: dict = None) -> 'Query':
        self.set_value(limit, offset, query, fuzzy_query, sort)
        return self


class Sql:
    '''
        数据库增查删改类
    '''

    def __init__(self, c=None) -> None:
        self.c = c

    @staticmethod
    def get_select_sql(table_name: str, target_column: list = None, query: 'Query' = None):
        '''拼接单表内行查询单句sql语句，返回语句和参数列表'''
        sql_list = []
        if not target_column:
            sql = f'select * from {table_name}'
        else:
            sql = f"select {', '.join(target_column)} from {table_name}"

        if query is None:
            return sql, sql_list

        where_key = []
        for k, v in query.query.items():
            if isinstance(v, list):
                where_key.append(f"{k} in ({','.join(['?'] * len(v))})")
                sql_list.extend(v)
            else:
                where_key.append(f'{k}=?')
                sql_list.append(v)

        for k, v in query.fuzzy_query.items():
            where_key.append(f'{k} like ?')
            sql_list.append(f'%{v}%')

        if where_key:
            sql += ' where '
            sql += ' and '.join(where_key)

        if query.sort:
            sql += ' order by ' + \
                ', '.join([x['column'] + ' ' + x['order'] for x in query.sort])

        if query.limit >= 0:
            sql += ' limit ? offset ?'
            sql_list.append(query.limit)
            sql_list.append(query.offset)

        return sql, sql_list

    @staticmethod
    def get_insert_sql(table_name: str, key: list = None, value_len: int = None, insert_type: str = None) -> str:
        '''拼接insert语句，请注意只返回sql语句，insert_type为replace或ignore'''
        if key is None:
            key = []
        insert_type = 'replace' if insert_type in [
            'replace', 'R', 'r', 'REPLACE'] else 'ignore'
        return ('insert into ' if insert_type is None else 'insert or ' + insert_type + ' into ') + table_name + ('(' + ','.join(key) + ')' if key else '') + ' values(' + ','.join(['?'] * (len(key) if value_len is None else value_len)) + ')'

    @staticmethod
    def get_update_sql(table_name: str, d: dict = None, query: 'Query' = None):
        if not d:
            return None
        sql_list = []
        sql = f"update {table_name} set {','.join([f'{k}=?' for k in d.keys()])}"
        sql_list.extend(d.values())

        if query is None:
            return sql, sql_list

        where_key = []
        for k, v in query.query.items():
            if isinstance(v, list):
                where_key.append(f"{k} in ({','.join(['?'] * len(v))})")
                sql_list.extend(v)
            else:
                where_key.append(f'{k}=?')
                sql_list.append(v)

        for k, v in query.fuzzy_query.items():
            where_key.append(f'{k} like ?')
            sql_list.append(f'%{v}%')

        if where_key:
            sql += ' where '
            sql += ' and '.join(where_key)

        return sql, sql_list

    @staticmethod
    def get_update_many_sql(table_name: str, key: list = None, where_key: list = None) -> str:
        '''拼接update语句，这里不用Query类，也不用字典，请注意只返回sql语句'''
        if not key or not where_key:
            return None
        return f"update {table_name} set {','.join([f'{k}=?' for k in key])} where {' and '.join([f'{k}=?' for k in where_key])}"

    @staticmethod
    def get_delete_sql(table_name: str, query: 'Query' = None):
        '''拼接删除语句，query中只有query和fuzzy_query会被处理'''
        sql = f'delete from {table_name}'

        if query is None:
            return sql, []

        sql_list = []
        where_key = []
        for k, v in query.query.items():
            if isinstance(v, list):
                where_key.append(f"{k} in ({','.join(['?'] * len(v))})")
                sql_list.extend(v)
            else:
                where_key.append(f'{k}=?')
                sql_list.append(v)

        for k, v in query.fuzzy_query.items():
            where_key.append(f'{k} like ?')
            sql_list.append(f'%{v}%')

        if where_key:
            sql += ' where '
            sql += ' and '.join(where_key)

        return sql, sql_list

    def select(self, table_name: str, target_column: list = None, query: 'Query' = None) -> list:
        '''单表内行select单句sql语句，返回fetchall数据'''
        sql, sql_list = self.get_select_sql(table_name, target_column, query)
        self.c.execute(sql, sql_list)
        return self.c.fetchall()

    def select_exists(self, table_name: str, target_column: list = None, query: 'Query' = None) -> bool:
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

    def update(self, table_name: str, d: dict, query: 'Query' = None) -> None:
        '''单表内行update单句sql语句'''
        if not d:
            return
        sql, sql_list = self.get_update_sql(table_name, d, query)
        self.c.execute(sql, sql_list)

    def update_many(self, table_name: str, key: list, value_list: list, where_key: list, where_value_list: list) -> None:
        '''单表内行update多句sql语句，这里不用Query类，也不用字典，要求值list长度一致，有点像insert_many'''
        if not key or not value_list or not where_key or not where_value_list or not len(key) == len(value_list[0]) or not len(where_key) == len(where_value_list[0]) or not len(value_list) == len(where_value_list):
            raise ValueError
        self.c.executemany(self.get_update_many_sql(
            table_name, key, where_key), [x + y for x, y in zip(value_list, where_value_list)])

    def delete(self, table_name: str, query: 'Query' = None) -> None:
        '''删除，query中只有query和fuzzy_query会被处理'''
        sql, sql_list = self.get_delete_sql(table_name, query)
        self.c.execute(sql, sql_list)

    def get_table_info(self, table_name: str):
        '''得到表结构，返回主键列表和字段名列表'''
        pk = []
        name = []

        self.c.execute(f'''pragma table_info ("{table_name}")''')  # 这里无法参数化
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

        public_column = list(filter(lambda x: x in db2_name, db1_name))

        sql2.insert_many(table_name, public_column, sql1.select(
            table_name, public_column), insert_type='replace')

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
            c.executemany('''insert into user_char_full values(?,?,?,?,?,?,0)''', [
                          (j[0], i[0], i[1], exp, i[2], 0) for j in y])

    def update_database(self) -> None:
        '''
        将c1数据库不存在数据加入或覆盖到c2数据库上
        对于c2，更新一些表，并用character数据更新user_char_full
        '''
        with Connect(self.c2_path) as c2:
            with Connect(self.c1_path) as c1:
                for i in Constant.DATABASE_MIGRATE_TABLES:
                    self.update_one_table(c1, c2, i)

                if not Constant.UPDATE_WITH_NEW_CHARACTER_DATA:
                    self.update_one_table(c1, c2, 'character')

            self.update_user_char_full(c2)  # 更新user_char_full


class LogDatabaseMigrator:

    def __init__(self, c1_path: str = Config.SQLITE_LOG_DATABASE_PATH) -> None:
        self.c1_path = c1_path
        # self.c2_path = c2_path
        self.init_folder_path = Config.DATABASE_INIT_PATH
        self.c = None

    @property
    def sql_path(self) -> str:
        return os.path.join(self.init_folder_path, 'log_tables.sql')

    def table_update(self) -> None:
        '''直接更新数据库结构'''
        with open(self.sql_path, 'r') as f:
            self.c.executescript(f.read())
        self.c.execute(
            '''insert or replace into cache values("version", :a, -1);''', {'a': ARCAEA_LOG_DATBASE_VERSION})

    def update_database(self) -> None:
        with Connect(self.c1_path) as c:
            self.c = c
            self.table_update()


class MemoryDatabase:
    conn = sqlite3.connect('file:arc_tmp?mode=memory&cache=shared', uri=True)

    def __init__(self):
        self.c = self.conn.cursor()
        self.c.execute('''PRAGMA journal_mode = OFF''')
        self.c.execute('''PRAGMA synchronous = 0''')
        self.c.execute('''create table if not exists download_token(user_id int,
        song_id text,file_name text,token text,time int,primary key(user_id, song_id, file_name));''')
        self.c.execute(
            '''create index if not exists download_token_1 on download_token (song_id, file_name);''')
        self.conn.commit()


@register
def atexit():
    MemoryDatabase.conn.close()
