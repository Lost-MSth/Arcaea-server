import json
from server.sql import Connect
from setting import Config
import server.item
import server.character
import os


def int2b(x):
    # int与布尔值转换
    if x is None or x == 0:
        return False
    else:
        return True


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
            c.execute('''insert into user_world values(:a,:b,0,0,0)''', {
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
    with Connect() as c:
        worlds = get_world_name()
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
                c.execute('''insert into user_world values(:a,:b,0,0,0)''', {
                    'a': user_id, 'b': map_id})

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
            "is_locked": False,
            "map_id": map_id
        }
        if x:
            re['curr_position'] = x[2]
            re['curr_capture'] = x[3]
            re['is_locked'] = int2b(x[4])
        else:
            c.execute('''insert into user_world values(:a,:b,0,0,0)''', {
                'a': user_id, 'b': map_id})

    return re


def change_user_current_map(user_id, map_id):
    # 改变用户当前图
    with Connect() as c:
        c.execute('''update user set current_map = :a where user_id=:b''', {
            'a': map_id, 'b': user_id})
    return None


def play_world_song(user_id, args):
    # 声明是世界模式的打歌，并且记录加成信息
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

    return None


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

    c.execute('''select character_id from user where user_id=?''', (user_id,))
    x = c.fetchone()
    character_id = x[0] if x else 0
    c.execute('''select frag1,prog1,overdrive1,frag20,prog20,overdrive20,frag30,prog30,overdrive30 from character where character_id=?''', (character_id,))
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
    else:
        flag = 0
        prog = 0
        overdrive = 0

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
    rewards, steps, curr_position, curr_capture, info = climb_step(
        user_id, map_id, step, y[3], y[2])
    for i in rewards:  # 物品分发
        for j in i['items']:
            amount = j['amount'] if 'amount' in j else 1
            item_id = j['id'] if 'id' in j else ''
            server.item.claim_user_item(c, user_id, item_id, j['type'], amount)
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
            "current_stamina": 12,
            "max_stamina_ts": 1586274871917
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
            "current_stamina": 12,
            "max_stamina_ts": 1586274871917
        }

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
