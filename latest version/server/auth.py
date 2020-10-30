import sqlite3
import hashlib
import time
import server.arcworld


def arc_login(name: str, password: str) -> str:  # 登录判断
    # 查询数据库中的user表，验证账号密码，返回并记录token
    # token采用user_id和时间戳连接后hash生成（真的是瞎想的，没用bear）
    # 密码和token的加密方式为 SHA-256

    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    hash_pwd = hashlib.sha256(password.encode("utf8")).hexdigest()
    c.execute('''select user_id from user where name = :name and password = :password''', {
              'name': name, 'password': hash_pwd})
    x = c.fetchone()
    if x is not None:
        user_id = str(x[0])
        now = int(time.time() * 1000)
        token = hashlib.sha256((user_id + str(now)).encode("utf8")).hexdigest()
        c.execute(
            '''select exists(select * from login where user_id = :user_id)''', {"user_id": user_id})

        if c.fetchone() == (1,):  # 删掉多余token
            c.execute('''delete from login where user_id = :user_id''',
                      {'user_id': user_id})

        c.execute('''insert into login(access_token, user_id) values(:access_token, :user_id)''', {
                  'user_id': user_id, 'access_token': token})
        conn.commit()
        conn.close()
        return token

    conn.commit()
    conn.close()
    return None


def arc_register(name: str, password: str):  # 注册
    # 账号注册，只记录hash密码和用户名，生成user_id和user_code，自动登录返回token
    # token和密码的处理同登录部分

    def build_user_code(c):
        # 生成9位的user_code，用的自然是随机
        import random
        flag = True
        while flag:
            user_code = ''.join([str(random.randint(0, 9)) for i in range(9)])
            c.execute('''select exists(select * from user where user_code = :user_code)''',
                      {'user_code': user_code})
            if c.fetchone() == (0,):
                flag = False
        return user_code

    def build_user_id(c):
        # 生成user_id，往后加1
        c.execute('''select max(user_id) from user''')
        x = c.fetchone()
        if x[0] is not None:
            return x[0] + 1
        else:
            return 2000001

    # def insert_user_char(c, user_id):
    #     # 为用户添加所有可用角色
    #     for i in range(0, 38):
    #         if i in [0, 1, 2, 4, 13, 26, 27, 28, 29, 36, 21]:
    #             sql = 'insert into user_char values('+str(user_id)+','+str(
    #                 i)+''',30,25000,25000,90,90,90,'',0,0,'',0,1,1)'''
    #             c.execute(sql)
    #         else:
    #             if i != 5:
    #                 sql = 'insert into user_char values('+str(user_id)+','+str(
    #                     i)+''',30,25000,25000,90,90,90,'',0,0,'',0,0,0)'''
    #                 c.execute(sql)
    def insert_user_char(c, user_id):
        # 为用户添加所有可用角色
        c.execute('''select * from character''')
        x = c.fetchall()
        if x != []:
            for i in x:
                c.execute('''insert into user_char values(:a,:b,:c,:d,:e,:f,:g,:h,:i,:j,:k,:l,:m,:n,:o)''', {
                          'a': user_id, 'b': i[0], 'c': i[2], 'd': i[3], 'e': i[4], 'f': i[5], 'g': i[6], 'h': i[7], 'i': i[8], 'j': i[9], 'k': i[10], 'l': i[11], 'm': i[12], 'n': i[14], 'o': i[15]})

    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    hash_pwd = hashlib.sha256(password.encode("utf8")).hexdigest()
    c.execute(
        '''select exists(select * from user where name = :name)''', {'name': name})
    if c.fetchone() == (0,):
        user_code = build_user_code(c)
        user_id = build_user_id(c)
        now = int(time.time() * 1000)
        c.execute('''insert into user(user_id, name, password, join_date, user_code, rating_ptt, 
        character_id, is_skill_sealed, is_char_uncapped, is_char_uncapped_override, is_hide_rating, favorite_character, max_stamina_notification_enabled, current_map)
        values(:user_id, :name, :password, :join_date, :user_code, 0, 0, 0, 0, 0, 0, -1, 0, '')
        ''', {'user_code': user_code, 'user_id': user_id, 'join_date': now, 'name': name, 'password': hash_pwd})
        c.execute('''insert into recent30(user_id) values(:user_id)''', {
                  'user_id': user_id})

        token = hashlib.sha256(
            (str(user_id) + str(now)).encode("utf8")).hexdigest()
        c.execute('''insert into login(access_token, user_id) values(:access_token, :user_id)''', {
                  'user_id': user_id, 'access_token': token})

        insert_user_char(c, user_id)
        conn.commit()
        conn.close()
        return user_id, token, 0
    else:
        conn.commit()
        conn.close()
        return None, None, 101


def token_get_id(token: str):
    # 用token获取id，没有考虑不同用户token相同情况，说不定会有bug

    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    c.execute('''select user_id from login where access_token = :token''', {
              'token': token})
    x = c.fetchone()
    if x is not None:
        conn.commit()
        conn.close()
        return x[0]
    else:
        conn.commit()
        conn.close()
        return None


def code_get_id(user_code):
    # 用user_code获取id

    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    c.execute('''select user_id from user where user_code = :a''',
              {'a': user_code})
    x = c.fetchone()
    if x is not None:
        conn.commit()
        conn.close()
        return x[0]
    else:
        conn.commit()
        conn.close()
        return None
