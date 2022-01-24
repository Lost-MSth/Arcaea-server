from setting import Config
from server.sql import Connect
from .config import Constant
import server.info
import server.item
import server.setme


def int2b(x):
    # int与布尔值转换
    if x is None or x == 0:
        return False
    else:
        return True


def get_level_steps():
    # 返回level_steps字典数组
    return [{'level': i, 'level_exp': Constant.LEVEL_STEPS[i]} for i in Constant.LEVEL_STEPS]


def calc_char_value(level, value1, value20, value30):
    # 计算搭档数值的核心函数，返回浮点数

    def calc_char_value_20(level, stata, statb, lva=1, lvb=20):
        # 计算1~20级搭档数值的核心函数，返回浮点数，来自https://redive.estertion.win/arcaea/calc/

        n = [0, 0, 0.0005831753900000081, 0.004665403120000065, 0.015745735529959858, 0.03732322495992008, 0.07289692374980007, 0.12596588423968, 0.2000291587694801, 0.29858579967923987, 0.42513485930893946,
             0.5748651406910605, 0.7014142003207574, 0.7999708412305152, 0.8740341157603029, 0.9271030762501818, 0.962676775040091, 0.9842542644700301, 0.9953345968799998, 0.9994168246100001, 1]
        e = n[lva] - n[lvb]
        a = stata - statb
        r = a / e
        d = stata - n[lva] * r

        return d + r * n[level]

    def calc_char_value_30(level, stata, statb, lva=20, lvb=30):
        # 计算21~30级搭档数值，返回浮点数

        return (level - lva) * (statb - stata) / (lvb - lva) + stata

    if level < 1 or level > 30:
        return 0
    elif 1 <= level <= 20:
        return calc_char_value_20(level, value1, value20)
    else:
        return calc_char_value_30(level, value20, value30)


def get_char_core(c, character_id):
    # 得到对应角色觉醒所需的核心，返回字典列表
    r = []
    c.execute(
        '''select item_id, amount from char_item where character_id = ? and type="core"''', (character_id,))
    x = c.fetchall()
    if x:
        for i in x:
            r.append({'core_type': i[0], 'amount': i[1]})
    return r


def get_user_characters(c, user_id):
    # 获取用户所拥有角色，返回列表

    c.execute('''select character_id from user_char where user_id = :user_id''',
              {'user_id': user_id})

    x = c.fetchall()
    characters = []

    if x:
        for i in x:
            characters.append(i[0])

    return characters


def get_user_character(c, user_id):
    # 得到用户拥有的角色列表，返回列表

    if Config.CHARACTER_FULL_UNLOCK:
        c.execute('''select * from user_char_full a,character b where a.user_id = :user_id and a.character_id=b.character_id''',
                  {'user_id': user_id})
    else:
        c.execute('''select * from user_char a,character b where a.user_id = :user_id and a.character_id=b.character_id''',
                  {'user_id': user_id})
    x = c.fetchall()
    if not x and not Config.CHARACTER_FULL_UNLOCK:
        # 添加初始角色
        c.execute('''insert into user_char values(?,?,?,?,?,?)''',
                  (user_id, 0, 1, 0, 0, 0))
        c.execute('''insert into user_char values(?,?,?,?,?,?)''',
                  (user_id, 1, 1, 0, 0, 0))
        c.execute('''select * from user_char a,character b where a.user_id = :user_id and a.character_id=b.character_id''',
                  {'user_id': user_id})
        x = c.fetchall()

    if not x:
        return []
    r = []
    for i in x:

        char = {
            "is_uncapped_override": int2b(i[5]),
            "is_uncapped": int2b(i[4]),
            "uncap_cores": get_char_core(c, i[1]),
            "char_type": i[22],
            "skill_id_uncap": i[21],
            "skill_requires_uncap": int2b(i[20]),
            "skill_unlock_level": i[19],
            "skill_id": i[18],
            "overdrive": calc_char_value(i[2], i[11], i[14], i[17]),
            "prog": calc_char_value(i[2], i[10], i[13], i[16]),
            "frag": calc_char_value(i[2], i[9], i[12], i[15]),
            "level_exp": Constant.LEVEL_STEPS[i[2]],
            "exp": i[3],
            "level": i[2],
            "name": i[7],
            "character_id": i[1]
        }
        if i[1] == 21:
            char["voice"] = [0, 1, 2, 3, 100, 1000, 1001]
        r.append(char)

    return r


def get_one_character(c, user_id, character_id):
    # 得到用户某个拥有的角色列表，返回字典

    if Config.CHARACTER_FULL_UNLOCK:
        c.execute('''select * from user_char_full a,character b where a.user_id = :user_id and a.character_id=b.character_id and a.character_id=:a''',
                  {'user_id': user_id, 'a': character_id})
    else:
        c.execute('''select * from user_char a,character b where a.user_id = :user_id and a.character_id=b.character_id and a.character_id=:a''',
                  {'user_id': user_id, 'a': character_id})
    x = c.fetchone()
    if not x:
        return {}
    r = {
        "is_uncapped_override": int2b(x[5]),
        "is_uncapped": int2b(x[4]),
        "uncap_cores": get_char_core(c, x[1]),
        "char_type": x[22],
        "skill_id_uncap": x[21],
        "skill_requires_uncap": int2b(x[20]),
        "skill_unlock_level": x[19],
        "skill_id": x[18],
        "overdrive": calc_char_value(x[2], x[11], x[14], x[17]),
        "prog": calc_char_value(x[2], x[10], x[13], x[16]),
        "frag": calc_char_value(x[2], x[9], x[12], x[15]),
        "level_exp": Constant.LEVEL_STEPS[x[2]],
        "exp": x[3],
        "level": x[2],
        "name": x[7],
        "character_id": x[1]
    }
    if x[1] == 21:
        r["voice"] = [0, 1, 2, 3, 100, 1000, 1001]

    return r


def calc_level_up(c, user_id, character_id, exp, exp_addition):
    # 计算角色升级，返回当前经验和等级

    exp += exp_addition

    if exp >= Constant.LEVEL_STEPS[20]:  # 未觉醒溢出
        c.execute('''select is_uncapped from user_char where user_id=? and character_id=?''',
                  (user_id, character_id))
        x = c.fetchone()
        if x and x[0] == 0:
            return Constant.LEVEL_STEPS[20], 20

    a = []
    b = []
    for i in Constant.LEVEL_STEPS:
        a.append(i)
        b.append(Constant.LEVEL_STEPS[i])

    if exp >= b[-1]:  # 溢出
        return b[-1], a[-1]

    if exp < b[0]:  # 向下溢出，是异常状态
        return 0, 1

    i = len(a) - 1
    while exp < b[i]:
        i -= 1

    return exp, a[i]


def char_use_core(user_id, character_id, amount):
    # 以太之滴升级，返回user_id，core状态，角色状态的字典
    r = None
    with Connect() as c:

        c.execute(
            '''select amount from user_item where user_id=? and item_id="core_generic" and type="core"''', (user_id,))
        x = c.fetchone()
        if x:
            pre_amount = x[0]
        else:
            pre_amount = 0

        if amount <= pre_amount:
            c.execute(
                '''select exp from user_char where user_id=? and character_id=?''', (user_id, character_id))
            x = c.fetchone()
            if x:
                exp, level = calc_level_up(
                    c, user_id, character_id, x[0], amount*Config.CORE_EXP)
                c.execute('''update user_char set level=?, exp=? where user_id=? and character_id=?''',
                          (level, exp, user_id, character_id))
                server.item.claim_user_item(
                    c, user_id, 'core_generic', 'core', -amount)

        r = {'character': [get_one_character(c, user_id, character_id)]}
        r['cores'] = server.item.get_user_cores(c, user_id)
        r['user_id'] = user_id
    return r


def char_uncap(user_id, character_id):
    # 角色觉醒，返回user_id，core状态，角色状态的字典
    r = None
    with Connect() as c:
        c.execute('''select * from char_item where character_id=?''',
                  (character_id,))
        x = c.fetchall()
        if not x:
            return None

        success = True
        for i in x:
            c.execute(
                '''select amount from user_item where user_id=? and item_id=? and type=?''', (user_id, i[1], i[2]))
            y = c.fetchone()
            if not y or i[3] > y[0]:
                success = False
                break

        if success:
            c.execute('''update user_char set is_uncapped=1, is_uncapped_override=0 where user_id=? and character_id=?''',
                      (user_id, character_id))
            for i in x:
                server.item.claim_user_item(c, user_id, i[1], i[2], -i[3])

        r = {'character': [get_one_character(c, user_id, character_id)]}
        r['cores'] = server.item.get_user_cores(c, user_id)
        r['user_id'] = user_id
    return r
