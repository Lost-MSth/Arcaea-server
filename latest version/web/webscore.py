import time

from core.score import Potential


def get_user_score(c, user_id, limit=-1, offset=0):
    # 返回用户的所有歌曲数据，带排名，返回字典列表
    if limit >= 0:
        c.execute('''select * from best_score where user_id =:a order by rating DESC limit :b offset :c''',
                  {'a': user_id, 'b': limit, 'c': offset})
    else:
        c.execute(
            '''select * from best_score where user_id =:a order by rating DESC''', {'a': user_id})
    x = c.fetchall()
    r = []
    if x:
        rank = 0
        for i in x:
            rank += 1
            r.append({
                "song_id": i[1],
                "difficulty": i[2],
                "score": i[3],
                "shiny_perfect_count": i[4],
                "perfect_count": i[5],
                "near_count": i[6],
                "miss_count": i[7],
                "health": i[8],
                "modifier": i[9],
                "time_played": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(i[10])),
                "best_clear_type": i[11],
                "clear_type": i[12],
                "rating": i[13],
                "rank": rank
            })

    return r


def get_user(c, user_id):
    # 得到user表部分用户信息，返回字典
    c.execute('''select * from user where user_id = :a''', {'a': user_id})
    x = c.fetchone()
    r = None
    if x:
        join_date = None
        time_played = None
        if x[3]:
            join_date = time.strftime('%Y-%m-%d %H:%M:%S',
                                      time.localtime(int(x[3])//1000))
        if x[20]:
            time_played = time.strftime('%Y-%m-%d %H:%M:%S',
                                        time.localtime(int(x[20])//1000))
        if x[2] == '':
            ban_flag = True
        else:
            ban_flag = False

        r = {'name': x[1],
             'user_id': user_id,
             'join_date': join_date,
             'user_code': x[4],
             'rating_ptt': x[5],
             'song_id': x[11],
             'difficulty': x[12],
             'score': x[13],
             'shiny_perfect_count': x[14],
             'perfect_count': x[15],
             'near_count': x[16],
             'miss_count': x[17],
             'time_played': time_played,
             'clear_type': x[21],
             'rating': x[22],
             'ticket': x[26],
             'ban_flag': ban_flag
             }

    return r
