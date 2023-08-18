import hashlib
import time
from random import Random

from core.sql import Connect


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


def update_user_char(c):
    # 用character数据更新user_char_full
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
                c.execute('''insert into user_char_full values(?,?,?,?,?,?,?)''',
                          (j[0], i[0], i[1], exp, i[2], 0))


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
