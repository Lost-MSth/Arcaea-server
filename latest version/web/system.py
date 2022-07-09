import os
from core.sql import Connect
import time
import hashlib
from random import Random
from setting import Config


def int2b(x):
    # int与布尔值转换
    if x is None or x == 0:
        return False
    else:
        return True


def random_str(randomlength=10):
    # 随机生成字符串
    s = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    random = Random()
    for _ in range(randomlength):
        s += chars[random.randint(0, length)]
    return s


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


def get_sql_delete_table(table_name, where_field=[], where_value=[]):
    # sql语句拼接，delete from ... where ...
    sql = 'delete from ' + table_name
    sql_dict = {}

    if where_field and where_value:
        sql += ' where '
        sql += where_field[0] + '=:' + where_field[0]
        sql_dict[where_field[0]] = where_value[0]
        if len(where_field) >= 1:
            for i in range(1, len(where_field)):
                sql_dict[where_field[i]] = where_value[i]
                sql += ' and ' + where_field[i] + '=:' + where_field[i]

    return sql, sql_dict


def update_one_table(c1, c2, table_name):
    # 从c1向c2更新数据表，c1中存在的信息不变
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

            if c2.fetchone() == (1,):  # 如果c2里存在，先删除
                sql, sql_dict = get_sql_delete_table(
                    table_name, db1_pk, list(x[i]))
                c2.execute(sql, sql_dict)

            sql, sql_dict = get_sql_insert_table(
                table_name, field, list(y[i]))
            c2.execute(sql, sql_dict)

    return None


def update_user_char(c):
    # 用character数据更新user_char
    c.execute('''select character_id, max_level, is_uncapped from character''')
    x = c.fetchall()
    c.execute('''select user_id from user''')
    y = c.fetchall()
    if x and y:
        for j in y:
            for i in x:
                c.execute('''delete from user_char_full where user_id=:a and character_id=:b''', {
                          'a': j[0], 'b': i[0]})
                exp = 25000 if i[1] == 30 else 10000
                c.execute('''insert into user_char_full values(?,?,?,?,?,?)''',
                          (j[0], i[0], i[1], exp, i[2], 0))


def update_database():
    # 将old数据库不存在数据加入到新数据库上，并删除old数据库
    # 对于arcaea_datebase.db，更新一些表，并用character数据更新user_char_full
    if os.path.isfile("database/old_arcaea_database.db") and os.path.isfile("database/arcaea_database.db"):
        with Connect('./database/old_arcaea_database.db') as c1:
            with Connect() as c2:

                update_one_table(c1, c2, 'user')
                update_one_table(c1, c2, 'friend')
                update_one_table(c1, c2, 'best_score')
                update_one_table(c1, c2, 'recent30')
                update_one_table(c1, c2, 'user_world')
                update_one_table(c1, c2, 'item')
                update_one_table(c1, c2, 'user_item')
                update_one_table(c1, c2, 'purchase')
                update_one_table(c1, c2, 'purchase_item')
                update_one_table(c1, c2, 'user_save')
                update_one_table(c1, c2, 'login')
                update_one_table(c1, c2, 'present')
                update_one_table(c1, c2, 'user_present')
                update_one_table(c1, c2, 'present_item')
                update_one_table(c1, c2, 'redeem')
                update_one_table(c1, c2, 'user_redeem')
                update_one_table(c1, c2, 'redeem_item')
                update_one_table(c1, c2, 'role')
                update_one_table(c1, c2, 'user_role')
                update_one_table(c1, c2, 'power')
                update_one_table(c1, c2, 'role_power')
                update_one_table(c1, c2, 'api_login')
                update_one_table(c1, c2, 'chart')
                update_one_table(c1, c2, 'user_course')
                update_one_table(c1, c2, 'course')
                update_one_table(c1, c2, 'course_item')
                update_one_table(c1, c2, 'course_chart')
                update_one_table(c1, c2, 'course_requirement')

                update_one_table(c1, c2, 'user_char')

                if not Config.UPDATE_WITH_NEW_CHARACTER_DATA:
                    update_one_table(c1, c2, 'character')

                update_user_char(c2)  # 更新user_char_full

        os.remove('database/old_arcaea_database.db')


def unlock_all_user_item(c):
    # 解锁所有用户购买

    c.execute('''select user_id from user''')
    x = c.fetchall()
    c.execute('''select item_id, type from purchase_item''')
    y = c.fetchall()
    if x and y:
        for i in x:
            for j in y:
                c.execute('''select exists(select * from user_item where user_id=:a and item_id=:b and type=:c)''', {
                    'a': i[0], 'b': j[0], 'c': j[1]})
                if c.fetchone() == (0,) and j[1] != 'character':
                    c.execute('''insert into user_item values(:a,:b,:c,1)''', {
                        'a': i[0], 'b': j[0], 'c': j[1]})

    return


def unlock_user_item(c, user_id):
    # 解锁用户购买

    c.execute('''select item_id, type from purchase_item''')
    y = c.fetchall()

    for j in y:
        c.execute('''select exists(select * from user_item where user_id=:a and item_id=:b and type=:c)''', {
            'a': user_id, 'b': j[0], 'c': j[1]})
        if c.fetchone() == (0,) and j[1] != 'character':
            c.execute('''insert into user_item values(:a,:b,:c,1)''', {
                'a': user_id, 'b': j[0], 'c': j[1]})

    return


def get_all_item():
    # 所有物品数据查询
    with Connect() as c:
        c.execute('''select * from item''')
        x = c.fetchall()
        re = []
        if x:
            for i in x:
                re.append({'item_id': i[0],
                           'type': i[1],
                           'is_available': int2b(i[2])
                           })

    return re


def get_all_purchase():
    # 所有购买数据查询
    with Connect() as c:
        c.execute('''select * from purchase''')
        x = c.fetchall()
        re = []
        if x:
            for i in x:

                discount_from = None
                discount_to = None
                discount_reason = 'Yes' if i[5] == 'anni5tix' else 'No'

                if i[3] and i[3] >= 0:
                    discount_from = time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(int(i[3])/1000))
                if i[4] and i[4] >= 0:
                    discount_to = time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(int(i[4])//1000))

                c.execute(
                    '''select * from purchase_item where purchase_name=?''', (i[0],))
                y = c.fetchall()
                items = []
                if y:
                    for j in y:
                        items.append(
                            {'item_id': j[1], 'type': j[2], 'amount': j[3]})

                re.append({'purchase_name': i[0],
                           'price': i[1],
                           'orig_price': i[2],
                           'discount_from': discount_from,
                           'discount_to': discount_to,
                           'discount_reason': discount_reason,
                           'items': items
                           })

    return re


def update_one_save(c, user_id):
    # 同步指定用户存档
    # 注意，best_score表不比较，直接覆盖
    return

    # c.execute('''select scores_data, clearlamps_data from user_save where user_id=:a''', {
    #           'a': user_id})
    # x = c.fetchone()
    # if x:
    #     scores = json.loads(x[0])[""]
    #     clearlamps = json.loads(x[1])[""]
    #     clear_song_id_difficulty = []
    #     clear_state = []
    #     for i in clearlamps:
    #         clear_song_id_difficulty.append(i['song_id']+str(i['difficulty']))
    #         clear_state.append(i['clear_type'])

    #     for i in scores:
    #         rating = server.arcscore.get_one_ptt(
    #             i['song_id'], i['difficulty'], i['score'])
    #         if rating < 0:
    #             rating = 0
    #         try:
    #             index = clear_song_id_difficulty.index(
    #                 i['song_id'] + str(i['difficulty']))
    #         except:
    #             index = -1
    #         if index != -1:
    #             clear_type = clear_state[index]
    #         else:
    #             clear_type = 0
    #         c.execute('''delete from best_score where user_id=:a and song_id=:b and difficulty=:c''', {
    #             'a': user_id, 'b': i['song_id'], 'c': i['difficulty']})
    #         c.execute('''insert into best_score values(:a, :b, :c, :d, :e, :f, :g, :h, :i, :j, :k, :l, :m, :n)''', {
    #             'a': user_id, 'b': i['song_id'], 'c': i['difficulty'], 'd': i['score'], 'e': i['shiny_perfect_count'], 'f': i['perfect_count'], 'g': i['near_count'], 'h': i['miss_count'], 'i': i['health'], 'j': i['modifier'], 'k': i['time_played'], 'l': clear_type, 'm': clear_type, 'n': rating})

    #     ptt = server.arcscore.get_user_ptt(c, user_id)  # 更新PTT
    #     c.execute('''update user set rating_ptt=:a where user_id=:b''', {
    #         'a': ptt, 'b': user_id})

    # return


def update_all_save(c):
    # 同步所有用户存档

    c.execute('''select user_id from user_save''')
    x = c.fetchall()
    if x:
        for i in x:
            update_one_save(c, i[0])

    return


def add_one_present(present_id, expire_ts, description, item_id, item_type, item_amount):
    # 添加一个奖励

    message = None
    with Connect() as c:
        c.execute(
            '''select exists(select * from present where present_id=:a)''', {'a': present_id})
        if c.fetchone() == (0,):
            c.execute(
                '''select exists(select * from item where item_id=? and type=?)''', (item_id, item_type))
            if c.fetchone() == (1,):
                c.execute('''insert into present values(:a,:b,:c)''', {
                    'a': present_id, 'b': expire_ts, 'c': description})
                c.execute('''insert into present_item values(?,?,?,?)''',
                          (present_id, item_id, item_type, item_amount))
                message = '添加成功 Successfully add it.'
            else:
                message = '物品不存在 The item does not exist.'
        else:
            message = '奖励已存在 The present exists.'

    return message


def delete_one_present(present_id):
    # 删除一个奖励

    message = None
    with Connect() as c:
        c.execute(
            '''select exists(select * from present where present_id=:a)''', {'a': present_id})
        if c.fetchone() == (1,):
            c.execute('''delete from present where present_id = :a''',
                      {'a': present_id})
            c.execute('''delete from user_present where present_id =:a''', {
                'a': present_id})
            c.execute('''delete from present_item where present_id =:a''', {
                'a': present_id})
            message = '删除成功 Successfully delete it.'
        else:
            message = '奖励不存在 The present does not exist.'

    return message


def is_present_available(c, present_id):
    # 判断present_id是否有效
    c.execute(
        '''select exists(select * from present where present_id = :a)''', {'a': present_id})

    if c.fetchone() == (1,):
        return True
    else:
        return False


def deliver_one_user_present(c, present_id, user_id):
    # 为指定玩家添加奖励，重复添加不会提示
    c.execute('''select exists(select * from user_present where user_id=:a and present_id=:b)''',
              {'a': user_id, 'b': present_id})
    if c.fetchone() == (0,):
        c.execute('''insert into user_present values(:a,:b)''',
                  {'a': user_id, 'b': present_id})
    return


def deliver_all_user_present(c, present_id):
    # 为所有玩家添加奖励
    c.execute('''select user_id from user''')
    x = c.fetchall()
    if x:
        c.execute('''delete from user_present where present_id=:b''',
                  {'b': present_id})
        for i in x:
            c.execute('''insert into user_present values(:a,:b)''',
                      {'a': i[0], 'b': present_id})

    return


def add_one_redeem(code, redeem_type, item_id, item_type, item_amount):
    # 添加一个兑换码

    message = None
    with Connect() as c:
        c.execute(
            '''select exists(select * from redeem where code=:a)''', {'a': code})
        if c.fetchone() == (0,):
            c.execute(
                '''select exists(select * from item where item_id=? and type=?)''', (item_id, item_type))
            if c.fetchone() == (1,):
                c.execute('''insert into redeem values(:a,:c)''', {
                    'a': code, 'c': redeem_type})
                c.execute('''insert into redeem_item values(?,?,?,?)''',
                          (code, item_id, item_type, item_amount))
                message = '添加成功 Successfully add it.'
            else:
                message = '物品不存在 The item does not exist.'
        else:
            message = '兑换码已存在 The redeem code exists.'

    return message


def add_some_random_redeem(amount, redeem_type, item_id, item_type, item_amount):
    # 随机生成一堆10位的兑换码

    message = None
    with Connect() as c:
        c.execute(
            '''select exists(select * from item where item_id=? and type=?)''', (item_id, item_type))
        if c.fetchone() == (0,):
            return '物品不存在 The item does not exist.'
        i = 1
        while i <= amount:
            code = random_str()
            c.execute(
                '''select exists(select * from redeem where code=:a)''', {'a': code})
            if c.fetchone() == (0,):
                c.execute('''insert into redeem values(:a,:c)''',
                          {'a': code, 'c': redeem_type})
                c.execute('''insert into redeem_item values(?,?,?,?)''',
                          (code, item_id, item_type, item_amount))
                i += 1

        message = '添加成功 Successfully add it.'

    return message


def delete_one_redeem(code):
    # 删除一个兑换码

    message = None
    with Connect() as c:
        c.execute(
            '''select exists(select * from redeem where code=:a)''', {'a': code})
        if c.fetchone() == (1,):
            c.execute('''delete from redeem where code = :a''', {'a': code})
            c.execute(
                '''delete from user_redeem where code =:a''', {'a': code})
            c.execute(
                '''delete from redeem_item where code =:a''', {'a': code})
            message = '删除成功 Successfully delete it.'
        else:
            message = '兑换码不存在 The redeem code does not exist.'

    return message


def change_userpwd(c, user_id, password):
    # 修改用户密码
    hash_pwd = hashlib.sha256(password.encode("utf8")).hexdigest()
    c.execute('''update user set password =:a where user_id=:b''',
              {'a': hash_pwd, 'b': user_id})
    return


def ban_one_user(c, user_id):
    # 封禁用户
    c.execute('''update user set password = '' where user_id=:a''',
              {'a': user_id})
    c.execute('''delete from login where user_id=:a''', {'a': user_id})
    return


def clear_user_score(c, user_id):
    # 清除用户所有成绩，包括best_score和recent30，以及recent数据，但不包括云端存档
    c.execute('''update user set rating_ptt=0, song_id='', difficulty=0, score=0, shiny_perfect_count=0, perfect_count=0, near_count=0, miss_count=0, health=0, time_played=0, rating=0, world_rank_score=0 where user_id=:a''',
              {'a': user_id})
    c.execute('''delete from best_score where user_id=:a''', {'a': user_id})
    c.execute('''delete from recent30 where user_id=:a''', {'a': user_id})
    return
