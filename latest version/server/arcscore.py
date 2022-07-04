from core.sql import Connect
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


def get_score(c, user_id, song_id, difficulty):
    # 根据user_id、song_id、难度得到该曲目最好成绩，返回字典
    c.execute('''select * from best_score where user_id = :a and song_id = :b and difficulty = :c''',
              {'a': user_id, 'b': song_id, 'c': difficulty})
    x = c.fetchone()
    if x is not None:
        c.execute('''select name, character_id, is_skill_sealed, is_char_uncapped, is_char_uncapped_override, favorite_character from user where user_id = :a''', {
                  'a': user_id})
        y = c.fetchone()
        if y is not None:
            character = y[1]
            is_char_uncapped = int2b(y[3])
            if y[5] != -1:
                character = y[5]
                if not Config.CHARACTER_FULL_UNLOCK:
                    c.execute('''select is_uncapped, is_uncapped_override from user_char where user_id=:a and character_id=:b''', {
                        'a': user_id, 'b': character})
                else:
                    c.execute('''select is_uncapped, is_uncapped_override from user_char_full where user_id=:a and character_id=:b''', {
                        'a': user_id, 'b': character})
                z = c.fetchone()
                if z:
                    if z[1] == 0:
                        is_char_uncapped = int2b(z[0])
                    else:
                        is_char_uncapped = False
            else:
                if y[4] == 1:
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


def calculate_rating(defnum, score):
    # 计算rating
    if score >= 10000000:
        ptt = defnum + 2
    elif score < 9800000:
        ptt = defnum + (score-9500000) / 300000
        if ptt < 0 and defnum != -10:
            ptt = 0
    else:
        ptt = defnum + 1 + (score-9800000) / 200000

    return ptt


def refresh_all_score_rating():
    # 刷新所有best成绩的rating
    error = 'Unknown error.'

    with Connect('') as c:
        c.execute(
            '''select song_id, rating_pst, rating_prs, rating_ftr, rating_byn from chart''')
        x = c.fetchall()

    if x:
        song_list = [i[0] for i in x]
        with Connect() as c:
            c.execute('''update best_score set rating=0 where song_id not in ({0})'''.format(
                ','.join(['?']*len(song_list))), tuple(song_list))
            for i in x:
                for j in range(0, 4):
                    defnum = -10  # 没在库里的全部当做定数-10
                    if i is not None:
                        defnum = float(i[j+1]) / 10
                        if defnum <= 0:
                            defnum = -10  # 缺少难度的当做定数-10

                    c.execute('''select user_id, score from best_score where song_id=:a and difficulty=:b''', {
                              'a': i[0], 'b': j})
                    y = c.fetchall()
                    if y:
                        for k in y:
                            ptt = calculate_rating(defnum, k[1])
                            if ptt < 0:
                                ptt = 0

                            c.execute('''update best_score set rating=:a where user_id=:b and song_id=:c and difficulty=:d''', {
                                      'a': ptt, 'b': k[0], 'c': i[0], 'd': j})
            error = None

    else:
        error = 'No song data.'

    return error
