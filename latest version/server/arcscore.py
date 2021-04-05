from server.sql import Connect
import time
import json
import server.arcworld
import hashlib
from setting import Config


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


def md5(code):
    # md5加密算法
    code = code.encode()
    md5s = hashlib.md5()
    md5s.update(code)
    codes = md5s.hexdigest()

    return codes


def get_score(c, user_id, song_id, difficulty):
    # 根据user_id、song_id、难度得到该曲目最好成绩，返回字典
    c.execute('''select * from best_score where user_id = :a and song_id = :b and difficulty = :c''',
              {'a': user_id, 'b': song_id, 'c': difficulty})
    x = c.fetchone()
    if x is not None:
        c.execute('''select name, character_id, is_skill_sealed, is_char_uncapped, favorite_character from user where user_id = :a''', {
                  'a': user_id})
        y = c.fetchone()
        if y is not None:
            character = y[1]
            is_char_uncapped = int2b(y[3])
            if y[4] != -1:
                character = y[4]
                c.execute('''select is_uncapped, is_uncapped_override from user_char where user_id=:a and character_id=:b''', {
                    'a': user_id, 'b': character})
                z = c.fetchone()
                if z:
                    if z[1] == 0:
                        is_char_uncapped = int2b(z[0])
                    else:
                        is_char_uncapped = False
            return {
                "user_id": x[0],
                "song_id": x[1],
                "difficulty": x[2],
                "score": x[3],
                "shiny_perfect_count": x[4],
                "perfect_count": x[5],
                "near_count": x[6],
                "miss_count": x[7],
                "health": x[8],
                "modifier": x[9],
                "time_played": x[10],
                "best_clear_type": x[11],
                "clear_type": x[12],
                "name": y[0],
                "character": character,
                "is_skill_sealed": int2b(y[2]),
                "is_char_uncapped": is_char_uncapped
            }
        else:
            return {}
    else:
        return {}


def arc_score_friend(user_id, song_id, difficulty, limit=50):
    # 得到用户好友分数表，默认最大50个
    r = []
    with Connect() as c:
        c.execute('''select user_id from best_score where user_id in (select :user_id union select user_id_other from friend where user_id_me = :user_id) and song_id = :song_id and difficulty = :difficulty order by score DESC, time_played DESC limit :limit''', {
            'user_id': user_id, 'song_id': song_id, 'difficulty': difficulty, 'limit': limit})
        x = c.fetchall()
        if x != []:
            rank = 0
            for i in x:
                rank += 1
                y = get_score(c, i[0], song_id, difficulty)
                y['rank'] = rank
                r.append(y)

    return r


def arc_score_top(song_id, difficulty, limit=20):
    # 得到top分数表，默认最多20个，如果是负数则全部查询
    r = []
    with Connect() as c:
        if limit >= 0:
            c.execute('''select user_id from best_score where song_id = :song_id and difficulty = :difficulty order by score DESC, time_played DESC limit :limit''', {
                'song_id': song_id, 'difficulty': difficulty, 'limit': limit})
        else:
            c.execute('''select user_id from best_score where song_id = :song_id and difficulty = :difficulty order by score DESC, time_played DESC''', {
                'song_id': song_id, 'difficulty': difficulty})
        x = c.fetchall()
        if x != []:
            rank = 0
            for i in x:
                rank += 1
                y = get_score(c, i[0], song_id, difficulty)
                y['rank'] = rank
                r.append(y)

    return r


def arc_score_me(user_id, song_id, difficulty, limit=20):
    # 得到用户的排名，默认最大20个
    r = []
    with Connect() as c:
        c.execute('''select exists(select * from best_score where user_id = :user_id and song_id = :song_id and difficulty = :difficulty)''', {
            'user_id': user_id, 'song_id': song_id, 'difficulty': difficulty})
        if c.fetchone() == (1,):
            c.execute('''select count(*) from best_score where song_id = :song_id and difficulty = :difficulty and (score>(select score from best_score where user_id = :user_id and song_id = :song_id and difficulty = :difficulty) or (score>(select score from best_score where user_id = :user_id and song_id = :song_id and difficulty = :difficulty) and time_played > (select time_played from best_score where user_id = :user_id and song_id = :song_id and difficulty = :difficulty)) )''', {
                'user_id': user_id, 'song_id': song_id, 'difficulty': difficulty})
            x = c.fetchone()
            myrank = int(x[0]) + 1
            c.execute('''select count(*) from best_score where song_id=:a and difficulty=:b''',
                      {'a': song_id, 'b': difficulty})
            amount = int(c.fetchone()[0])

            if myrank <= 4:  # 排名在前4
                return arc_score_top(song_id, difficulty, limit)
            elif myrank >= 5 and myrank <= 9999 - limit + 4 and amount >= 10000:  # 万名内，前面有4个人
                c.execute('''select user_id from best_score where song_id = :song_id and difficulty = :difficulty order by score DESC, time_played DESC limit :limit offset :offset''', {
                    'song_id': song_id, 'difficulty': difficulty, 'limit': limit, 'offset': myrank - 5})
                x = c.fetchall()
                if x != []:
                    rank = myrank - 5
                    for i in x:
                        rank += 1
                        y = get_score(c, i[0], song_id, difficulty)
                        y['rank'] = rank
                        r.append(y)

            elif myrank >= 10000:  # 万名外
                c.execute('''select user_id from best_score where song_id = :song_id and difficulty = :difficulty order by score DESC, time_played DESC limit :limit offset :offset''', {
                    'song_id': song_id, 'difficulty': difficulty, 'limit': limit - 1, 'offset': 9999-limit})
                x = c.fetchall()
                if x != []:
                    rank = 9999 - limit
                    for i in x:
                        rank += 1
                        y = get_score(c, i[0], song_id, difficulty)
                        y['rank'] = rank
                        r.append(y)
                    y = get_score(c, user_id, song_id, difficulty)
                    y['rank'] = -1
                    r.append(y)
            elif amount - myrank < limit - 5:  # 后方人数不足
                c.execute('''select user_id from best_score where song_id = :song_id and difficulty = :difficulty order by score DESC, time_played DESC limit :limit offset :offset''', {
                    'song_id': song_id, 'difficulty': difficulty, 'limit': limit, 'offset': amount - limit})
                x = c.fetchall()
                if x != []:
                    rank = amount - limit
                    for i in x:
                        rank += 1
                        y = get_score(c, i[0], song_id, difficulty)
                        y['rank'] = rank
                        r.append(y)
            else:
                c.execute('''select user_id from best_score where song_id = :song_id and difficulty = :difficulty order by score DESC, time_played DESC limit :limit offset :offset''', {
                    'song_id': song_id, 'difficulty': difficulty, 'limit': limit, 'offset': 9998-limit})
                x = c.fetchall()
                if x != []:
                    rank = 9998 - limit
                    for i in x:
                        rank += 1
                        y = get_score(c, i[0], song_id, difficulty)
                        y['rank'] = rank
                        r.append(y)

    return r


def get_one_ptt(song_id, difficulty, score: int) -> float:
    # 单曲ptt计算，ptt为负说明没铺面定数数据
    ptt = -10
    with Connect('./database/arcsong.db') as c:
        if difficulty == 0:
            c.execute('''select rating_pst from songs where sid = :sid;''', {
                'sid': song_id})
        elif difficulty == 1:
            c.execute('''select rating_prs from songs where sid = :sid;''', {
                'sid': song_id})
        elif difficulty == 2:
            c.execute('''select rating_ftr from songs where sid = :sid;''', {
                'sid': song_id})
        elif difficulty == 3:
            c.execute('''select rating_byn from songs where sid = :sid;''', {
                'sid': song_id})

        x = c.fetchone()
        defnum = -10  # 没在库里的全部当做定数-10
        if x is not None and x != '':
            defnum = float(x[0]) / 10
            if defnum <= 0:
                defnum = -10  # 缺少难度的当做定数-10

        if score >= 10000000:
            ptt = defnum + 2
        elif score < 9800000:
            ptt = defnum + (score-9500000) / 300000
            if ptt < 0 and defnum != -10:
                ptt = 0
        else:
            ptt = defnum + 1 + (score-9800000) / 200000

    return ptt


def get_song_grade(x):
    # 成绩转换评级
    if x >= 9900000:  # EX+
        return 6
    elif x < 9900000 and x >= 9800000:  # EX
        return 5
    elif x < 9800000 and x >= 9500000:  # AA
        return 4
    elif x < 9500000 and x >= 9200000:  # A
        return 3
    elif x < 9200000 and x >= 8900000:  # B
        return 2
    elif x < 8900000 and x >= 8600000:  # C
        return 1
    else:
        return 0


def get_song_state(x):
    # 返回成绩状态，便于比较
    if x == 3:  # PM
        return 5
    elif x == 2:  # FC
        return 4
    elif x == 5:  # Hard Clear
        return 3
    elif x == 1:  # Clear
        return 2
    elif x == 4:  # Easy Clear
        return 1
    else:  # Track Lost
        return 0


def get_user_ptt_float(c, user_id) -> float:
    # 总ptt计算，返回浮点数

    sumr = 0
    c.execute('''select rating from best_score where user_id = :a order by rating DESC limit 30''', {
              'a': user_id})
    x = c.fetchall()
    if x != []:
        n = len(x)
        for i in x:
            sumr += float(i[0])
    c.execute('''select * from recent30 where user_id = :a''', {'a': user_id})
    x = c.fetchone()
    if x is not None:
        r30 = []
        s30 = []
        for i in range(1, 61, 2):
            if x[i] is not None:
                r30.append(float(x[i]))
                s30.append(x[i+1])
            else:
                r30.append(0)
                s30.append('')
        r30, s30 = (list(t) for t in zip(*sorted(zip(r30, s30), reverse=True)))
        songs = []
        i = 0
        while len(songs) < 10 and i <= 29 and s30[i] != '' and s30[i] is not None:
            if s30[i] not in songs:
                sumr += r30[i]
                songs.append(s30[i])
            i += 1
    return sumr/40


def get_user_ptt(c, user_id) -> int:
    # 总ptt计算，返回4位整数，向下取整

    return int(get_user_ptt_float(c, user_id)*100)


def update_recent30(c, user_id, song_id, rating, is_protected):
    # 刷新r30，这里的判断方法存疑
    def insert_r30table(c, user_id, a, b):
        # 更新r30表
        c.execute('''delete from recent30 where user_id = :a''',
                  {'a': user_id})
        sql = 'insert into recent30 values(' + str(user_id)
        for i in range(0, 30):
            if a[i] is not None and b[i] is not None:
                sql = sql + ',' + str(a[i]) + ',"' + b[i] + '"'
            else:
                sql = sql + ',0,""'

        sql = sql + ')'
        c.execute(sql)

    c.execute('''select * from recent30 where user_id = :a''', {'a': user_id})
    x = c.fetchone()
    if not x:
        x = [None] * 61
        x[0] = user_id
        for i in range(2, 61, 2):
            x[i] = ''
    songs = []
    flag = True
    for i in range(2, 61, 2):
        if x[i] is None or x[i] == '':
            r30_id = 29
            flag = False
            break
        if x[i] not in songs:
            songs.append(x[i])
    if flag:
        n = len(songs)
        if n >= 11:
            r30_id = 29
        elif song_id not in songs and n == 10:
            r30_id = 29
        elif song_id in songs and n == 10:
            i = 29
            while x[i*2+2] == song_id:
                i -= 1
            r30_id = i
        elif song_id not in songs and n == 9:
            i = 29
            while x[i*2+2] == song_id:
                i -= 1
            r30_id = i
        else:
            r30_id = 29
    a = []
    b = []
    for i in range(1, 61, 2):
        a.append(x[i])
        b.append(x[i+1])

    if is_protected:
        ptt_pre = get_user_ptt_float(c, user_id)
        a_pre = [x for x in a]
        b_pre = [x for x in b]

    for i in range(r30_id, 0, -1):
        a[i] = a[i-1]
        b[i] = b[i-1]
    a[0] = rating
    b[0] = song_id

    insert_r30table(c, user_id, a, b)

    if is_protected:
        ptt = get_user_ptt_float(c, user_id)
        if ptt < ptt_pre:
            # 触发保护
            if song_id in b_pre:
                for i in range(29, -1, -1):
                    if song_id == b_pre[i] and rating > a_pre[i]:
                        # 发现重复歌曲，更新到最高rating
                        a_pre[i] = rating
                        break

            insert_r30table(c, user_id, a_pre, b_pre)
    return None


def arc_score_post(user_id, song_id, difficulty, score, shiny_perfect_count, perfect_count, near_count, miss_count, health, modifier, beyond_gauge, clear_type):
    # 分数上传，返回变化后的ptt，和世界模式变化
    ptt = None
    re = None
    with Connect() as c:
        rating = get_one_ptt(song_id, difficulty, score)
        if rating < 0:  # 没数据不会向recent30里记入
            unrank_flag = True
            rating = 0
        else:
            unrank_flag = False
        now = int(time.time() * 1000)
        # recent 更新
        c.execute('''update user set song_id = :b, difficulty = :c, score = :d, shiny_perfect_count = :e, perfect_count = :f, near_count = :g, miss_count = :h, health = :i, modifier = :j, clear_type = :k, rating = :l, time_played = :m  where user_id = :a''', {
            'a': user_id, 'b': song_id, 'c': difficulty, 'd': score, 'e': shiny_perfect_count, 'f': perfect_count, 'g': near_count, 'h': miss_count, 'i': health, 'j': modifier, 'k': clear_type, 'l': rating, 'm': now})
        # 成绩录入
        c.execute('''select score, best_clear_type from best_score where user_id = :a and song_id = :b and difficulty = :c''', {
            'a': user_id, 'b': song_id, 'c': difficulty})
        now = int(now // 1000)
        x = c.fetchone()
        if x is None:
            first_protect_flag = True  # 初见保护
            c.execute('''insert into best_score values(:a,:b,:c,:d,:e,:f,:g,:h,:i,:j,:k,:l,:m,:n)''', {
                'a': user_id, 'b': song_id, 'c': difficulty, 'd': score, 'e': shiny_perfect_count, 'f': perfect_count, 'g': near_count, 'h': miss_count, 'i': health, 'j': modifier, 'k': now, 'l': clear_type, 'm': clear_type, 'n': rating})
        else:
            first_protect_flag = False
            if get_song_state(clear_type) > get_song_state(int(x[1])):  # 状态更新
                c.execute('''update best_score set best_clear_type = :a where user_id = :b and song_id = :c and difficulty = :d''', {
                    'a': clear_type, 'b': user_id, 'c': song_id, 'd': difficulty})
            if score >= int(x[0]):  # 成绩更新
                c.execute('''update best_score set score = :d, shiny_perfect_count = :e, perfect_count = :f, near_count = :g, miss_count = :h, health = :i, modifier = :j, clear_type = :k, rating = :l, time_played = :m  where user_id = :a and song_id = :b and difficulty = :c ''', {
                    'a': user_id, 'b': song_id, 'c': difficulty, 'd': score, 'e': shiny_perfect_count, 'f': perfect_count, 'g': near_count, 'h': miss_count, 'i': health, 'j': modifier, 'k': clear_type, 'l': rating, 'm': now})
        if not unrank_flag:
            # recent30 更新
            if health == -1 or int(score) >= 9800000 or first_protect_flag:
                update_recent30(c, user_id, song_id +
                                str(difficulty), rating, True)
            else:
                update_recent30(c, user_id, song_id +
                                str(difficulty), rating, False)
        # 总PTT更新
        ptt = get_user_ptt(c, user_id)
        c.execute('''update user set rating_ptt = :a where user_id = :b''', {
            'a': ptt, 'b': user_id})
        # 世界模式判断
        c.execute('''select stamina_multiply,fragment_multiply,prog_boost_multiply from world_songplay where user_id=:a and song_id=:b and difficulty=:c''', {
            'a': user_id, 'b': song_id, 'c': difficulty})
        x = c.fetchone()
        re = None
        if x:
            stamina_multiply = x[0]
            fragment_multiply = x[1]
            prog_boost_multiply = x[2]
            step_times = stamina_multiply * fragment_multiply / \
                100 * (prog_boost_multiply+100)/100
            exp_times = stamina_multiply * (prog_boost_multiply+100)/100
            if prog_boost_multiply != 0:
                c.execute('''update user set prog_boost = 0 where user_id = :a''', {
                    'a': user_id})
            c.execute('''delete from world_songplay where user_id=:a and song_id=:b and difficulty=:c''', {
                'a': user_id, 'b': song_id, 'c': difficulty})
            c.execute('''select character_id,frag,prog,overdrive from user_char where user_id = :a and character_id = (select character_id from user where user_id=:a)''', {
                'a': user_id})
            y = c.fetchone()
            if y:
                character_id = y[0]
                flag = float(y[1])
                prog = float(y[2])
                overdrive = float(y[3])
            else:
                character_id = 0
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
                info = server.arcworld.get_world_info(map_id)
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
            rewards, steps, curr_position, curr_capture, info = server.arcworld.climb_step(
                user_id, map_id, step, y[3], y[2])

            if beyond_gauge == 0:
                re = {
                    "rewards": rewards,
                    "exp": 25000,
                    "level": 30,
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
                    "max_stamina_ts": 1586274871917,
                    "user_rating": ptt
                }
            else:
                re = {
                    "rewards": rewards,
                    "exp": 25000,
                    "level": 30,
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
                    "max_stamina_ts": 1586274871917,
                    "user_rating": ptt
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
    return ptt, re


def arc_score_check(user_id, song_id, difficulty, score, shiny_perfect_count, perfect_count, near_count, miss_count, health, modifier, beyond_gauge, clear_type, song_token, song_hash, submission_hash):
    # 分数校验，返回布尔值
    if shiny_perfect_count < 0 or perfect_count < 0 or near_count < 0 or miss_count < 0 or score < 0:
        return False
    if difficulty not in [0, 1, 2, 3]:
        return False

    all_note = perfect_count + near_count + miss_count
    ascore = 10000000 / all_note * \
        (perfect_count + near_count/2) + shiny_perfect_count
    if abs(ascore - score) >= 5:
        return False

    x = song_token + song_hash + song_id + str(difficulty) + str(score) + str(shiny_perfect_count) + str(
        perfect_count) + str(near_count) + str(miss_count) + str(health) + str(modifier) + str(clear_type)
    y = str(user_id) + song_hash
    checksum = md5(x+md5(y))
    if checksum != submission_hash:
        return False

    return True


def arc_all_post(user_id, scores_data, clearlamps_data, clearedsongs_data, unlocklist_data, installid_data, devicemodelname_data, story_data):
    # 向云端同步，无返回
    with Connect() as c:
        now = int(time.time() * 1000)
        c.execute('''delete from user_save where user_id=:a''', {'a': user_id})
        c.execute('''insert into user_save values(:a,:b,:c,:d,:e,:f,:g,:h,:i)''', {
            'a': user_id, 'b': scores_data, 'c': clearlamps_data, 'd': clearedsongs_data, 'e': unlocklist_data, 'f': installid_data, 'g': devicemodelname_data, 'h': story_data, 'i': now})
    return None


def arc_all_get(user_id):
    # 从云端同步，返回字典

    scores_data = []
    clearlamps_data = []
    clearedsongs_data = []
    unlocklist_data = []
    installid_data = ''
    devicemodelname_data = ''
    story_data = []
    createdAt = 0

    with Connect() as c:
        c.execute('''select * from user_save where user_id=:a''',
                  {'a': user_id})
        x = c.fetchone()

        if x:
            scores_data = json.loads(x[1])[""]
            clearlamps_data = json.loads(x[2])[""]
            clearedsongs_data = json.loads(x[3])[""]
            unlocklist_data = json.loads(x[4])[""]
            installid_data = json.loads(x[5])["val"]
            devicemodelname_data = json.loads(x[6])["val"]
            story_data = json.loads(x[7])[""]
            if x[8]:
                createdAt = int(x[8])

    if Config.SAVE_FULL_UNLOCK:
        installid_data = "0fcec8ed-7b62-48e2-9d61-55041a22b123"
        story_data = [{
            "ma": 1,
            "mi": 1,
            "c": True,
            "r": True
        }, {
            "ma": 1,
            "mi": 2,
            "c": True,
            "r": True
        }, {
            "ma": 1,
            "mi": 3,
            "c": True,
            "r": True
        }, {
            "ma": 1,
            "mi": 4,
            "c": True,
            "r": True
        }, {
            "ma": 1,
            "mi": 5,
            "c": True,
            "r": True
        }, {
            "ma": 1,
            "mi": 6,
            "c": True,
            "r": True
        }, {
            "ma": 1,
            "mi": 7,
            "c": True,
            "r": True
        }, {
            "ma": 1,
            "mi": 8,
            "c": True,
            "r": True
        }, {
            "ma": 1,
            "mi": 9,
            "c": True,
            "r": True
        }, {
            "ma": 2,
            "mi": 1,
            "c": True,
            "r": True
        }, {
            "ma": 2,
            "mi": 2,
            "c": True,
            "r": True
        }, {
            "ma": 2,
            "mi": 3,
            "c": True,
            "r": True
        }, {
            "ma": 2,
            "mi": 4,
            "c": True,
            "r": True
        }, {
            "ma": 2,
            "mi": 5,
            "c": True,
            "r": True
        }, {
            "ma": 2,
            "mi": 6,
            "c": True,
            "r": True
        }, {
            "ma": 2,
            "mi": 7,
            "c": True,
            "r": True
        }, {
            "ma": 2,
            "mi": 8,
            "c": True,
            "r": True
        }, {
            "ma": 2,
            "mi": 9,
            "c": True,
            "r": True
        }, {
            "ma": 100,
            "mi": 1,
            "c": True,
            "r": True
        }, {
            "ma": 100,
            "mi": 2,
            "c": True,
            "r": True
        }, {
            "ma": 100,
            "mi": 3,
            "c": True,
            "r": True
        }, {
            "ma": 100,
            "mi": 4,
            "c": True,
            "r": True
        }, {
            "ma": 100,
            "mi": 5,
            "c": True,
            "r": True
        }, {
            "ma": 101,
            "mi": 1,
            "c": True,
            "r": True
        }, {
            "ma": 101,
            "mi": 2,
            "c": True,
            "r": True
        }, {
            "ma": 101,
            "mi": 3,
            "c": True,
            "r": True
        }, {
            "ma": 101,
            "mi": 4,
            "c": True,
            "r": True
        }, {
            "ma": 101,
            "mi": 5,
            "c": True,
            "r": True
        }, {
            "ma": 101,
            "mi": 6,
            "c": True,
            "r": True
        }, {
            "ma": 101,
            "mi": 7,
            "c": True,
            "r": True
        }, {
            "ma": 101,
            "mi": 8,
            "c": True,
            "r": True
        }, {
            "ma": 3,
            "mi": 1,
            "c": True,
            "r": True
        }, {
            "ma": 3,
            "mi": 2,
            "c": True,
            "r": True
        }, {
            "ma": 3,
            "mi": 3,
            "c": True,
            "r": True
        }, {
            "ma": 3,
            "mi": 4,
            "c": True,
            "r": True
        }, {
            "ma": 3,
            "mi": 5,
            "c": True,
            "r": True
        }, {
            "ma": 3,
            "mi": 6,
            "c": True,
            "r": True
        }, {
            "ma": 4,
            "mi": 1,
            "c": True,
            "r": True
        }, {
            "ma": 4,
            "mi": 2,
            "c": True,
            "r": True
        }, {
            "ma": 4,
            "mi": 3,
            "c": True,
            "r": True
        }, {
            "ma": 4,
            "mi": 4,
            "c": True,
            "r": True
        }, {
            "ma": 4,
            "mi": 5,
            "c": True,
            "r": True
        }, {
            "ma": 4,
            "mi": 6,
            "c": True,
            "r": True
        }, {
            "ma": 4,
            "mi": 7,
            "c": True,
            "r": True
        }, {
            "ma": 4,
            "mi": 8,
            "c": True,
            "r": True
        }, {
            "ma": 5,
            "mi": 1,
            "c": True,
            "r": True
        }, {
            "ma": 5,
            "mi": 2,
            "c": True,
            "r": True
        }, {
            "ma": 5,
            "mi": 3,
            "c": True,
            "r": True
        }, {
            "ma": 5,
            "mi": 4,
            "c": True,
            "r": True
        }, {
            "ma": 5,
            "mi": 5,
            "c": True,
            "r": True
        }, {
            "ma": 5,
            "mi": 6,
            "c": True,
            "r": True
        }, {
            "ma": 6,
            "mi": 1,
            "c": True,
            "r": True
        }, {
            "ma": 6,
            "mi": 2,
            "c": True,
            "r": True
        }, {
            "ma": 6,
            "mi": 3,
            "c": True,
            "r": True
        }, {
            "ma": 7,
            "mi": 1,
            "c": True,
            "r": True
        }, {
            "ma": 7,
            "mi": 2,
            "c": True,
            "r": True
        }, {
            "ma": 7,
            "mi": 3,
            "c": True,
            "r": True
        }, {
            "ma": 7,
            "mi": 4,
            "c": True,
            "r": True
        }, {
            "ma": 7,
            "mi": 5,
            "c": True,
            "r": True
        }, {
            "ma": 7,
            "mi": 6,
            "c": True,
            "r": True
        }, {
            "ma": 8,
            "mi": 1,
            "c": True,
            "r": True
        }, {
            "ma": 8,
            "mi": 2,
            "c": True,
            "r": True
        }, {
            "ma": 8,
            "mi": 3,
            "c": True,
            "r": True
        }]
        unlocklist_data = [{
            "unlock_key": "worldvanquisher|2|0",
            "complete": 1
        }, {
            "unlock_key": "worldvanquisher|1|0",
            "complete": 1
        }, {
            "unlock_key": "worldexecuteme|2|0",
            "complete": 1
        }, {
            "unlock_key": "viyellastears|2|0",
            "complete": 1
        }, {
            "unlock_key": "viyellastears|1|0",
            "complete": 1
        }, {
            "unlock_key": "viciousheroism|2|0",
            "complete": 1
        }, {
            "unlock_key": "vector|2|0",
            "complete": 1
        }, {
            "unlock_key": "valhallazero|2|0",
            "complete": 1
        }, {
            "unlock_key": "tiferet|1|0",
            "complete": 1
        }, {
            "unlock_key": "tiemedowngently|1|0",
            "complete": 1
        }, {
            "unlock_key": "tempestissimo|0|101",
            "complete": 100
        }, {
            "unlock_key": "syro|2|0",
            "complete": 1
        }, {
            "unlock_key": "suomi|1|0",
            "complete": 1
        }, {
            "unlock_key": "solitarydream|2|0",
            "complete": 1
        }, {
            "unlock_key": "snowwhite|2|0",
            "complete": 1
        }, {
            "unlock_key": "sheriruth|2|0",
            "complete": 1
        }, {
            "unlock_key": "senkyou|2|0",
            "complete": 1
        }, {
            "unlock_key": "senkyou|1|0",
            "complete": 1
        }, {
            "unlock_key": "scarletlance|2|0",
            "complete": 1
        }, {
            "unlock_key": "scarletlance|1|0",
            "complete": 1
        }, {
            "unlock_key": "rugie|2|0",
            "complete": 1
        }, {
            "unlock_key": "rise|2|0",
            "complete": 1
        }, {
            "unlock_key": "revixy|2|0",
            "complete": 1
        }, {
            "unlock_key": "reinvent|2|0",
            "complete": 1
        }, {
            "unlock_key": "reinvent|1|0",
            "complete": 1
        }, {
            "unlock_key": "redandblue|2|0",
            "complete": 1
        }, {
            "unlock_key": "redandblue|1|0",
            "complete": 1
        }, {
            "unlock_key": "rabbitintheblackroom|2|0",
            "complete": 1
        }, {
            "unlock_key": "rabbitintheblackroom|1|0",
            "complete": 1
        }, {
            "unlock_key": "worldexecuteme|1|0",
            "complete": 1
        }, {
            "unlock_key": "ringedgenesis|2|0",
            "complete": 1
        }, {
            "unlock_key": "quon|1|0",
            "complete": 1
        }, {
            "unlock_key": "qualia|2|0",
            "complete": 1
        }, {
            "unlock_key": "purgatorium|2|0",
            "complete": 1
        }, {
            "unlock_key": "supernova|2|0",
            "complete": 1
        }, {
            "unlock_key": "saikyostronger|2|3|einherjar|2",
            "complete": 1
        }, {
            "unlock_key": "purgatorium|1|0",
            "complete": 1
        }, {
            "unlock_key": "pragmatism|2|0",
            "complete": 1
        }, {
            "unlock_key": "ouroboros|2|0",
            "complete": 1
        }, {
            "unlock_key": "ouroboros|1|0",
            "complete": 1
        }, {
            "unlock_key": "oracle|1|0",
            "complete": 1
        }, {
            "unlock_key": "onelastdrive|2|0",
            "complete": 1
        }, {
            "unlock_key": "onelastdrive|1|0",
            "complete": 1
        }, {
            "unlock_key": "omegafour|1|0",
            "complete": 1
        }, {
            "unlock_key": "oblivia|2|0",
            "complete": 1
        }, {
            "unlock_key": "pragmatism|1|0",
            "complete": 1
        }, {
            "unlock_key": "nhelv|2|0",
            "complete": 1
        }, {
            "unlock_key": "memoryforest|1|0",
            "complete": 1
        }, {
            "unlock_key": "melodyoflove|2|0",
            "complete": 1
        }, {
            "unlock_key": "saikyostronger|2|3|laqryma|2",
            "complete": 1
        }, {
            "unlock_key": "omegafour|2|0",
            "complete": 1
        }, {
            "unlock_key": "melodyoflove|1|0",
            "complete": 1
        }, {
            "unlock_key": "lucifer|2|0",
            "complete": 1
        }, {
            "unlock_key": "lucifer|1|0",
            "complete": 1
        }, {
            "unlock_key": "lostdesire|2|0",
            "complete": 1
        }, {
            "unlock_key": "tiemedowngently|2|0",
            "complete": 1
        }, {
            "unlock_key": "lostdesire|1|0",
            "complete": 1
        }, {
            "unlock_key": "viciousheroism|1|0",
            "complete": 1
        }, {
            "unlock_key": "flyburg|1|0",
            "complete": 1
        }, {
            "unlock_key": "lostcivilization|2|0",
            "complete": 1
        }, {
            "unlock_key": "infinityheaven|1|0",
            "complete": 1
        }, {
            "unlock_key": "ignotus|2|0",
            "complete": 1
        }, {
            "unlock_key": "snowwhite|1|0",
            "complete": 1
        }, {
            "unlock_key": "partyvinyl|1|0",
            "complete": 1
        }, {
            "unlock_key": "axiumcrisis|1|0",
            "complete": 1
        }, {
            "unlock_key": "ifi|2|0",
            "complete": 1
        }, {
            "unlock_key": "jump|2|0",
            "complete": 1
        }, {
            "unlock_key": "harutopia|2|0",
            "complete": 1
        }, {
            "unlock_key": "revixy|1|0",
            "complete": 1
        }, {
            "unlock_key": "aterlbus|1|0",
            "complete": 1
        }, {
            "unlock_key": "linearaccelerator|2|0",
            "complete": 1
        }, {
            "unlock_key": "guardina|2|0",
            "complete": 1
        }, {
            "unlock_key": "corpssansorganes|2|0",
            "complete": 1
        }, {
            "unlock_key": "linearaccelerator|1|0",
            "complete": 1
        }, {
            "unlock_key": "guardina|1|0",
            "complete": 1
        }, {
            "unlock_key": "saikyostronger|2|0",
            "complete": 1
        }, {
            "unlock_key": "guardina|0|0",
            "complete": 1
        }, {
            "unlock_key": "jump|1|0",
            "complete": 1
        }, {
            "unlock_key": "oshamascramble|2|0",
            "complete": 1
        }, {
            "unlock_key": "blaster|2|0",
            "complete": 1
        }, {
            "unlock_key": "grievouslady|2|101",
            "complete": 100
        }, {
            "unlock_key": "partyvinyl|2|0",
            "complete": 1
        }, {
            "unlock_key": "darakunosono|1|0",
            "complete": 1
        }, {
            "unlock_key": "grievouslady|1|101",
            "complete": 100
        }, {
            "unlock_key": "valhallazero|1|0",
            "complete": 1
        }, {
            "unlock_key": "grimheart|1|0",
            "complete": 1
        }, {
            "unlock_key": "ifi|1|0",
            "complete": 1
        }, {
            "unlock_key": "gothiveofra|1|0",
            "complete": 1
        }, {
            "unlock_key": "tempestissimo|3|101",
            "complete": 100
        }, {
            "unlock_key": "chronostasis|2|0",
            "complete": 1
        }, {
            "unlock_key": "gloryroad|2|0",
            "complete": 1
        }, {
            "unlock_key": "supernova|1|0",
            "complete": 1
        }, {
            "unlock_key": "singularity|2|0",
            "complete": 1
        }, {
            "unlock_key": "gloryroad|0|0",
            "complete": 1
        }, {
            "unlock_key": "shadesoflight|1|0",
            "complete": 1
        }, {
            "unlock_key": "kanagawa|2|0",
            "complete": 1
        }, {
            "unlock_key": "genesis|1|0",
            "complete": 1
        }, {
            "unlock_key": "fractureray|1|101",
            "complete": 100
        }, {
            "unlock_key": "freefall|2|0",
            "complete": 1
        }, {
            "unlock_key": "fractureray|2|101",
            "complete": 100
        }, {
            "unlock_key": "monochromeprincess|2|0",
            "complete": 1
        }, {
            "unlock_key": "babaroque|1|0",
            "complete": 1
        }, {
            "unlock_key": "flyburg|2|0",
            "complete": 1
        }, {
            "unlock_key": "oracle|2|0",
            "complete": 1
        }, {
            "unlock_key": "clotho|2|0",
            "complete": 1
        }, {
            "unlock_key": "gou|2|0",
            "complete": 1
        }, {
            "unlock_key": "felis|2|0",
            "complete": 1
        }, {
            "unlock_key": "qualia|1|0",
            "complete": 1
        }, {
            "unlock_key": "etherstrike|2|0",
            "complete": 1
        }, {
            "unlock_key": "etherstrike|1|0",
            "complete": 1
        }, {
            "unlock_key": "syro|1|0",
            "complete": 1
        }, {
            "unlock_key": "anokumene|2|0",
            "complete": 1
        }, {
            "unlock_key": "essenceoftwilight|2|0",
            "complete": 1
        }, {
            "unlock_key": "shadesoflight|2|0",
            "complete": 1
        }, {
            "unlock_key": "espebranch|2|0",
            "complete": 1
        }, {
            "unlock_key": "tempestissimo|1|101",
            "complete": 100
        }, {
            "unlock_key": "nhelv|1|0",
            "complete": 1
        }, {
            "unlock_key": "conflict|1|0",
            "complete": 1
        }, {
            "unlock_key": "espebranch|1|0",
            "complete": 1
        }, {
            "unlock_key": "lostcivilization|1|0",
            "complete": 1
        }, {
            "unlock_key": "goodtek|2|0",
            "complete": 1
        }, {
            "unlock_key": "dandelion|2|0",
            "complete": 1
        }, {
            "unlock_key": "suomi|2|0",
            "complete": 1
        }, {
            "unlock_key": "dandelion|1|0",
            "complete": 1
        }, {
            "unlock_key": "oblivia|1|0",
            "complete": 1
        }, {
            "unlock_key": "cyberneciacatharsis|1|0",
            "complete": 1
        }, {
            "unlock_key": "quon|2|0",
            "complete": 1
        }, {
            "unlock_key": "chronostasis|1|0",
            "complete": 1
        }, {
            "unlock_key": "bookmaker|2|0",
            "complete": 1
        }, {
            "unlock_key": "heavensdoor|1|0",
            "complete": 1
        }, {
            "unlock_key": "tempestissimo|2|101",
            "complete": 100
        }, {
            "unlock_key": "cyaegha|2|0",
            "complete": 1
        }, {
            "unlock_key": "axiumcrisis|2|0",
            "complete": 1
        }, {
            "unlock_key": "blrink|2|0",
            "complete": 1
        }, {
            "unlock_key": "rise|1|0",
            "complete": 1
        }, {
            "unlock_key": "cyanine|1|0",
            "complete": 1
        }, {
            "unlock_key": "corpssansorganes|0|0",
            "complete": 1
        }, {
            "unlock_key": "vector|1|0",
            "complete": 1
        }, {
            "unlock_key": "infinityheaven|2|0",
            "complete": 1
        }, {
            "unlock_key": "essenceoftwilight|1|0",
            "complete": 1
        }, {
            "unlock_key": "conflict|2|0",
            "complete": 1
        }, {
            "unlock_key": "singularity|1|0",
            "complete": 1
        }, {
            "unlock_key": "harutopia|1|0",
            "complete": 1
        }, {
            "unlock_key": "cyberneciacatharsis|2|0",
            "complete": 1
        }, {
            "unlock_key": "ignotus|1|0",
            "complete": 1
        }, {
            "unlock_key": "nirvluce|1|0",
            "complete": 1
        }, {
            "unlock_key": "monochromeprincess|1|0",
            "complete": 1
        }, {
            "unlock_key": "lethaeus|1|0",
            "complete": 1
        }, {
            "unlock_key": "clotho|1|0",
            "complete": 1
        }, {
            "unlock_key": "aterlbus|2|0",
            "complete": 1
        }, {
            "unlock_key": "dreaminattraction|2|0",
            "complete": 1
        }, {
            "unlock_key": "solitarydream|1|0",
            "complete": 1
        }, {
            "unlock_key": "ringedgenesis|1|0",
            "complete": 1
        }, {
            "unlock_key": "corpssansorganes|1|0",
            "complete": 1
        }, {
            "unlock_key": "buchigireberserker|2|0",
            "complete": 1
        }, {
            "unlock_key": "bookmaker|1|0",
            "complete": 1
        }, {
            "unlock_key": "heavensdoor|2|0",
            "complete": 1
        }, {
            "unlock_key": "genesis|2|0",
            "complete": 1
        }, {
            "unlock_key": "halcyon|2|0",
            "complete": 1
        }, {
            "unlock_key": "saikyostronger|2|3|izana|2",
            "complete": 1
        }, {
            "unlock_key": "memoryforest|2|0",
            "complete": 1
        }, {
            "unlock_key": "halcyon|1|0",
            "complete": 1
        }, {
            "unlock_key": "felis|1|0",
            "complete": 1
        }, {
            "unlock_key": "toaliceliddell|2|0",
            "complete": 1
        }, {
            "unlock_key": "blrink|1|0",
            "complete": 1
        }, {
            "unlock_key": "grievouslady|0|101",
            "complete": 100
        }, {
            "unlock_key": "buchigireberserker|2|3|gothiveofra|2",
            "complete": 1
        }, {
            "unlock_key": "kanagawa|1|0",
            "complete": 1
        }, {
            "unlock_key": "darakunosono|2|0",
            "complete": 1
        }, {
            "unlock_key": "freefall|1|0",
            "complete": 1
        }, {
            "unlock_key": "nirvluce|2|0",
            "complete": 1
        }, {
            "unlock_key": "cyanine|2|0",
            "complete": 1
        }, {
            "unlock_key": "goodtek|1|0",
            "complete": 1
        }, {
            "unlock_key": "buchigireberserker|2|3|ouroboros|2",
            "complete": 1
        }, {
            "unlock_key": "fractureray|0|101",
            "complete": 100
        }, {
            "unlock_key": "blaster|1|0",
            "complete": 1
        }, {
            "unlock_key": "dreaminattraction|1|0",
            "complete": 1
        }, {
            "unlock_key": "toaliceliddell|1|0",
            "complete": 1
        }, {
            "unlock_key": "oshamascramble|1|0",
            "complete": 1
        }, {
            "unlock_key": "gothiveofra|2|0",
            "complete": 1
        }, {
            "unlock_key": "tiferet|2|0",
            "complete": 1
        }, {
            "unlock_key": "grimheart|2|0",
            "complete": 1
        }, {
            "unlock_key": "amazingmightyyyy|1|0",
            "complete": 1
        }, {
            "unlock_key": "lethaeus|2|0",
            "complete": 1
        }, {
            "unlock_key": "rugie|1|0",
            "complete": 1
        }, {
            "unlock_key": "gou|1|0",
            "complete": 1
        }, {
            "unlock_key": "sheriruth|1|0",
            "complete": 1
        }, {
            "unlock_key": "babaroque|2|0",
            "complete": 1
        }, {
            "unlock_key": "aiueoon|2|0",
            "complete": 1
        }, {
            "unlock_key": "gloryroad|1|0",
            "complete": 1
        }, {
            "unlock_key": "cyaegha|1|0",
            "complete": 1
        }, {
            "unlock_key": "amazingmightyyyy|2|0",
            "complete": 1
        }, {
            "unlock_key": "anokumene|1|0",
            "complete": 1
        }]

    return {
        "user_id": user_id,
        "story": {
            "": story_data
        },
        "devicemodelname": {
            "val": devicemodelname_data
        },
        "installid":  {
            "val": installid_data
        },
        "unlocklist": {
            "": unlocklist_data
        },
        "clearedsongs": {
            "": clearedsongs_data
        },
        "clearlamps": {
            "": clearlamps_data
        },
        "scores": {
            "": scores_data
        },
        "version": {
            "val": 1
        },
        "createdAt": createdAt
    }
