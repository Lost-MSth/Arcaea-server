from setting import Config


def get_user_items(c, user_id, item_type):
    # 得到用户的物品，返回列表，不包含数量信息

    if item_type == 'world_song' and Config.WORLD_SONG_FULL_UNLOCK or item_type == 'world_unlock' and Config.WORLD_SCENERY_FULL_UNLOCK:
        c.execute('''select item_id from item where type=?''', (item_type,))
    else:
        c.execute('''select item_id from user_item where user_id = :user_id and type = :item_type''',
                  {'user_id': user_id, 'item_type': item_type})
    x = c.fetchall()
    if not x:
        return []

    re = []
    for i in x:
        re.append(i[0])
    return re


def get_user_cores(c, user_id):
    # 得到用户的core，返回字典列表
    r = []
    c.execute(
        '''select item_id, amount from user_item where user_id = ? and type="core"''', (user_id,))
    x = c.fetchall()
    if x:
        for i in x:
            if i[1]:
                amount = i[1]
            else:
                amount = 0
            r.append({'core_type': i[0], 'amount': amount})

    return r


def claim_user_item(c, user_id, item_id, item_type, amount=1):
    # 处理用户物品，包括添加和删除操作，返回成功与否布尔值
    # 这个接口允许memory变成负数，所以不能用来购买

    try:
        amount = int(amount)
    except:
        return False

    if item_type not in ['memory', 'character']:
        c.execute('''select is_available from item where item_id=? and type=?''',
                  (item_id, item_type))
        x = c.fetchone()
        if x:
            if x[0] == 0:
                return False
        else:
            return False

    if item_type in ['core', 'anni5tix']:
        c.execute(
            '''select amount from user_item where user_id=? and item_id=? and type=?''', (user_id, item_id, item_type))
        x = c.fetchone()
        if x:
            if x[0] + amount < 0:  # 数量不足
                return False
            c.execute('''update user_item set amount=? where user_id=? and item_id=? and type=?''',
                      (x[0]+amount, user_id, item_id, item_type))
        else:
            if amount < 0:  # 添加数量错误
                return False
            c.execute('''insert into user_item values(?,?,?,?)''',
                      (user_id, item_id, item_type, amount))

    elif item_type == 'memory':
        c.execute('''select ticket from user where user_id=?''', (user_id,))
        x = c.fetchone()
        if x is not None:
            c.execute('''update user set ticket=? where user_id=?''',
                      (x[0]+amount, user_id))
        else:
            return False

    elif item_type == 'character':
        if not item_id.isdigit():
            c.execute(
                '''select character_id from character where name=?''', (item_id,))
            x = c.fetchone()
            if x:
                character_id = x[0]
            else:
                return False
        else:
            character_id = int(item_id)
        c.execute(
            '''select exists(select * from user_char where user_id=? and character_id=?)''', (user_id, character_id))
        if c.fetchone() == (0,):
            c.execute('''insert into user_char values(?,?,1,0,0,0)''',
                      (user_id, character_id))

    elif item_type in ['world_song', 'world_unlock', 'single', 'pack']:
        c.execute('''select exists(select * from user_item where user_id=? and item_id=? and type=?)''',
                  (user_id, item_id, item_type))
        if c.fetchone() == (0,):
            c.execute('''insert into user_item values(:a,:b,:c,1)''',
                      {'a': user_id, 'b': item_id, 'c': item_type})

    return True
