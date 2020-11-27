import os
import sqlite3
import time


def int2b(x):
    # int与布尔值转换
    if x is None or x == 0:
        return False
    else:
        return True


def get_table_info(c, table_name):
    # 得到表结构，返回主键列表和字段名列表
    pk = []
    name = []

    c.execute('''pragma table_info ("'''+table_name+'''")''')
    x = c.fetchall()
    if x:
        for i in x:
            name.append(i[1])
            if i[5] != 0:
                pk.append(i[1])

    return pk, name


def get_sql_select_table(table_name, get_field, where_field=[], where_value=[]):
    # sql语句拼接，select ... from ... where ...
    sql = 'select '
    sql_dict = {}
    if len(get_field) >= 2:
        sql += get_field[0]
        for i in range(1, len(get_field)):
            sql += ',' + get_field[i]
        sql += ' from ' + table_name
    elif len(get_field) == 1:
        sql += get_field[0] + ' from ' + table_name
    else:
        sql += '* from ' + table_name

    if where_field and where_value:
        sql += ' where '
        sql += where_field[0] + '=:' + where_field[0]
        sql_dict[where_field[0]] = where_value[0]
        if len(where_field) >= 1:
            for i in range(1, len(where_field)):
                sql_dict[where_field[i]] = where_value[i]
                sql += ' and ' + where_field[i] + '=:' + where_field[i]

    sql += ' order by rowid'
    return sql, sql_dict


def get_sql_insert_table(table_name, field, value):
    # sql语句拼接，insert into ...(...) values(...)
    sql = 'insert into ' + table_name + '('
    sql_dict = {}
    sql2 = ''
    if len(field) >= 2:
        sql += field[0]
        sql2 += ':' + field[0]
        sql_dict[field[0]] = value[0]
        for i in range(1, len(field)):
            sql += ',' + field[i]
            sql2 += ', :' + field[i]
            sql_dict[field[i]] = value[i]

        sql += ') values('

    elif len(field) == 1:
        sql += field[0] + ') values('
        sql2 += ':' + field[0]
        sql_dict[field[0]] = value[0]

    else:
        return 'error', {}

    sql += sql2 + ')'

    return sql, sql_dict


def update_one_table(c1, c2, table_name):
    # 从c1向c2更新数据表，c2中存在的信息不变
    c1.execute(
        '''select * from sqlite_master where type = 'table' and name = :a''', {'a': table_name})
    c2.execute(
        '''select * from sqlite_master where type = 'table' and name = :a''', {'a': table_name})
    if not c1.fetchone() or not c2.fetchone():
        return 'error'

    db1_pk, db1_name = get_table_info(c1, table_name)
    db2_pk, db2_name = get_table_info(c2, table_name)
    if db1_pk != db2_pk:
        return 'error'

    field = []
    for i in db1_name:
        if i in db2_name:
            field.append(i)

    sql, sql_dict = get_sql_select_table(table_name, db1_pk)
    c1.execute(sql)
    x = c1.fetchall()
    sql, sql_dict = get_sql_select_table(table_name, field)
    c1.execute(sql)
    y = c1.fetchall()
    if x:
        for i in range(0, len(x)):
            sql, sql_dict = get_sql_select_table(
                table_name, [], db1_pk, list(x[i]))
            sql = 'select exists(' + sql + ')'
            c2.execute(sql, sql_dict)

            if c2.fetchone() == (0,):
                sql, sql_dict = get_sql_insert_table(
                    table_name, field, list(y[i]))
                c2.execute(sql, sql_dict)

    return None


def update_user_char(c):
    # 用character数据更新user_char
    c.execute('''select * from character''')
    x = c.fetchall()
    c.execute('''select user_id from user''')
    y = c.fetchall()
    if x and y:
        for j in y:
            for i in x:
                c.execute('''delete from user_char where user_id=:a and character_id=:b''', {
                          'a': j[0], 'b': i[0]})
                c.execute('''insert into user_char values(:a,:b,:c,:d,:e,:f,:g,:h,:i,:j,:k,:l,:m,:n,:o)''', {
                    'a': j[0], 'b': i[0], 'c': i[2], 'd': i[3], 'e': i[4], 'f': i[5], 'g': i[6], 'h': i[7], 'i': i[8], 'j': i[9], 'k': i[10], 'l': i[11], 'm': i[12], 'n': i[14], 'o': i[15]})


def update_database():
    # 将old数据库不存在数据加入到新数据库上，并删除old数据库
    # 对于arcaea_datebase.db，更新best_score，friend，recent30，user，user_world, user_item并用character数据更新user_char
    # 对于arcsong.db，更新songs
    if os.path.isfile("database/old_arcaea_database.db") and os.path.isfile("database/arcaea_database.db"):
        conn1 = sqlite3.connect('./database/old_arcaea_database.db')
        c1 = conn1.cursor()
        conn2 = sqlite3.connect('./database/arcaea_database.db')
        c2 = conn2.cursor()

        update_one_table(c1, c2, 'user')
        update_one_table(c1, c2, 'friend')
        update_one_table(c1, c2, 'best_score')
        update_one_table(c1, c2, 'recent30')
        update_one_table(c1, c2, 'user_world')
        update_one_table(c1, c2, 'user_item')

        update_user_char(c2)

        conn1.commit()
        conn1.close()
        conn2.commit()
        conn2.close()
        os.remove('database/old_arcaea_database.db')

    # songs
    if os.path.isfile("database/old_arcsong.db") and os.path.isfile("database/arcsong.db"):
        conn1 = sqlite3.connect('./database/old_arcsong.db')
        c1 = conn1.cursor()
        conn2 = sqlite3.connect('./database/arcsong.db')
        c2 = conn2.cursor()

        update_one_table(c1, c2, 'songs')

        conn1.commit()
        conn1.close()
        conn2.commit()
        conn2.close()
        os.remove('database/old_arcsong.db')


def unlock_all_user_item(c):
    # 解锁所有用户购买

    c.execute('''select user_id from user''')
    x = c.fetchall()
    c.execute('''select item_id, type from item''')
    y = c.fetchall()
    c.execute('''delete from user_item''')
    if x and y:
        for i in x:
            for j in y:
                c.execute('''insert into user_item values(:a,:b,:c)''', {
                    'a': i[0], 'b': j[0], 'c': j[1]})

    return


def unlock_user_item(c, user_id):
    # 解锁用户购买

    c.execute('''select item_id, type from item''')
    y = c.fetchall()

    for j in y:
        c.execute('''select exists(select * from user_item where user_id=:a and item_id=:b and type=:c)''', {
            'a': user_id, 'b': j[0], 'c': j[1]})
        if c.fetchone() == (0,):
            c.execute('''insert into user_item values(:a,:b,:c)''', {
                'a': user_id, 'b': j[0], 'c': j[1]})

    return


def get_all_item():
    # 所有购买数据查询
    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    c.execute('''select * from item''')
    x = c.fetchall()
    re = []
    if x:
        for i in x:
            discount_from = None
            discount_to = None

            if i[5] and i[5] >= 0:
                discount_from = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(int(i[5])/1000))
            if i[6] and i[6] >= 0:
                discount_to = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(int(i[6])//1000))

            re.append({'item_id': i[0],
                       'type': i[1],
                       'is_available': int2b(i[2]),
                       'price': i[3],
                       'orig_price': i[4],
                       'discount_from': discount_from,
                       'discount_to': discount_to
                       })

    conn.commit()
    conn.close()
    return re
