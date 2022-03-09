from server.sql import Connect
import server.item
import server.character
import time


def int2b(x):
    # int与布尔值转换
    if x is None or x == 0:
        return False
    else:
        return True


def get_purchase(c, user_id, type='pack'):
    # 读取packs内容，返回字典列表
    c.execute(
        '''select * from purchase where purchase_name in (select purchase_name from purchase_item where type = :a)''', {'a': type})
    x = c.fetchall()
    if not x:
        return []

    re = []
    for i in x:
        items = []
        c.execute(
            '''select a.*, b.amount from item a, purchase_item b where a.item_id=b.item_id and a.type=b.type and b.purchase_name=:name''', {'name': i[0]})
        y = c.fetchall()
        t = None
        if y:
            for j in y:
                if j[3]:
                    amount = j[3]
                else:
                    amount = 1
                if i[0] == j[0]:
                    # 物品排序，否则客户端报错
                    t = {
                        "type": j[1],
                        "id": j[0],
                        "is_available": int2b(j[2]),
                        'amount': amount
                    }
                else:
                    items.append({
                        "type": j[1],
                        "id": j[0],
                        "is_available": int2b(j[2]),
                        "amount": amount
                    })

            if t is not None:
                # 放到列表头
                items = [t, items]

        r = {"name": i[0],
             "items": items,
             "price": i[1],
             "orig_price": i[2]}

        if i[3] > 0:
            r['discount_from'] = i[3]
            if i[4] > 0:
                r['discount_to'] = i[4]

            if i[5] == 'anni5tix' and i[3] <= int(time.time() * 1000) <= i[4]:
                c.execute(
                    '''select amount from user_item where user_id=? and item_id="anni5tix"''', (user_id,))
                z = c.fetchone()
                if z and z[0] >= 1:
                    r['discount_reason'] = 'anni5tix'
                    r['price'] = 0

        re.append(r)

    return re


def get_single_purchase(user_id):
    # main里面没开数据库，这里写一下代替
    re = []
    with Connect() as c:
        re = get_purchase(c, user_id, 'single')

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


def buy_item_with_anni5tix(c, user_id):
    # 兑换券购买接口，返回成功与否标志
    c.execute('''select amount from user_item where user_id = :a and item_id = "anni5tix"''',
              {'a': user_id})
    amount = c.fetchone()
    if amount:
        amount = amount[0]
    else:
        return False

    if amount <= 0:
        return False

    c.execute('''update user_item set amount = :b where user_id = :a and item_id = "anni5tix"''',
              {'a': user_id, 'b': amount-1})

    return True


def buy_thing(user_id, purchase_id):
    # 购买物品接口，返回字典
    success_flag = False
    ticket = 0
    packs = []
    singles = []
    characters = []

    with Connect() as c:
        c.execute('''select price, orig_price, discount_from, discount_to, discount_reason from purchase where purchase_name=:a''',
                  {'a': purchase_id})
        x = c.fetchone()
        price = 0
        flag = False
        if x:
            price = x[0]
            orig_price = x[1]
            discount_from = x[2]
            discount_to = x[3]
            discount_reason = x[4]
        else:
            return {
                "success": False,
                "error_code": 501
            }

        c.execute(
            '''select item_id, type, amount from purchase_item where purchase_name=:a''', {'a': purchase_id})
        x = c.fetchall()
        if x:
            now = int(time.time() * 1000)
            if not(discount_from <= now <= discount_to):
                price = orig_price
            elif discount_reason == 'anni5tix' and buy_item_with_anni5tix(c, user_id):
                price = 0

            flag, ticket = buy_item(c, user_id, price)

            if flag:
                for i in x:
                    if i[2]:
                        amount = i[2]
                    else:
                        amount = 1
                    server.item.claim_user_item(c, user_id, i[0], i[1], amount)

                success_flag = True
        else:
            return {
                "success": False,
                "error_code": 501
            }

        packs = server.item.get_user_items(c, user_id, 'pack')
        singles = server.item.get_user_items(c, user_id, 'single')
        characters = server.character.get_user_characters(c, user_id)

    return {
        "success": success_flag,
        "value": {'user_id': user_id,
                  'ticket': ticket,
                  'packs': packs,
                  'singles': singles,
                  'characters': characters
                  }
    }


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
                c.execute(
                    '''select * from present_item where present_id=?''', (i[0],))
                y = c.fetchall()
                items = []
                if y:
                    for j in y:
                        if j is not None:
                            items.append({
                                "type": j[2],
                                "id": j[1],
                                "amount": j[3]
                            })
                re.append({'expire_ts': i[1],
                           'description': i[2],
                           'present_id': i[0],
                           'items': items
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
                c.execute(
                    '''select * from present_item where present_id=?''', (x[0],))
                y = c.fetchall()
                flag = True
                if y:
                    for j in y:
                        if j is not None:
                            flag = flag and server.item.claim_user_item(
                                c, user_id, j[1], j[2], j[3])

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

        if x[1] == 0:  # 一次性
            c.execute(
                '''select exists(select * from user_redeem where code=:a)''', {'a': code})
            if c.fetchone() == (1,):
                return 0, 505
        elif x[1] == 1:  # 每个玩家一次
            c.execute('''select exists(select * from user_redeem where code=:a and user_id=:b)''',
                      {'a': code, 'b': user_id})
            if c.fetchone() == (1,):
                return 0, 506

        c.execute('''insert into user_redeem values(:b,:a)''',
                  {'a': code, 'b': user_id})

        c.execute('''select * from redeem_item where code=?''', (code,))
        x = c.fetchall()
        flag = True
        if x:
            for i in x:
                if i[2] == 'fragment':
                    fragment += i[3]
                else:
                    flag = flag and server.item.claim_user_item(
                        c, user_id, i[1], i[2], i[3])
        if flag:
            error_code = None

    return fragment, error_code
