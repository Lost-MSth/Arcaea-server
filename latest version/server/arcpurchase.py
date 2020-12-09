import sqlite3


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
    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    re = get_item(c, type='single')
    conn.commit()
    conn.close()
    return re


def buy_pack(user_id, pack_id):
    # 曲包购买，返回字典
    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    c.execute('''select price from item where item_id = :a''', {'a': pack_id})
    price = c.fetchone()
    if price:
        price = price[0]
    else:
        price = 0

    c.execute('''select ticket from user where user_id = :a''', {'a': user_id})
    ticket = c.fetchone()
    if ticket:
        ticket = ticket[0]
    else:
        ticket = 0

    if ticket < price:
        conn.commit()
        conn.close()
        return {
            "success": False
        }

    c.execute('''update user set ticket = :b where user_id = :a''',
              {'a': user_id, 'b': ticket-price})
    c.execute('''insert into user_item values(:a,:b,'pack')''',
              {'a': user_id, 'b': pack_id})

    conn.commit()
    conn.close()
    return {
        "success": True
    }


def buy_single(user_id, single_id):
    # 单曲购买，返回字典
    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    c.execute('''select price from item where item_id = :a''',
              {'a': single_id})
    price = c.fetchone()
    if price:
        price = price[0]
    else:
        price = 0

    c.execute('''select ticket from user where user_id = :a''', {'a': user_id})
    ticket = c.fetchone()
    if ticket:
        ticket = ticket[0]
    else:
        ticket = 0

    if ticket < price:
        conn.commit()
        conn.close()
        return {
            "success": False
        }

    c.execute('''update user set ticket = :b where user_id = :a''',
              {'a': user_id, 'b': ticket-price})
    c.execute('''insert into user_item values(:a,:b,'single')''',
              {'a': user_id, 'b': single_id})

    conn.commit()
    conn.close()
    return {
        "success": True
    }


def get_user_present(c, user_id):
    # 获取用户奖励，返回字典列表
    c.execute(
        '''select * from present where present_id in (select present_id from user_present where user_id=:a)''', {'a': user_id})
    x = c.fetchall()
    re = []
    if x:
        for i in x:
            re.append({'expire_ts': i[1],
                       'description': i[3],
                       'present_id': i[0],
                       'items': i[2]
                       })

    return re


def claim_user_present(user_id, present_id):
    # 确认并删除用户奖励，返回成功与否的布尔值
    flag = False
    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()

    c.execute('''select exists(select * from user_present where user_id=:a and present_id=:b)''',
              {'a': user_id, 'b': present_id})
    if c.fetchone() == (1,):
        flag = True
        c.execute('''delete from user_present where user_id=:a and present_id=:b''',
                  {'a': user_id, 'b': present_id})

    conn.commit()
    conn.close()
    return flag
