from server.sql import Connect
import server.info


def b2int(x):
    # int与布尔值转换
    if x:
        return 1
    else:
        return 0


def int2b(x):
    # int与布尔值转换
    if x is None or x == 0:
        return False
    else:
        return True


def change_char(user_id, character_id, skill_sealed):
    # 角色改变，包括技能封印的改变，返回成功与否的布尔值
    re = False

    with Connect() as c:
        c.execute('''select is_uncapped, is_uncapped_override from user_char where user_id = :a and character_id = :b''',
                  {'a': user_id, 'b': character_id})
        x = c.fetchone()
        if x is not None:
            if skill_sealed == 'false':
                skill_sealed = False
            else:
                skill_sealed = True
            c.execute('''update user set is_skill_sealed = :a, character_id = :b, is_char_uncapped = :c, is_char_uncapped_override = :d where user_id = :e''', {
                'a': b2int(skill_sealed), 'b': character_id, 'c': x[0], 'd': x[1], 'e': user_id})

            re = True

    return re


def change_char_uncap(user_id, character_id):
    # 角色觉醒改变，返回字典
    r = None
    with Connect() as c:
        c.execute('''select is_uncapped, is_uncapped_override from user_char where user_id = :a and character_id = :b''',
                  {'a': user_id, 'b': character_id})
        x = c.fetchone()

        if x is not None and x[0] == 1:
            c.execute('''update user set is_char_uncapped_override = :a where user_id = :b''', {
                'a': b2int(x[1] == 0), 'b': user_id})
            c.execute('''update user_char set is_uncapped_override = :a where user_id = :b and character_id = :c''', {
                'a': b2int(x[1] == 0), 'b': user_id, 'c': character_id})
            c.execute('''select * from user_char where user_id = :a and character_id = :b''',
                      {'a': user_id, 'b': character_id})
            y = c.fetchone()
            c.execute(
                '''select name from character where character_id = :x''', {'x': y[1]})
            z = c.fetchone()
            if z is not None:
                char_name = z[0]
            if y is not None:
                r = {
                    "is_uncapped_override": int2b(y[14]),
                    "is_uncapped": int2b(y[13]),
                    "uncap_cores": [],
                    "char_type": y[12],
                    "skill_id_uncap": y[11],
                    "skill_requires_uncap": int2b(y[10]),
                    "skill_unlock_level": y[9],
                    "skill_id": y[8],
                    "overdrive": y[7],
                    "prog": y[6],
                    "frag": y[5],
                    "level_exp": y[4],
                    "exp": y[3],
                    "level": y[2],
                    "name": char_name,
                    "character_id": y[1]
                }

    return r


def arc_sys_set(user_id, value, set_arg):
    # 三个设置，PTT隐藏、体力满通知、最爱角色，无返回
    with Connect() as c:
        if 'favorite_character' in set_arg:
            value = int(value)
            c.execute('''update user set favorite_character = :a where user_id = :b''', {
                'a': value, 'b': user_id})

        else:
            if value == 'false':
                value = False
            else:
                value = True

            if 'is_hide_rating' in set_arg:
                c.execute('''update user set is_hide_rating = :a where user_id = :b''', {
                    'a': b2int(value), 'b': user_id})
            if 'max_stamina_notification_enabled' in set_arg:
                c.execute('''update user set max_stamina_notification_enabled = :a where user_id = :b''', {
                    'a': b2int(value), 'b': user_id})

    return None


def arc_add_friend(user_id, friend_id):
    # 加好友，返回好友列表，或者是错误码602、604
    if user_id == friend_id:
        return 604

    r = None
    with Connect() as c:
        c.execute('''select exists(select * from friend where user_id_me = :x and user_id_other = :y)''',
                  {'x': user_id, 'y': friend_id})
        if c.fetchone() == (0,):
            c.execute('''insert into friend values(:a, :b)''',
                      {'a': user_id, 'b': friend_id})
            r = server.info.get_user_friend(c, user_id)
        else:
            r = 602

    return r


def arc_delete_friend(user_id, friend_id):
    # 删好友，返回好友列表
    r = None
    with Connect() as c:

        c.execute('''select exists(select * from friend where user_id_me = :x and user_id_other = :y)''',
                  {'x': user_id, 'y': friend_id})
        if c.fetchone() == (1,):
            c.execute('''delete from friend where user_id_me = :x and user_id_other = :y''',
                      {'x': user_id, 'y': friend_id})

            r = server.info.get_user_friend(c, user_id)

    return r
