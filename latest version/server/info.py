from server.sql import Connect
import server.arcworld
import server.arcpurchase
import server.arcdownload
import server.character
import server.item
import time
from setting import Config


def int2b(x):
    # int与布尔值转换
    if x is None or x == 0:
        return False
    else:
        return True


def get_recent_score(c, user_id):
    # 得到用户最近一次的成绩，返回列表
    c.execute('''select * from user where user_id = :x''', {'x': user_id})
    x = c.fetchone()
    if x is not None:
        if x[11] is not None:
            c.execute('''select best_clear_type from best_score where user_id=:u and song_id=:s and difficulty=:d''', {
                'u': user_id, 's': x[11], 'd': x[12]})
            y = c.fetchone()
            if y is not None:
                best_clear_type = y[0]
            else:
                best_clear_type = x[21]

            return [{
                "rating": x[22],
                "modifier": x[19],
                "time_played": x[20],
                "health": x[18],
                "best_clear_type": best_clear_type,
                "clear_type": x[21],
                "miss_count": x[17],
                "near_count": x[16],
                "perfect_count": x[15],
                "shiny_perfect_count": x[14],
                "score": x[13],
                "difficulty": x[12],
                "song_id": x[11]
            }]
    return []


def get_user_friend(c, user_id):
    # 得到用户的朋友列表，返回列表
    c.execute('''select user_id_other from friend where user_id_me = :user_id''', {
              'user_id': user_id})
    x = c.fetchall()
    s = []
    if x != [] and x[0][0] is not None:

        for i in x:
            c.execute('''select exists(select * from friend where user_id_me = :x and user_id_other = :y)''',
                      {'x': i[0], 'y': user_id})
            if c.fetchone() == (1,):
                is_mutual = True
            else:
                is_mutual = False

            c.execute('''select * from user where user_id = :x''', {'x': i[0]})
            y = c.fetchone()
            if y is not None:
                character = y[6]
                is_char_uncapped = int2b(y[8])
                is_char_uncapped_override = int2b(y[9])
                if y[23] != -1:
                    character = y[23]
                    if not Config.CHARACTER_FULL_UNLOCK:
                        c.execute('''select is_uncapped, is_uncapped_override from user_char where user_id=:a and character_id=:b''', {
                            'a': i[0], 'b': character})
                    else:
                        c.execute('''select is_uncapped, is_uncapped_override from user_char_full where user_id=:a and character_id=:b''', {
                            'a': i[0], 'b': character})
                    z = c.fetchone()
                    if z:
                        is_char_uncapped = int2b(z[0])
                        is_char_uncapped_override = int2b(z[1])

                rating = y[5]
                if int2b(y[10]):
                    rating = -1

                s.append({
                    "is_mutual": is_mutual,
                    "is_char_uncapped_override": is_char_uncapped_override,
                    "is_char_uncapped": is_char_uncapped,
                    "is_skill_sealed": int2b(y[7]),
                    "rating": rating,
                    "join_date": int(y[3]),
                    "character": character,
                    "recent_score": get_recent_score(c, i[0]),
                    "name": y[1],
                    "user_id": i[0]
                })

    return s


def get_user_me(c, user_id):
    # 构造user/me的数据，返回字典
    c.execute('''select * from user where user_id = :x''', {'x': user_id})
    x = c.fetchone()
    r = {}
    if x is not None:
        user_character = server.character.get_user_character(c, user_id)
        # 下面没有使用get_user_characters函数是为了节省一次查询
        characters = []
        for i in user_character:
            characters.append(i['character_id'])

        character_id = x[6]
        if character_id not in characters:
            character_id = 0
            c.execute(
                '''update user set character_id=0 where user_id=?''', (user_id,))

        favorite_character_id = x[23]
        if favorite_character_id not in characters:
            favorite_character_id = -1
            c.execute(
                '''update user set favorite_character=-1 where user_id=?''', (user_id,))

        c.execute(
            '''select world_rank_score from user where user_id=?''', (user_id,))
        y = c.fetchone()
        if y and y[0]:
            c.execute(
                '''select count(*) from user where world_rank_score > ?''', (y[0],))
            y = c.fetchone()
            if y and y[0] + 1 <= Config.WORLD_RANK_MAX:
                world_rank = y[0] + 1
            else:
                world_rank = 0
        else:
            world_rank = 0

        prog_boost = 0
        if x[27] and x[27] != 0:
            prog_boost = 300

        r = {"is_aprilfools": Config.IS_APRILFOOLS,
             "curr_available_maps": [],
             "character_stats": user_character,
             "friends": get_user_friend(c, user_id),
             "settings": {
                 "favorite_character": favorite_character_id,
                 "is_hide_rating": int2b(x[10]),
                 "max_stamina_notification_enabled": int2b(x[24])
             },
             "user_id": user_id,
             "name": x[1],
             "user_code": x[4],
             "display_name": x[1],
             "ticket": x[26],
             "character": character_id,
             "is_locked_name_duplicate": False,
             "is_skill_sealed": int2b(x[7]),
             "current_map": x[25],
             "prog_boost": prog_boost,
             "next_fragstam_ts": -1,
             "max_stamina_ts": 1586274871917,
             "stamina": 12,
             "world_unlocks": server.item.get_user_items(c, user_id, 'world_unlock'),
             "world_songs": server.item.get_user_items(c, user_id, 'world_song'),
             "singles": server.item.get_user_items(c, user_id, 'single'),
             "packs": server.item.get_user_items(c, user_id, 'pack'),
             "characters": characters,
             "cores": server.item.get_user_cores(c, user_id),
             "recent_score": get_recent_score(c, user_id),
             "max_friend": 50,
             "rating": x[5],
             "join_date": int(x[3]),
             "global_rank": world_rank
             }

    return r


def arc_aggregate_small(user_id):
    # 返回用户数据
    r = {"success": False}
    with Connect() as c:
        r = {"success": True,
             "value": [{
                 "id": 0,
                 "value": get_user_me(c, user_id)
             }]}

    return r


def arc_aggregate_big(user_id):
    # 返回比较全的用户数据
    r = {"success": False}
    with Connect() as c:
        # 防止数据库锁
        id_2 = server.arcdownload.get_all_songs(user_id, url_flag=False)
        id_5 = {
            "current_map": server.arcworld.get_current_map(user_id),
            "user_id": user_id,
            "maps": server.arcworld.get_world_all(user_id)
        }
        r = {"success": True,
             "value": [{
                 "id": 0,
                 "value": get_user_me(c, user_id)
             }, {
                 "id": 1,
                 "value": server.arcpurchase.get_purchase(c, 'pack')
             }, {
                 "id": 2,
                 "value": id_2
             }, {
                 "id": 3,
                 "value": {
                     "max_stamina": 12,
                     "stamina_recover_tick": 1800000,
                     "core_exp": 250,
                     "curr_ts": int(time.time())*1000,
                     "level_steps": server.character.get_level_steps(),
                     "world_ranking_enabled": False,
                     "is_byd_chapter_unlocked": True
                 }
             }, {
                 "id": 4,
                 "value": server.arcpurchase.get_user_present(c, user_id)
             }, {
                 "id": 5,
                 "value": id_5
             }
             ]}

    return r
