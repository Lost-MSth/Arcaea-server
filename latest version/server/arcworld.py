import json
from server.sql import Connect
from setting import Config
import server.item
import server.character
import server.info
import server.arcpurchase
import os
import time


ETO_UNCAP_BONUS_PROGRESS = 7
LUNA_UNCAP_BONUS_PROGRESS = 7


def int2b(x):
    # int与布尔值转换
    if x is None or x == 0:
        return False
    else:
        return True


def calc_stamina(max_stamina_ts, curr_stamina):
    # 计算体力，返回剩余体力数值

    stamina = int(server.info.MAX_STAMINA - (max_stamina_ts -
                                             int(time.time()*1000)) / server.info.STAMINA_RECOVER_TICK)

    if stamina >= server.info.MAX_STAMINA:
        if curr_stamina >= server.info.MAX_STAMINA:
            stamina = curr_stamina
        else:
            stamina = server.info.MAX_STAMINA
    if stamina < 0:
        stamina = 0

    return stamina


def get_world_name(file_dir='./database/map'):
    # 获取所有地图名称，返回列表
    L = []
    for root, dirs, files in os.walk(file_dir):
        for file in files:
            if os.path.splitext(file)[1] == '.json':
                L.append(os.path.splitext(file)[0])
    return L


def get_world_info(map_id):
    # 读取json文件内容，返回字典
    world_info = {}
    with open('./database/map/'+map_id+'.json', 'r') as f:
        world_info = json.load(f)

    return world_info


def get_user_world_info(user_id, map_id):
    # 读取json文件内容，加上用户信息，返回字典
    info = get_world_info(map_id)
    with Connect() as c:
        c.execute('''select * from user_world where map_id = :a and user_id = :b''',
                  {'a': map_id, 'b': user_id})
        x = c.fetchone()
        if x:
            info['curr_position'] = x[2]
            info['curr_capture'] = x[3]
            info['is_locked'] = int2b(x[4])
        else:
            info['curr_position'] = 0
            info['curr_capture'] = 0
            info['is_locked'] = True
            c.execute('''insert into user_world values(:a,:b,0,0,1)''', {
                'a': user_id, 'b': map_id})

    return info


def get_current_map(user_id):
    # 得到user的当前图，返回字符串
    re = ''
    with Connect() as c:
        c.execute('''select current_map from user where user_id = :a''',
                  {'a': user_id})
        x = c.fetchone()
        if x:
            re = x[0]

    return re


def get_world_all(user_id):
    # 读取所有地图信息并处理，返回字典列表
    re = []
    worlds = get_world_name()
    with Connect() as c:
        for map_id in worlds:
            info = get_world_info(map_id)
            steps = info['steps']
            del info['steps']
            rewards = []
            for step in steps:
                if 'items' in step:
                    rewards.append(
                        {'items': step['items'], 'position': step['position']})
            info['rewards'] = rewards
            c.execute('''select * from user_world where map_id = :a and user_id = :b''',
                      {'a': map_id, 'b': user_id})
            x = c.fetchone()
            if x:
                info['curr_position'] = x[2]
                info['curr_capture'] = x[3]
                info['is_locked'] = int2b(x[4])
            else:
                info['curr_position'] = 0
                info['curr_capture'] = 0
                info['is_locked'] = True
                c.execute('''insert into user_world values(:a,:b,0,0,1)''', {
                    'a': user_id, 'b': map_id})

            re.append(info)

    return re


def get_available_maps():
    # 获取当前可用图（用户设定的），返回字典列表
    re = []
    for i in Config.AVAILABLE_MAP:
        info = get_world_info(i)
        del info['steps']
        try:
            del info['is_locked']
            del info['curr_position']
            del info['curr_capture']
        except:
            pass
        re.append(info)

    return re


def get_user_world(user_id, map_id):
    # 获取用户图信息，返回字典
    re = {}
    with Connect() as c:
        c.execute('''select * from user_world where map_id = :a and user_id = :b''',
                  {'a': map_id, 'b': user_id})
        x = c.fetchone()
        re = {
            "user_id": user_id,
            "curr_position": 0,
            "curr_capture": 0,
            "is_locked": True,
            "map_id": map_id
        }
        if x:
            re['curr_position'] = x[2]
            re['curr_capture'] = x[3]
            re['is_locked'] = int2b(x[4])
        else:
            c.execute('''insert into user_world values(:a,:b,0,0,1)''', {
                'a': user_id, 'b': map_id})

    return re


def unlock_user_world(user_id, map_id):
    # 解锁用户的图，返回成功与否布尔值

    with Connect() as c:
        c.execute(
            '''select is_locked from user_world where map_id=? and user_id=?''', (map_id, user_id))
        x = c.fetchone()
        if x:
            is_locked = x[0]
        else:
            is_locked = 1
            c.execute('''insert into user_world values(:a,:b,0,0,1)''', {
                'a': user_id, 'b': map_id})
        if is_locked == 1:
            map_info = get_world_info(map_id)
            if 'require_type' in map_info and map_info['require_type'] != '':
                if map_info['require_type'] in ['pack', 'single']:
                    c.execute('''select exists(select * from user_item where user_id=? and item_id=? and type=?)''',
                              (user_id, map_info['require_id'], map_info['require_type']))
                    if c.fetchone() == (0,):
                        return False

            c.execute(
                '''update user_world set is_locked=0 where user_id=? and map_id=?''', (user_id, map_id))

    return True


def change_user_current_map(user_id, map_id):
    # 改变用户当前图
    with Connect() as c:
        c.execute('''update user set current_map = :a where user_id=:b''', {
            'a': map_id, 'b': user_id})
    return None


def play_world_song(user_id, args):
    # 声明是世界模式的打歌，并且记录加成信息，返回字典
    r = {}
    with Connect() as c:
        stamina_multiply = 1
        fragment_multiply = 100
        prog_boost_multiply = 0
        if 'stamina_multiply' in args:
            stamina_multiply = int(args['stamina_multiply'])
        if 'fragment_multiply' in args:
            fragment_multiply = int(args['fragment_multiply'])
        if 'prog_boost_multiply' in args:
            c.execute('''select prog_boost from user where user_id=:a''', {
                      'a': user_id})
            x = c.fetchone()
            if x and x[0] == 1:
                prog_boost_multiply = 300

        c.execute('''delete from world_songplay where user_id=:a and song_id=:b and difficulty=:c''', {
            'a': user_id, 'b': args['song_id'], 'c': args['difficulty']})
        c.execute('''insert into world_songplay values(:a,:b,:c,:d,:e,:f)''', {
            'a': user_id, 'b': args['song_id'], 'c': args['difficulty'], 'd': stamina_multiply, 'e': fragment_multiply, 'f': prog_boost_multiply})

        c.execute('''select current_map from user where user_id = :a''', {
                  'a': user_id})
        map_id = c.fetchone()[0]
        info = get_world_info(map_id)
        # 体力计算
        c.execute(
            '''select max_stamina_ts, stamina from user where user_id=?''', (user_id,))
        x = c.fetchone()
        max_stamina_ts = x[0] if x and x[0] is not None else 0
        stamina = x[1] if x and x[1] is not None else 12
        now = int(time.time() * 1000)

        # 体力不足
        if calc_stamina(max_stamina_ts, stamina) < info['stamina_cost']:
            return {}
        stamina = calc_stamina(max_stamina_ts, stamina) - \
            info['stamina_cost'] * stamina_multiply
        max_stamina_ts = now + server.info.STAMINA_RECOVER_TICK * \
            (server.info.MAX_STAMINA - stamina)
        c.execute('''update user set max_stamina_ts=?, stamina=? where user_id=?''',
                  (max_stamina_ts, stamina, user_id))
        r = {
            "stamina": stamina,
            "max_stamina_ts": max_stamina_ts,
            "token": "13145201919810"
        }

    return r


def climb_step(user_id, map_id, step, prev_capture, prev_position):
    # 爬梯子，返回奖励列表，台阶列表，当前的位置和坐标，图信息

    info = get_world_info(map_id)
    step_count = int(info['step_count'])

    restrict_ids = [[]] * step_count
    capture = [0] * step_count
    reward_bundle = [""] * step_count  # 暂且不用
    restrict_id = [""] * step_count
    restrict_type = [""] * step_count
    items = [[]] * step_count
    step_type = [[]] * step_count
    speed_limit_value = [0] * step_count
    plus_stamina_value = [0] * step_count

    for i in info['steps']:
        capture[i['position']] = i['capture']
        if 'items' in i:
            items[i['position']] = i['items']
        if 'restrict_id' in i:
            restrict_id[i['position']] = i['restrict_id']
        if 'restrict_ids' in i:
            restrict_ids[i['position']] = i['restrict_ids']
        if 'restrict_type' in i:
            restrict_type[i['position']] = i['restrict_type']
        if 'step_type' in i:
            step_type[i['position']] = i['step_type']
            if "speedlimit" in i['step_type']:
                speed_limit_value[i['position']] = i['speed_limit_value']
            if "plusstamina" in i['step_type']:
                plus_stamina_value[i['position']] = i['plus_stamina_value']

    if info['is_beyond']:  # beyond判断
        dt = info['beyond_health'] - prev_capture
        if dt >= step:
            curr_capture = prev_capture + step
        else:
            curr_capture = info['beyond_health']
        i = 0
        t = prev_capture + step
        while i < step_count and t > 0:
            dt = capture[i]
            if dt > t:
                t = 0
            else:
                t -= dt
                i += 1
        if i >= step_count:
            curr_position = step_count - 1
        else:
            curr_position = i

    else:
        i = prev_position
        j = prev_capture
        t = step
        while t > 0 and i < step_count:
            dt = capture[i] - j
            if dt > t:
                j += t
                t = 0
            else:
                t -= dt
                j = 0
                i += 1
        if i >= step_count:
            curr_position = step_count - 1
            curr_capture = 0
        else:
            curr_position = i
            curr_capture = j

    rewards = []
    steps = []
    for i in range(prev_position, curr_position+1):
        if items[i]:
            rewards.append({'position': i, 'items': items[i]})
        x = {
            "map_id": map_id,
            "position": i,
            "restrict_ids": restrict_ids[i],
            "capture": capture[i],
            "reward_bundle": reward_bundle[i],
            "restrict_id": restrict_id[i],
            "restrict_type": restrict_type[i]
        }
        if step_type[i]:
            x['step_type'] = step_type[i]
        if speed_limit_value[i]:
            x['speed_limit_value'] = speed_limit_value[i]
        if plus_stamina_value[i]:
            x['plus_stamina_value'] = plus_stamina_value[i]
        steps.append(x)

    return rewards, steps, curr_position, curr_capture, info


def world_update(c, user_id, song_id, difficulty, rating, clear_type, beyond_gauge, stamina_multiply=1, fragment_multiply=100, prog_boost_multiply=0):
    # 成绩上传后世界模式更新，返回字典

    step_times = stamina_multiply * fragment_multiply / \
        100 * (prog_boost_multiply+100)/100
    exp_times = stamina_multiply * (prog_boost_multiply+100)/100
    if prog_boost_multiply != 0:
        c.execute('''update user set prog_boost = 0 where user_id = :a''', {
            'a': user_id})
    c.execute('''delete from world_songplay where user_id=:a and song_id=:b and difficulty=:c''', {
        'a': user_id, 'b': song_id, 'c': difficulty})

    c.execute(
        '''select character_id, max_stamina_ts, stamina, is_skill_sealed, is_char_uncapped, is_char_uncapped_override from user where user_id=?''', (user_id,))
    x = c.fetchone()
    character_id = x[0] if x and x[0] is not None else 0
    max_stamina_ts = x[1] if x and x[1] is not None else 0
    stamina = x[2] if x and x[2] is not None else 12
    is_skill_sealed = x[3] if x and x[3] is not None else 1
    skill = False
    skill_uncap = False
    if not is_skill_sealed:
        if x:
            skill = True
            if x[4] is not None and x[4] == 1:
                skill_uncap = True
            if x[5] is not None and x[5] == 1:
                skill_uncap = False

    c.execute('''select frag1,prog1,overdrive1,frag20,prog20,overdrive20,frag30,prog30,overdrive30,skill_id,skill_id_uncap from character where character_id=?''', (character_id,))
    x = c.fetchone()

    if Config.CHARACTER_FULL_UNLOCK:
        c.execute('''select level, exp from user_char_full where user_id = :a and character_id = :b''', {
                  'a': user_id, 'b': character_id})
    else:
        c.execute('''select level, exp from user_char where user_id = :a and character_id = :b''', {
                  'a': user_id, 'b': character_id})
    y = c.fetchone()
    if y:
        level = y[0]
        exp = y[1]
    else:
        level = 1
        exp = 0

    if x:
        flag = server.character.calc_char_value(level, x[0], x[3], x[6])
        prog = server.character.calc_char_value(level, x[1], x[4], x[7])
        overdrive = server.character.calc_char_value(level, x[2], x[5], x[8])
        if x[9] is not None and x[9] != '' and skill:
            skill = x[9]
        else:
            skill = None
        if x[10] is not None and x[9] != '' and skill_uncap:
            skill_uncap = x[10]
        else:
            skill_uncap = None
    else:
        flag = 0
        prog = 0
        overdrive = 0
        skill = None
        skill_uncap = None

    c.execute('''select current_map from user where user_id = :a''', {
        'a': user_id})
    map_id = c.fetchone()[0]

    if beyond_gauge == 0:  # 是否是beyond挑战
        base_step = 2.5 + 2.45*rating**0.5
        step = base_step * (prog/50) * step_times
    else:
        info = get_world_info(map_id)
        if clear_type == 0:
            base_step = 8/9 + (rating/1.3)**0.5
        else:
            base_step = 8/3 + (rating/1.3)**0.5

        if character_id in info['character_affinity']:
            affinity_multiplier = info['affinity_multiplier'][info['character_affinity'].index(
                character_id)]
        else:
            affinity_multiplier = 1

        step = base_step * (prog/50) * step_times * affinity_multiplier

    c.execute('''select * from user_world where user_id = :a and map_id =:b''',
              {'a': user_id, 'b': map_id})
    y = c.fetchone()
    if y[4] == 1:  # 图不可用
        return {}

    rewards, steps, curr_position, curr_capture, info = climb_step(
        user_id, map_id, step, y[3], y[2])
    # Eto和Luna的技能
    character_bonus_progress = None
    skill_special = ''
    if skill_uncap is not None and skill_uncap and skill_uncap in ['eto_uncap', 'luna_uncap']:
        skill_special = skill_uncap
    elif skill is not None and skill and skill in ['eto_uncap', 'luna_uncap']:
        skill_special = skill
    if skill_special == 'eto_uncap':
        # eto觉醒技能，获得残片奖励时世界模式进度加7
        fragment_flag = False
        for i in rewards:
            for j in i['items']:
                if j['type'] == 'fragment':
                    fragment_flag = True
                    break
            if fragment_flag:
                break
        if fragment_flag:
            character_bonus_progress = ETO_UNCAP_BONUS_PROGRESS
            step += character_bonus_progress * step_times
        rewards, steps, curr_position, curr_capture, info = climb_step(
            user_id, map_id, step, y[3], y[2])  # 二次爬梯，重新计算

    elif skill_special == 'luna_uncap':
        # luna觉醒技能，限制格开始时世界模式进度加7
        if 'restrict_id' in steps[0] and 'restrict_type' in steps[0] and steps[0]['restrict_type'] != '' and steps[0]['restrict_id'] != '':
            character_bonus_progress = LUNA_UNCAP_BONUS_PROGRESS
            step += character_bonus_progress * step_times
        rewards, steps, curr_position, curr_capture, info = climb_step(
            user_id, map_id, step, y[3], y[2])  # 二次爬梯，重新计算

    for i in rewards:  # 物品分发
        for j in i['items']:
            amount = j['amount'] if 'amount' in j else 1
            item_id = j['id'] if 'id' in j else ''
            server.item.claim_user_item(c, user_id, item_id, j['type'], amount)

    if 'step_type' in steps[-1]:
        if 'plusstamina' in steps[-1]['step_type'] and 'plus_stamina_value' in steps[-1]:
            # 体力格子
            max_stamina_ts, stamina = add_stamina(
                c, user_id, int(steps[-1]['plus_stamina_value']))
    # 角色升级
    if not Config.CHARACTER_FULL_UNLOCK:
        exp, level = server.character.calc_level_up(
            c, user_id, character_id, exp, exp_times*rating*6)
        c.execute('''update user_char set level=?, exp=? where user_id=? and character_id=?''',
                  (level, exp, user_id, character_id))
    else:
        exp = server.character.LEVEL_STEPS[level]

    if beyond_gauge == 0:
        re = {
            "rewards": rewards,
            "exp": exp,
            "level": level,
            "base_progress": base_step,
            "progress": step,
            "user_map": {
                "user_id": user_id,
                "curr_position": curr_position,
                "curr_capture": curr_capture,
                "is_locked": int2b(y[4]),
                "map_id": map_id,
                "prev_capture": y[3],
                "prev_position": y[2],
                "beyond_health": info['beyond_health'],
                "steps": steps
            },
            "char_stats": {
                "character_id": character_id,
                "frag": flag,
                "prog": prog,
                "overdrive": overdrive
            },
            "current_stamina": calc_stamina(max_stamina_ts, stamina),
            "max_stamina_ts": max_stamina_ts
        }
    else:
        re = {
            "rewards": rewards,
            "exp": exp,
            "level": level,
            "base_progress": base_step,
            "progress": step,
            "user_map": {
                "user_id": user_id,
                "curr_position": curr_position,
                "curr_capture": curr_capture,
                "is_locked": int2b(y[4]),
                "map_id": map_id,
                "prev_capture": y[3],
                "prev_position": y[2],
                "beyond_health": info['beyond_health'],
                "step_count": len(steps)
            },
            "char_stats": {
                "character_id": character_id,
                "frag": flag,
                "prog": prog,
                "overdrive": overdrive
            },
            "current_stamina": calc_stamina(max_stamina_ts, stamina),
            "max_stamina_ts": max_stamina_ts
        }

    if character_bonus_progress is not None:
        re['character_bonus_progress'] = character_bonus_progress

    if stamina_multiply != 1:
        re['stamina_multiply'] = stamina_multiply
    if fragment_multiply != 100:
        re['fragment_multiply'] = fragment_multiply
    if prog_boost_multiply != 0:
        re['prog_boost_multiply'] = prog_boost_multiply

    if curr_position == info['step_count']-1 and info['is_repeatable']:  # 循环图判断
        curr_position = 0
    c.execute('''update user_world set curr_position=:a, curr_capture=:b where user_id=:c and map_id=:d''', {
        'a': curr_position, 'b': curr_capture, 'c': user_id, 'd': map_id})

    return re


def add_stamina(c, user_id, add_stamina):
    # 增添体力，返回max_stamina_ts和stamina

    now = int(time.time() * 1000)
    c.execute(
        '''select max_stamina_ts, stamina from user where user_id=?''', (user_id,))
    x = c.fetchone()
    if x and x[0] is not None and x[1] is not None:
        stamina = calc_stamina(x[0], x[1]) + add_stamina
        max_stamina_ts = now - \
            (stamina-server.info.MAX_STAMINA) * \
            server.info.STAMINA_RECOVER_TICK
    else:
        max_stamina_ts = now
        stamina = server.info.MAX_STAMINA

    c.execute('''update user set max_stamina_ts=?, stamina=? where user_id=?''',
              (max_stamina_ts, stamina, user_id))

    return max_stamina_ts, stamina


def buy_stamina_by_fragment(user_id):
    # 残片买体力，返回字典和错误码
    r = {}

    with Connect() as c:
        c.execute(
            '''select next_fragstam_ts from user where user_id=?''', (user_id,))
        x = c.fetchone()
        if x:
            now = int(time.time() * 1000)
            next_fragstam_ts = x[0] if x[0] else 0

            if now < next_fragstam_ts:
                return {}, 905

            next_fragstam_ts = now + 24*3600*1000
            max_stamina_ts, stamina = add_stamina(c, user_id, 6)
            c.execute('''update user set next_fragstam_ts=?, max_stamina_ts=?, stamina=? where user_id=?''',
                      (next_fragstam_ts, max_stamina_ts, stamina, user_id))

            r = {
                "user_id": user_id,
                "stamina": stamina,
                "max_stamina_ts": max_stamina_ts,
                "next_fragstam_ts": next_fragstam_ts
            }

    return r, None


def buy_stamina_by_ticket(user_id):
    # 源点买体力，返回字典和错误码
    r = {}

    with Connect() as c:
        flag, ticket = server.arcpurchase.buy_item(c, user_id, 50)
        if flag:
            max_stamina_ts, stamina = add_stamina(c, user_id, 6)
            c.execute('''update user set max_stamina_ts=?, stamina=? where user_id=?''',
                      (max_stamina_ts, stamina, user_id))
            r = {
                "user_id": user_id,
                "stamina": stamina,
                "max_stamina_ts": max_stamina_ts,
                "ticket": ticket
            }
        else:
            return None, 501

    return r, None
