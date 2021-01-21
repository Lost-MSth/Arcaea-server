import json
from server.sql import Connect
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
