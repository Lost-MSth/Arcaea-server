import sqlite3
import time
import json


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


def get_score(c, user_id, song_id, difficulty):
    # 根据user_id、song_id、难度得到该曲目最好成绩，返回字典
    c.execute('''select * from best_score where user_id = :a and song_id = :b and difficulty = :c''',
              {'a': user_id, 'b': song_id, 'c': difficulty})
    x = c.fetchone()
    if x is not None:
        c.execute('''select name, character_id, is_skill_sealed, is_char_uncapped from user where user_id = :a''', {
                  'a': user_id})
        y = c.fetchone()
        if y is not None:
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
                "character": y[1],
                "is_skill_sealed": int2b(y[2]),
                "is_char_uncapped": int2b(y[3])
            }
        else:
            return {}
    else:
        return {}


def arc_score_friend(user_id, song_id, difficulty, limit=50):
    # 得到用户好友分数表，默认最大50个
    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    c.execute('''select user_id from best_score where user_id in (select :user_id union select user_id_other from friend where user_id_me = :user_id) and song_id = :song_id and difficulty = :difficulty order by score DESC, time_played DESC limit :limit''', {
              'user_id': user_id, 'song_id': song_id, 'difficulty': difficulty, 'limit': limit})
    x = c.fetchall()
    r = []
    if x != []:
        rank = 0
        for i in x:
            rank += 1
            y = get_score(c, i[0], song_id, difficulty)
            y['rank'] = rank
            r.append(y)

    conn.commit()
    conn.close()
    return r


def arc_score_top(song_id, difficulty, limit=20):
    # 得到top分数表，默认最多20个，如果是负数则全部查询
    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    if limit >= 0:
        c.execute('''select user_id from best_score where song_id = :song_id and difficulty = :difficulty order by score DESC, time_played DESC limit :limit''', {
            'song_id': song_id, 'difficulty': difficulty, 'limit': limit})
    else:
        c.execute('''select user_id from best_score where song_id = :song_id and difficulty = :difficulty order by score DESC, time_played DESC''', {
            'song_id': song_id, 'difficulty': difficulty})
    x = c.fetchall()
    r = []
    if x != []:
        rank = 0
        for i in x:
            rank += 1
            y = get_score(c, i[0], song_id, difficulty)
            y['rank'] = rank
            r.append(y)

    conn.commit()
    conn.close()
    return r


def arc_score_me(user_id, song_id, difficulty, limit=20):
    # 得到用户的排名，默认最大20个
    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    r = []
    c.execute('''select exists(select * from best_score where user_id = :user_id and song_id = :song_id and difficulty = :difficulty)''', {
              'user_id': user_id, 'song_id': song_id, 'difficulty': difficulty})
    if c.fetchone() == (1,):
        c.execute('''select count(*) from best_score where song_id = :song_id and difficulty = :difficulty and (score>(select score from best_score where user_id = :user_id and song_id = :song_id and difficulty = :difficulty) or (score>(select score from best_score where user_id = :user_id and song_id = :song_id and difficulty = :difficulty) and time_played > (select time_played from best_score where user_id = :user_id and song_id = :song_id and difficulty = :difficulty)) )''', {
            'user_id': user_id, 'song_id': song_id, 'difficulty': difficulty})
        x = c.fetchone()
        myrank = int(x[0]) + 1
        if myrank <= 4:  # 排名在前4
            conn.commit()
            conn.close()
            return arc_score_top(song_id, difficulty, limit)
        elif myrank >= 5 and myrank <= 9999 - limit + 4:  # 万名内，前面有4个人
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

    conn.commit()
    conn.close()
    return r


def get_one_ptt(song_id, difficulty, score: int) -> float:
    # 单曲ptt计算
    conn = sqlite3.connect('./database/arcsong.db')
    c = conn.cursor()
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
    defnum = 10.0  # 没在库里的全部当做定数10.0，不过要小心recent30表可能会被污染
    if x is not None and x != '':
        defnum = float(x[0]) / 10
        if defnum <= 0:
            defnum = 11.0  # 缺少难度的当做定数11.0

    if score >= 10000000:
        ptt = defnum + 2
    elif score < 9800000:
        ptt = defnum + (score-9500000) / 300000
        if ptt < 0:
            ptt = 0
    else:
        ptt = defnum + 1 + (score-9800000) / 200000

    conn.commit()
    conn.close()
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


def update_recent30(c, user_id, song_id, rating):
    # 刷新r30，这里的判断方法存疑
    c.execute('''select * from recent30 where user_id = :a''', {'a': user_id})
    x = c.fetchone()
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
        n = len(song_id)
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
    for i in range(r30_id, 0, -1):
        a[i] = a[i-1]
        b[i] = b[i-1]
    a[0] = rating
    b[0] = song_id
    c.execute('''delete from recent30 where user_id = :a''', {'a': user_id})
    sql = 'insert into recent30 values(' + str(user_id)
    for i in range(0, 30):
        if a[i] is not None and b[i] is not None:
            sql = sql + ',' + str(a[i]) + ',"' + b[i] + '"'
        else:
            sql = sql + ',0,""'

    sql = sql + ')'
    c.execute(sql)
    return None


def get_user_ptt(c, user_id) -> int:
    # 总ptt计算
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

    return int(sumr/40*100)


def arc_score_post(user_id, song_id, difficulty, score, shiny_perfect_count, perfect_count, near_count, miss_count, health, modifier, beyond_gauge, clear_type):
    # 分数上传，返回变化后的ptt
    # beyond_gauge是个什么呀？不管了，扔了

    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    rating = get_one_ptt(song_id, difficulty, score)
    now = int(time.time() * 1000)
    # recent 更新
    c.execute('''update user set song_id = :b, difficulty = :c, score = :d, shiny_perfect_count = :e, perfect_count = :f, near_count = :g, miss_count = :h, health = :i, modifier = :j, clear_type = :k, rating = :l, time_played = :m  where user_id = :a''', {
              'a': user_id, 'b': song_id, 'c': difficulty, 'd': score, 'e': shiny_perfect_count, 'f': perfect_count, 'g': near_count, 'h': miss_count, 'i': health, 'j': modifier, 'k': clear_type, 'l': rating, 'm': now})
    # recent30 更新
    update_recent30(c, user_id, song_id+str(difficulty), rating)
    # 成绩录入
    c.execute('''select score, best_clear_type from best_score where user_id = :a and song_id = :b and difficulty = :c''', {
              'a': user_id, 'b': song_id, 'c': difficulty})
    now = int(now // 1000)
    x = c.fetchone()
    if x is None:
        c.execute('''insert into best_score values(:a,:b,:c,:d,:e,:f,:g,:h,:i,:j,:k,:l,:m,:n)''', {
                  'a': user_id, 'b': song_id, 'c': difficulty, 'd': score, 'e': shiny_perfect_count, 'f': perfect_count, 'g': near_count, 'h': miss_count, 'i': health, 'j': modifier, 'k': now, 'l': clear_type, 'm': clear_type, 'n': rating})
    else:
        if get_song_state(clear_type) > get_song_state(int(x[1])):  # 状态更新
            c.execute('''update best_score set best_clear_type = :a where user_id = :b and song_id = :c and difficulty = :d''', {
                      'a': clear_type, 'b': user_id, 'c': song_id, 'd': difficulty})
        if score >= int(x[0]):  # 成绩更新
            c.execute('''update best_score set score = :d, shiny_perfect_count = :e, perfect_count = :f, near_count = :g, miss_count = :h, health = :i, modifier = :j, clear_type = :k, rating = :l, time_played = :m  where user_id = :a and song_id = :b and difficulty = :c ''', {
                'a': user_id, 'b': song_id, 'c': difficulty, 'd': score, 'e': shiny_perfect_count, 'f': perfect_count, 'g': near_count, 'h': miss_count, 'i': health, 'j': modifier, 'k': clear_type, 'l': rating, 'm': now})
    # 总PTT更新
    ptt = get_user_ptt(c, user_id)
    c.execute('''update user set rating_ptt = :a where user_id = :b''', {
              'a': ptt, 'b': user_id})
    conn.commit()
    conn.close()
    return ptt


def arc_all_post(user_id, scores_data, clearlamps_data):
    # 向云端同步，无返回
    # 注意，best_score表不比较，直接覆盖
    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    scores = json.loads(scores_data)[""]
    clearlamps = json.loads(clearlamps_data)[""]
    clear_song_id_difficulty = []
    clear_state = []
    for i in clearlamps:
        clear_song_id_difficulty.append(i['song_id']+str(i['difficulty']))
        clear_state.append(i['clear_type'])

    for i in scores:
        rating = get_one_ptt(i['song_id'], i['difficulty'], i['score'])
        try:
            index = clear_song_id_difficulty.index(
                i['song_id'] + str(i['difficulty']))
        except:
            index = -1
        if index != -1:
            clear_type = clear_state[index]
        else:
            clear_type = 0
        c.execute('''delete from best_score where user_id = :a and song_id = :b and difficulty = :c''', {
                  'a': user_id, 'b': i['song_id'], 'c': i['difficulty']})
        c.execute('''insert into best_score values(:a,:b,:c,:d,:e,:f,:g,:h,:i,:j,:k,:l,:m,:n)''', {
                  'a': user_id, 'b': i['song_id'], 'c': i['difficulty'], 'd': i['score'], 'e': i['shiny_perfect_count'], 'f': i['perfect_count'], 'g': i['near_count'], 'h': i['miss_count'], 'i': i['health'], 'j': i['modifier'], 'k': i['time_played'], 'l': clear_type, 'm': clear_type, 'n': rating})

    ptt = get_user_ptt(c, user_id)  # 更新PTT
    c.execute('''update user set rating_ptt = :a where user_id = :b''', {
              'a': ptt, 'b': user_id})
    conn.commit()
    conn.close()
    return None


def arc_all_get(user_id):
    # 从云端同步，返回字典
    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    c.execute('''select * from best_score where user_id = :a''',
              {'a': user_id})
    x = c.fetchall()
    song_1 = []
    song_2 = []
    song_3 = []
    if x != []:
        for i in x:
            if i[11] != 0:
                song_1.append({
                    "grade": get_song_grade(i[3]),
                    "difficulty": i[2],
                    "song_id": i[1]
                })
                song_2.append({
                    "ct": 0,
                    "clear_type": i[11],
                    "difficulty": i[2],
                    "song_id": i[1]
                })
            song_3.append({
                "ct": 0,
                "time_played": i[10],
                "modifier": i[9],
                "health": i[8],
                "miss_count": i[7],
                "near_count": i[6],
                "perfect_count": i[5],
                "shiny_perfect_count": i[4],
                "score": i[3],
                "difficulty": i[2],
                "version": 1,
                "song_id": i[1]
            })

    conn.commit()
    conn.close()
    return {
        "user_id": user_id,
        "story": {
            "": [{
                "r": True,
                "c": True,
                "mi": 1,
                "ma": 1
            }, {
                "r": True,
                "c": True,
                "mi": 2,
                "ma": 1
            }, {
                "r": True,
                "c": True,
                "mi": 3,
                "ma": 1
            }, {
                "r": True,
                "c": True,
                "mi": 4,
                "ma": 1
            }, {
                "r": True,
                "c": True,
                "mi": 5,
                "ma": 1
            }, {
                "r": True,
                "c": True,
                "mi": 6,
                "ma": 1
            }, {
                "r": True,
                "c": True,
                "mi": 7,
                "ma": 1
            }, {
                "r": True,
                "c": True,
                "mi": 8,
                "ma": 1
            }, {
                "r": True,
                "c": True,
                "mi": 9,
                "ma": 1
            }, {
                "r": True,
                "c": True,
                "mi": 1,
                "ma": 2
            }, {
                "r": True,
                "c": True,
                "mi": 2,
                "ma": 2
            }, {
                "r": True,
                "c": True,
                "mi": 3,
                "ma": 2
            }, {
                "r": True,
                "c": True,
                "mi": 4,
                "ma": 2
            }, {
                "r": True,
                "c": True,
                "mi": 5,
                "ma": 2
            }, {
                "r": True,
                "c": True,
                "mi": 6,
                "ma": 2
            }, {
                "r": True,
                "c": True,
                "mi": 7,
                "ma": 2
            }, {
                "r": True,
                "c": True,
                "mi": 8,
                "ma": 2
            }, {
                "r": True,
                "c": True,
                "mi": 9,
                "ma": 2
            }, {
                "r": True,
                "c": True,
                "mi": 1,
                "ma": 100
            }, {
                "r": True,
                "c": True,
                "mi": 2,
                "ma": 100
            }, {
                "r": True,
                "c": True,
                "mi": 3,
                "ma": 100
            }, {
                "r": True,
                "c": True,
                "mi": 4,
                "ma": 100
            }, {
                "r": True,
                "c": True,
                "mi": 5,
                "ma": 100
            }, {
                "r": True,
                "c": True,
                "mi": 1,
                "ma": 101
            }, {
                "r": True,
                "c": True,
                "mi": 2,
                "ma": 101
            }, {
                "r": True,
                "c": True,
                "mi": 3,
                "ma": 101
            }, {
                "r": True,
                "c": True,
                "mi": 4,
                "ma": 101
            }, {
                "r": True,
                "c": True,
                "mi": 5,
                "ma": 101
            }, {
                "r": True,
                "c": True,
                "mi": 6,
                "ma": 101
            }, {
                "r": True,
                "c": True,
                "mi": 7,
                "ma": 101
            }, {
                "r": True,
                "c": True,
                "mi": 8,
                "ma": 101
            }, {
                "r": True,
                "c": True,
                "mi": 1,
                "ma": 3
            }, {
                "r": True,
                "c": True,
                "mi": 2,
                "ma": 3
            }, {
                "r": True,
                "c": True,
                "mi": 3,
                "ma": 3
            }, {
                "r": True,
                "c": True,
                "mi": 4,
                "ma": 3
            }, {
                "r": True,
                "c": True,
                "mi": 5,
                "ma": 3
            }, {
                "r": True,
                "c": True,
                "mi": 6,
                "ma": 3
            }, {
                "r": True,
                "c": True,
                "mi": 1,
                "ma": 4
            }, {
                "r": True,
                "c": True,
                "mi": 2,
                "ma": 4
            }, {
                "r": True,
                "c": True,
                "mi": 3,
                "ma": 4
            }, {
                "r": True,
                "c": True,
                "mi": 4,
                "ma": 4
            }, {
                "r": True,
                "c": True,
                "mi": 5,
                "ma": 4
            }, {
                "r": True,
                "c": True,
                "mi": 6,
                "ma": 4
            }, {
                "r": True,
                "c": True,
                "mi": 7,
                "ma": 4
            }, {
                "r": True,
                "c": True,
                "mi": 8,
                "ma": 4
            }, {
                "r": True,
                "c": True,
                "mi": 1,
                "ma": 5
            }, {
                "r": True,
                "c": True,
                "mi": 2,
                "ma": 5
            }, {
                "r": True,
                "c": True,
                "mi": 3,
                "ma": 5
            }, {
                "r": True,
                "c": True,
                "mi": 4,
                "ma": 5
            }, {
                "r": True,
                "c": True,
                "mi": 5,
                "ma": 5
            }, {
                "r": True,
                "c": True,
                "mi": 6,
                "ma": 5
            }, {
                "r": True,
                "c": True,
                "mi": 1,
                "ma": 6
            }, {
                "r": True,
                "c": True,
                "mi": 2,
                "ma": 6
            }, {
                "r": True,
                "c": True,
                "mi": 3,
                "ma": 6
            }]
        },
        "devicemodelname": {
            "val": "MopeMope"
        },
        "installid": {
            "val": "b5e064cf-1a3f-4e64-9636-fce4accc9011"
        },
        "unlocklist": {
            "": [{
                "complete": 1,
                "unlock_key": "worldvanquisher|2|0"
            }, {
                "complete": 1,
                "unlock_key": "worldvanquisher|1|0"
            }, {
                "complete": 1,
                "unlock_key": "worldexecuteme|2|0"
            }, {
                "complete": 1,
                "unlock_key": "viciousheroism|2|0"
            }, {
                "complete": 1,
                "unlock_key": "vector|2|0"
            }, {
                "complete": 1,
                "unlock_key": "valhallazero|2|0"
            }, {
                "complete": 1,
                "unlock_key": "tiferet|1|0"
            }, {
                "complete": 1,
                "unlock_key": "tiemedowngently|1|0"
            }, {
                "complete": 1,
                "unlock_key": "tempestissimo|0|101"
            }, {
                "complete": 1,
                "unlock_key": "syro|2|0"
            }, {
                "complete": 1,
                "unlock_key": "suomi|1|0"
            }, {
                "complete": 1,
                "unlock_key": "solitarydream|2|0"
            }, {
                "complete": 1,
                "unlock_key": "snowwhite|2|0"
            }, {
                "complete": 1,
                "unlock_key": "sheriruth|2|0"
            }, {
                "complete": 1,
                "unlock_key": "senkyou|2|0"
            }, {
                "complete": 1,
                "unlock_key": "senkyou|1|0"
            }, {
                "complete": 1,
                "unlock_key": "scarletlance|2|0"
            }, {
                "complete": 1,
                "unlock_key": "scarletlance|1|0"
            }, {
                "complete": 1,
                "unlock_key": "rugie|2|0"
            }, {
                "complete": 1,
                "unlock_key": "rugie|1|0"
            }, {
                "complete": 1,
                "unlock_key": "rise|2|0"
            }, {
                "complete": 1,
                "unlock_key": "revixy|2|0"
            }, {
                "complete": 1,
                "unlock_key": "reinvent|2|0"
            }, {
                "complete": 1,
                "unlock_key": "reinvent|1|0"
            }, {
                "complete": 1,
                "unlock_key": "redandblue|2|0"
            }, {
                "complete": 1,
                "unlock_key": "redandblue|1|0"
            }, {
                "complete": 1,
                "unlock_key": "rabbitintheblackroom|2|0"
            }, {
                "complete": 1,
                "unlock_key": "rabbitintheblackroom|1|0"
            }, {
                "complete": 1,
                "unlock_key": "worldexecuteme|1|0"
            }, {
                "complete": 1,
                "unlock_key": "ringedgenesis|2|0"
            }, {
                "complete": 1,
                "unlock_key": "quon|1|0"
            }, {
                "complete": 1,
                "unlock_key": "qualia|2|0"
            }, {
                "complete": 1,
                "unlock_key": "purgatorium|2|0"
            }, {
                "complete": 1,
                "unlock_key": "supernova|2|0"
            }, {
                "complete": 1,
                "unlock_key": "saikyostronger|2|3|einherjar|2"
            }, {
                "complete": 1,
                "unlock_key": "purgatorium|1|0"
            }, {
                "complete": 1,
                "unlock_key": "pragmatism|2|0"
            }, {
                "complete": 1,
                "unlock_key": "ouroboros|2|0"
            }, {
                "complete": 1,
                "unlock_key": "ouroboros|1|0"
            }, {
                "complete": 1,
                "unlock_key": "oracle|1|0"
            }, {
                "complete": 1,
                "unlock_key": "onelastdrive|2|0"
            }, {
                "complete": 1,
                "unlock_key": "onelastdrive|1|0"
            }, {
                "complete": 1,
                "unlock_key": "oblivia|2|0"
            }, {
                "complete": 1,
                "unlock_key": "memoryforest|1|0"
            }, {
                "complete": 1,
                "unlock_key": "melodyoflove|2|0"
            }, {
                "complete": 1,
                "unlock_key": "saikyostronger|2|3|laqryma|2"
            }, {
                "complete": 1,
                "unlock_key": "melodyoflove|1|0"
            }, {
                "complete": 1,
                "unlock_key": "lucifer|2|0"
            }, {
                "complete": 1,
                "unlock_key": "saikyostronger|2|3|izana|2"
            }, {
                "complete": 1,
                "unlock_key": "halcyon|1|0"
            }, {
                "complete": 1,
                "unlock_key": "memoryforest|2|0"
            }, {
                "complete": 1,
                "unlock_key": "tiemedowngently|2|0"
            }, {
                "complete": 1,
                "unlock_key": "lostdesire|1|0"
            }, {
                "complete": 1,
                "unlock_key": "viciousheroism|1|0"
            }, {
                "complete": 1,
                "unlock_key": "flyburg|1|0"
            }, {
                "complete": 1,
                "unlock_key": "lostcivilization|2|0"
            }, {
                "complete": 1,
                "unlock_key": "infinityheaven|1|0"
            }, {
                "complete": 1,
                "unlock_key": "lostdesire|2|0"
            }, {
                "complete": 1,
                "unlock_key": "ignotus|2|0"
            }, {
                "complete": 1,
                "unlock_key": "harutopia|2|0"
            }, {
                "complete": 1,
                "unlock_key": "revixy|1|0"
            }, {
                "complete": 1,
                "unlock_key": "aterlbus|1|0"
            }, {
                "complete": 1,
                "unlock_key": "linearaccelerator|2|0"
            }, {
                "complete": 1,
                "unlock_key": "guardina|2|0"
            }, {
                "complete": 1,
                "unlock_key": "corpssansorganes|2|0"
            }, {
                "complete": 1,
                "unlock_key": "linearaccelerator|1|0"
            }, {
                "complete": 1,
                "unlock_key": "guardina|1|0"
            }, {
                "complete": 1,
                "unlock_key": "saikyostronger|2|0"
            }, {
                "complete": 1,
                "unlock_key": "guardina|0|0"
            }, {
                "complete": 1,
                "unlock_key": "valhallazero|1|0"
            }, {
                "complete": 1,
                "unlock_key": "grimheart|1|0"
            }, {
                "complete": 1,
                "unlock_key": "blaster|2|0"
            }, {
                "complete": 1,
                "unlock_key": "grievouslady|2|101"
            }, {
                "complete": 1,
                "unlock_key": "partyvinyl|2|0"
            }, {
                "complete": 1,
                "unlock_key": "darakunosono|1|0"
            }, {
                "complete": 1,
                "unlock_key": "grievouslady|1|101"
            }, {
                "complete": 1,
                "unlock_key": "goodtek|1|0"
            }, {
                "complete": 1,
                "unlock_key": "tempestissimo|3|101"
            }, {
                "complete": 1,
                "unlock_key": "chronostasis|2|0"
            }, {
                "complete": 1,
                "unlock_key": "gloryroad|2|0"
            }, {
                "complete": 1,
                "unlock_key": "supernova|1|0"
            }, {
                "complete": 1,
                "unlock_key": "singularity|2|0"
            }, {
                "complete": 1,
                "unlock_key": "gloryroad|0|0"
            }, {
                "complete": 1,
                "unlock_key": "shadesoflight|1|0"
            }, {
                "complete": 1,
                "unlock_key": "kanagawa|2|0"
            }, {
                "complete": 1,
                "unlock_key": "genesis|1|0"
            }, {
                "complete": 1,
                "unlock_key": "fractureray|1|101"
            }, {
                "complete": 1,
                "unlock_key": "freefall|2|0"
            }, {
                "complete": 1,
                "unlock_key": "babaroque|1|0"
            }, {
                "complete": 1,
                "unlock_key": "monochromeprincess|2|0"
            }, {
                "complete": 1,
                "unlock_key": "flyburg|2|0"
            }, {
                "complete": 1,
                "unlock_key": "shadesoflight|2|0"
            }, {
                "complete": 1,
                "unlock_key": "espebranch|2|0"
            }, {
                "complete": 1,
                "unlock_key": "qualia|1|0"
            }, {
                "complete": 1,
                "unlock_key": "etherstrike|2|0"
            }, {
                "complete": 1,
                "unlock_key": "tempestissimo|1|101"
            }, {
                "complete": 1,
                "unlock_key": "conflict|1|0"
            }, {
                "complete": 1,
                "unlock_key": "nhelv|1|0"
            }, {
                "complete": 1,
                "unlock_key": "etherstrike|1|0"
            }, {
                "complete": 1,
                "unlock_key": "syro|1|0"
            }, {
                "complete": 1,
                "unlock_key": "anokumene|2|0"
            }, {
                "complete": 1,
                "unlock_key": "essenceoftwilight|2|0"
            }, {
                "complete": 1,
                "unlock_key": "snowwhite|1|0"
            }, {
                "complete": 1,
                "unlock_key": "partyvinyl|1|0"
            }, {
                "complete": 1,
                "unlock_key": "axiumcrisis|1|0"
            }, {
                "complete": 1,
                "unlock_key": "ifi|2|0"
            }, {
                "complete": 1,
                "unlock_key": "espebranch|1|0"
            }, {
                "complete": 1,
                "unlock_key": "lostcivilization|1|0"
            }, {
                "complete": 1,
                "unlock_key": "goodtek|2|0"
            }, {
                "complete": 1,
                "unlock_key": "dandelion|2|0"
            }, {
                "complete": 1,
                "unlock_key": "suomi|2|0"
            }, {
                "complete": 1,
                "unlock_key": "dandelion|1|0"
            }, {
                "complete": 1,
                "unlock_key": "oblivia|1|0"
            }, {
                "complete": 1,
                "unlock_key": "cyberneciacatharsis|1|0"
            }, {
                "complete": 1,
                "unlock_key": "quon|2|0"
            }, {
                "complete": 1,
                "unlock_key": "bookmaker|2|0"
            }, {
                "complete": 1,
                "unlock_key": "chronostasis|1|0"
            }, {
                "complete": 1,
                "unlock_key": "heavensdoor|1|0"
            }, {
                "complete": 1,
                "unlock_key": "tempestissimo|2|101"
            }, {
                "complete": 1,
                "unlock_key": "cyaegha|2|0"
            }, {
                "complete": 1,
                "unlock_key": "axiumcrisis|2|0"
            }, {
                "complete": 1,
                "unlock_key": "blrink|2|0"
            }, {
                "complete": 1,
                "unlock_key": "rise|1|0"
            }, {
                "complete": 1,
                "unlock_key": "cyanine|1|0"
            }, {
                "complete": 1,
                "unlock_key": "ifi|1|0"
            }, {
                "complete": 1,
                "unlock_key": "aterlbus|2|0"
            }, {
                "complete": 1,
                "unlock_key": "dreaminattraction|2|0"
            }, {
                "complete": 1,
                "unlock_key": "bookmaker|1|0"
            }, {
                "complete": 1,
                "unlock_key": "lucifer|1|0"
            }, {
                "complete": 1,
                "unlock_key": "solitarydream|1|0"
            }, {
                "complete": 1,
                "unlock_key": "ringedgenesis|1|0"
            }, {
                "complete": 1,
                "unlock_key": "corpssansorganes|1|0"
            }, {
                "complete": 1,
                "unlock_key": "vector|1|0"
            }, {
                "complete": 1,
                "unlock_key": "infinityheaven|2|0"
            }, {
                "complete": 1,
                "unlock_key": "essenceoftwilight|1|0"
            }, {
                "complete": 1,
                "unlock_key": "conflict|2|0"
            }, {
                "complete": 1,
                "unlock_key": "singularity|1|0"
            }, {
                "complete": 1,
                "unlock_key": "harutopia|1|0"
            }, {
                "complete": 1,
                "unlock_key": "cyberneciacatharsis|2|0"
            }, {
                "complete": 1,
                "unlock_key": "oracle|2|0"
            }, {
                "complete": 1,
                "unlock_key": "clotho|2|0"
            }, {
                "complete": 1,
                "unlock_key": "corpssansorganes|0|0"
            }, {
                "complete": 1,
                "unlock_key": "ignotus|1|0"
            }, {
                "complete": 1,
                "unlock_key": "monochromeprincess|1|0"
            }, {
                "complete": 1,
                "unlock_key": "nirvluce|1|0"
            }, {
                "complete": 1,
                "unlock_key": "lethaeus|1|0"
            }, {
                "complete": 1,
                "unlock_key": "clotho|1|0"
            }, {
                "complete": 1,
                "unlock_key": "blaster|1|0"
            }, {
                "complete": 1,
                "unlock_key": "fractureray|0|101"
            }, {
                "complete": 1,
                "unlock_key": "kanagawa|1|0"
            }, {
                "complete": 1,
                "unlock_key": "darakunosono|2|0"
            }, {
                "complete": 1,
                "unlock_key": "freefall|1|0"
            }, {
                "complete": 1,
                "unlock_key": "nirvluce|2|0"
            }, {
                "complete": 1,
                "unlock_key": "cyanine|2|0"
            }, {
                "complete": 1,
                "unlock_key": "heavensdoor|2|0"
            }, {
                "complete": 1,
                "unlock_key": "genesis|2|0"
            }, {
                "complete": 1,
                "unlock_key": "pragmatism|1|0"
            }, {
                "complete": 1,
                "unlock_key": "nhelv|2|0"
            }, {
                "complete": 1,
                "unlock_key": "halcyon|2|0"
            }, {
                "complete": 1,
                "unlock_key": "blrink|1|0"
            }, {
                "complete": 1,
                "unlock_key": "fractureray|2|101"
            }, {
                "complete": 1,
                "unlock_key": "lethaeus|2|0"
            }, {
                "complete": 1,
                "unlock_key": "sheriruth|1|0"
            }, {
                "complete": 1,
                "unlock_key": "babaroque|2|0"
            }, {
                "complete": 1,
                "unlock_key": "tiferet|2|0"
            }, {
                "complete": 1,
                "unlock_key": "grimheart|2|0"
            }, {
                "complete": 1,
                "unlock_key": "cyaegha|1|0"
            }, {
                "complete": 1,
                "unlock_key": "aiueoon|2|0"
            }, {
                "complete": 1,
                "unlock_key": "gloryroad|1|0"
            }, {
                "complete": 1,
                "unlock_key": "anokumene|1|0"
            }, {
                "complete": 1,
                "unlock_key": "grievouslady|0|101"
            }, {
                "complete": 1,
                "unlock_key": "dreaminattraction|1|0"
            }]
        }, "clearedsongs": {
            "": song_1
        },
        "clearlamps": {
            "": song_2
        },
        "scores": {
            "": song_3
        },
        "version": {
            "val": 1
        }
    }
