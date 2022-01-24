from server.sql import Connect
from setting import Config
from .config import Constant
import server.info
import server.character


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
        if Config.CHARACTER_FULL_UNLOCK:
            c.execute('''select is_uncapped, is_uncapped_override from user_char_full where user_id = :a and character_id = :b''',
                      {'a': user_id, 'b': character_id})
        else:
            c.execute('''select is_uncapped, is_uncapped_override from user_char where user_id = :a and character_id = :b''',
                      {'a': user_id, 'b': character_id})
        x = c.fetchone()
        if x:
            is_uncapped = x[0]
            is_uncapped_override = x[1]
        else:
            return False

        if skill_sealed == 'false':
            skill_sealed = False
        else:
            skill_sealed = True
        c.execute('''update user set is_skill_sealed = :a, character_id = :b, is_char_uncapped = :c, is_char_uncapped_override = :d where user_id = :e''', {
            'a': b2int(skill_sealed), 'b': character_id, 'c': is_uncapped, 'd': is_uncapped_override, 'e': user_id})

        re = True

    return re


def change_char_uncap(user_id, character_id):
    # 角色觉醒改变，返回字典
    r = None
    with Connect() as c:
        if not Config.CHARACTER_FULL_UNLOCK:
            c.execute('''select is_uncapped, is_uncapped_override from user_char where user_id = :a and character_id = :b''',
                      {'a': user_id, 'b': character_id})
        else:
            c.execute('''select is_uncapped, is_uncapped_override from user_char_full where user_id = :a and character_id = :b''',
                      {'a': user_id, 'b': character_id})
        x = c.fetchone()

        if x is not None and x[0] == 1:
            c.execute('''update user set is_char_uncapped_override = :a where user_id = :b''', {
                'a': b2int(x[1] == 0), 'b': user_id})

            if not Config.CHARACTER_FULL_UNLOCK:
                c.execute('''update user_char set is_uncapped_override = :a where user_id = :b and character_id = :c''', {
                    'a': b2int(x[1] == 0), 'b': user_id, 'c': character_id})
                c.execute(
                    '''select * from user_char a,character b where a.user_id=? and a.character_id=b.character_id and a.character_id=?''', (user_id, character_id))
            else:
                c.execute('''update user_char_full set is_uncapped_override = :a where user_id = :b and character_id = :c''', {
                    'a': b2int(x[1] == 0), 'b': user_id, 'c': character_id})
                c.execute(
                    '''select * from user_char_full a,character b where a.user_id=? and a.character_id=b.character_id and a.character_id=?''', (user_id, character_id))
            y = c.fetchone()
            if y is not None:
                r = {
                    "is_uncapped_override": int2b(y[5]),
                    "is_uncapped": int2b(y[4]),
                    "uncap_cores": server.character.get_char_core(c, y[1]),
                    "char_type": y[22],
                    "skill_id_uncap": y[21],
                    "skill_requires_uncap": int2b(y[20]),
                    "skill_unlock_level": y[19],
                    "skill_id": y[18],
                    "overdrive": server.character.calc_char_value(y[2], y[11], y[14], y[17]),
                    "prog": server.character.calc_char_value(y[2], y[10], y[13], y[16]),
                    "frag": server.character.calc_char_value(y[2], y[9], y[12], y[15]),
                    "level_exp": Constant.LEVEL_STEPS[y[2]],
                    "exp": y[3],
                    "level": y[2],
                    "name": y[7],
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
