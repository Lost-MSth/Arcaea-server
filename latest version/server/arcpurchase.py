from server.sql import Connect
import time
import json


def int2b(x):
    # int与布尔值转换
    if x is None or x == 0:
        return False
    else:
        return True


def get_item(c, type='pack'):
    # 读取packs内容，返回字典列表
    c.execute('''select * from item where type = :a''', {'a': type})
    x = c.fetchall()
    if not x:
        return []

    re = []
    for i in x:
        r = {"name": i[0],
             "items": [{
                 "type": i[1],
                 "id": i[0],
                 "is_available": int2b(i[2])
             }],
             "price": i[3],
             "orig_price": i[4]}

        if i[5] > 0:
            r['discount_from'] = i[5]
        if i[6] > 0:
            r['discount_to'] = i[6]

        re.append(r)

    return re


def get_single_purchase():
    # main里面没开数据库，这里写一下代替
    re = []
    with Connect() as c:
        re = get_item(c, type='single')

    return re


def buy_item(c, user_id, price):
    # 购买接口，返回成功与否标识符和剩余源点数
    c.execute('''select ticket from user where user_id = :a''',
              {'a': user_id})
    ticket = c.fetchone()
    if ticket:
        ticket = ticket[0]
    else:
        ticket = 0

    if ticket < price:
        return False, ticket

    c.execute('''update user set ticket = :b where user_id = :a''',
              {'a': user_id, 'b': ticket-price})

    return True, ticket - price


def buy_pack(user_id, pack_id):
    # 曲包购买，返回字典
    re = {"success": False}
    with Connect() as c:
        c.execute('''select price from item where item_id = :a''',
                  {'a': pack_id})
        price = c.fetchone()
        if price:
            price = price[0]
        else:
            price = 0

        flag, ticket = buy_item(c, user_id, price)

        if flag:
            c.execute('''insert into user_item values(:a,:b,'pack')''',
                      {'a': user_id, 'b': pack_id})

            re = {"success": True}

    return re


def buy_single(user_id, single_id):
    # 单曲购买，返回字典
    re = {"success": False}
    with Connect() as c:
        c.execute('''select price from item where item_id = :a''',
                  {'a': single_id})
        price = c.fetchone()
        if price:
            price = price[0]
        else:
            price = 0

        flag, ticket = buy_item(c, user_id, price)

        if flag:
            c.execute('''insert into user_item values(:a,:b,'single')''',
                      {'a': user_id, 'b': single_id})
            re = {"success": True}

    return re


def get_prog_boost(user_id):
    # 世界模式源韵强化，扣50源点，返回剩余源点数

    ticket = -1
    with Connect() as c:
        flag, ticket = buy_item(c, user_id, 50)

        if flag:
            c.execute('''update user set prog_boost = 1 where user_id = :a''', {
                      'a': user_id})
    if ticket >= 0:
        return ticket, None
    else:
        return 0, 108


def get_user_present(c, user_id):
    # 获取用户奖励，返回字典列表
    c.execute(
        '''select * from present where present_id in (select present_id from user_present where user_id=:a)''', {'a': user_id})
    x = c.fetchall()
    re = []
    now = int(time.time() * 1000)
    if x:
        for i in x:
            if now <= int(i[1]):
                re.append({'expire_ts': i[1],
                           'description': i[3],
                           'present_id': i[0],
                           'items': json.loads(i[2])
                           })

    return re


def claim_user_present(user_id, present_id):
    # 确认并删除用户奖励，返回成功与否的布尔值
    flag = False
    with Connect() as c:
        c.execute('''select exists(select * from user_present where user_id=:a and present_id=:b)''',
                  {'a': user_id, 'b': present_id})
        if c.fetchone() == (1,):
            c.execute('''delete from user_present where user_id=:a and present_id=:b''',
                      {'a': user_id, 'b': present_id})
            c.execute('''select * from present where present_id=:b''',
                      {'b': present_id})
            x = c.fetchone()
            now = int(time.time() * 1000)
            if now <= int(x[1]):
                # 处理memory
                items = json.loads(x[2])
                for i in items:
                    if i['id'] == 'memory':
                        c.execute('''select ticket from user where user_id=:a''', {
                            'a': user_id})
                        ticket = int(c.fetchone()[0])
                        ticket += int(i['amount'])
                        c.execute('''update user set ticket=:b where user_id=:a''', {
                            'a': user_id, 'b': ticket})
                flag = True
            else:
                # 过期
                flag = False

    return flag


def claim_user_redeem(user_id, code):
    # 处理兑换码，返回碎片数量和错误码
    fragment = 0
    error_code = 108
    with Connect() as c:
        c.execute('''select * from redeem where code=:a''', {'a': code})
        x = c.fetchone()
        if not x:
            return 0, 504

        if x[2] == 0:  # 一次性
            c.execute(
                '''select exists(select * from user_redeem where code=:a)''', {'a': code})
            if c.fetchone() == (1,):
                return 0, 505
        elif x[2] == 1:  # 每个玩家一次
            c.execute('''select exists(select * from user_redeem where code=:a and user_id=:b)''',
                      {'a': code, 'b': user_id})
            if c.fetchone() == (1,):
                return 0, 506

        c.execute('''insert into user_redeem values(:b,:a)''',
                  {'a': code, 'b': user_id})

        items = json.loads(x[1])
        for i in items:
            if i['type'] == 'fragment':
                fragment = i['amount']
            if i['type'] == 'memory':
                c.execute('''select ticket from user where user_id=:a''', {
                    'a': user_id})
                ticket = int(c.fetchone()[0])
                ticket += int(i['amount'])
                c.execute('''update user set ticket=:b where user_id=:a''', {
                    'a': user_id, 'b': ticket})
        error_code = None

    return fragment, error_code
