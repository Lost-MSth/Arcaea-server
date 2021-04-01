from server.sql import Connect
import server.arcworld
import server.arcpurchase
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


def get_user_character(c, user_id):
    # 得到用户拥有的角色列表，返回列表
    c.execute('''select * from user_char where user_id = :user_id''',
              {'user_id': user_id})
    x = c.fetchall()
    if x != []:
        s = []
        for i in x:
            char_name = ''
            c.execute(
                '''select name from character where character_id = :x''', {'x': i[1]})
            y = c.fetchone()
            if y is not None:
                char_name = y[0]
            char = {
                "is_uncapped_override": int2b(i[14]),
                "is_uncapped": int2b(i[13]),
                "uncap_cores": [],
                "char_type": i[12],
                "skill_id_uncap": i[11],
                "skill_requires_uncap": int2b(i[10]),
                "skill_unlock_level": i[9],
                "skill_id": i[8],
                "overdrive": i[7],
                "prog": i[6],
                "frag": i[5],
                "level_exp": i[4],
                "exp": i[3],
                "level": i[2],
                "name": char_name,
                "character_id": i[1]
            }
            if i[1] == 21:
                char["voice"] = [0, 1, 2, 3, 100, 1000, 1001]
            s.append(char)

        return s
    else:
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
                    c.execute('''select is_uncapped, is_uncapped_override from user_char where user_id=:a and character_id=:b''', {
                              'a': i[0], 'b': character})
                    z = c.fetchone()
                    if z:
                        is_char_uncapped = int2b(z[0])
                        is_char_uncapped_override = int2b(z[1])

                s.append({
                    "is_mutual": is_mutual,
                    "is_char_uncapped_override": is_char_uncapped_override,
                    "is_char_uncapped": is_char_uncapped,
                    "is_skill_sealed": int2b(y[7]),
                    "rating": y[5],
                    "join_date": int(y[3]),
                    "character": character,
                    "recent_score": get_recent_score(c, i[0]),
                    "name": y[1],
                    "user_id": i[0]
                })

    return s


def get_user_singles(c, user_id):
    # 得到用户的单曲，返回列表
    c.execute('''select * from user_item where user_id = :user_id and type = "single"''',
              {'user_id': user_id})
    x = c.fetchall()
    if not x:
        return []

    re = []
    for i in x:
        re.append(i[1])
    return re


def get_user_packs(c, user_id):
    # 得到用户的曲包，返回列表
    c.execute('''select * from user_item where user_id = :user_id and type = "pack"''',
              {'user_id': user_id})
    x = c.fetchall()
    if not x:
        return []

    re = []
    for i in x:
        re.append(i[1])
    return re


def get_value_0(c, user_id):
    # 构造value id=0的数据，返回字典
    c.execute('''select * from user where user_id = :x''', {'x': user_id})
    x = c.fetchone()
    r = {}
    if x is not None:
        user_character = get_user_character(c, user_id)
        characters = []
        for i in user_character:
            characters.append(i['character_id'])
        prog_boost = 0
        if x[27] and x[27] != 0:
            prog_boost = 300

        r = {"is_aprilfools": Config.IS_APRILFOOLS,
             "curr_available_maps": [],
             "character_stats": user_character,
             "friends": get_user_friend(c, user_id),
             "settings": {
                 "favorite_character": x[23],
                 "is_hide_rating": int2b(x[10]),
                 "max_stamina_notification_enabled": int2b(x[24])
             },
             "user_id": user_id,
             "name": x[1],
             "user_code": x[4],
             "display_name": x[1],
             "ticket": x[26],
             "character": x[6],
             "is_locked_name_duplicate": False,
             "is_skill_sealed": int2b(x[7]),
             "current_map": x[25],
             "prog_boost": prog_boost,
             "next_fragstam_ts": -1,
             "max_stamina_ts": 1586274871917,
             "stamina": 12,
             "world_unlocks": ["scenery_chap1", "scenery_chap2", "scenery_chap3", "scenery_chap4", "scenery_chap5"],
             "world_songs": ["babaroque", "shadesoflight", "kanagawa", "lucifer", "anokumene", "ignotus", "rabbitintheblackroom", "qualia", "redandblue", "bookmaker", "darakunosono", "espebranch", "blacklotus", "givemeanightmare", "vividtheory", "onefr", "gekka", "vexaria3", "infinityheaven3", "fairytale3", "goodtek3", "suomi", "rugie", "faintlight", "harutopia", "goodtek", "dreaminattraction", "syro", "diode", "freefall", "grimheart", "blaster", "cyberneciacatharsis", "monochromeprincess", "revixy", "vector", "supernova", "nhelv", "purgatorium3", "dement3", "crossover", "guardina", "axiumcrisis", "worldvanquisher", "sheriruth", "pragmatism", "gloryroad", "etherstrike", "corpssansorganes", "lostdesire", "blrink", "essenceoftwilight", "lapis", "solitarydream", "lumia3", "purpleverse", "moonheart3", "glow", "enchantedlove", "take"],
             "singles": get_user_singles(c, user_id),
             "packs": get_user_packs(c, user_id),
             "characters": characters,
             "cores": [],
             "recent_score": get_recent_score(c, user_id),
             "max_friend": 50,
             "rating": x[5],
             "join_date": int(x[3])
             }

    return r


def arc_aggregate_small(user_id):
    # 返回用户数据
    r = {"success": False}
    with Connect() as c:
        r = {"success": True,
             "value": [{
                 "id": 0,
                 "value": get_value_0(c, user_id)
             }]}

    return r


def arc_aggregate_big(user_id):
    # 返回用户数据和地图歌曲信息
    r = {"success": False}
    with Connect() as c:
        r = {"success": True,
             "value": [{
                 "id": 0,
                 "value": get_value_0(c, user_id)
             }, {
                 "id": 1,
                 "value": server.arcpurchase.get_item(c, 'pack')
             }, {
                 "id": 2,
                 "value": {}
             }, {
                 "id": 3,
                 "value": {
                     "max_stamina": 12,
                     "stamina_recover_tick": 1800000,
                     "core_exp": 250,
                     "curr_ts": int(time.time())*1000,
                     "level_steps": [{
                         "level": 1,
                         "level_exp": 0
                     }, {
                         "level": 2,
                         "level_exp": 50
                     }, {
                         "level": 3,
                         "level_exp": 100
                     }, {
                         "level": 4,
                         "level_exp": 150
                     }, {
                         "level": 5,
                         "level_exp": 200
                     }, {
                         "level": 6,
                         "level_exp": 300
                     }, {
                         "level": 7,
                         "level_exp": 450
                     }, {
                         "level": 8,
                         "level_exp": 650
                     }, {
                         "level": 9,
                         "level_exp": 900
                     }, {
                         "level": 10,
                         "level_exp": 1200
                     }, {
                         "level": 11,
                         "level_exp": 1600
                     }, {
                         "level": 12,
                         "level_exp": 2100
                     }, {
                         "level": 13,
                         "level_exp": 2700
                     }, {
                         "level": 14,
                         "level_exp": 3400
                     }, {
                         "level": 15,
                         "level_exp": 4200
                     }, {
                         "level": 16,
                         "level_exp": 5100
                     }, {
                         "level": 17,
                         "level_exp": 6100
                     }, {
                         "level": 18,
                         "level_exp": 7200
                     }, {
                         "level": 19,
                         "level_exp": 8500
                     }, {
                         "level": 20,
                         "level_exp": 10000
                     }, {
                         "level": 21,
                         "level_exp": 11500
                     }, {
                         "level": 22,
                         "level_exp": 13000
                     }, {
                         "level": 23,
                         "level_exp": 14500
                     }, {
                         "level": 24,
                         "level_exp": 16000
                     }, {
                         "level": 25,
                         "level_exp": 17500
                     }, {
                         "level": 26,
                         "level_exp": 19000
                     }, {
                         "level": 27,
                         "level_exp": 20500
                     }, {
                         "level": 28,
                         "level_exp": 22000
                     }, {
                         "level": 29,
                         "level_exp": 23500
                     }, {
                         "level": 30,
                         "level_exp": 25000
                     }],
                     "world_ranking_enabled": False,
                     "is_byd_chapter_unlocked": True
                 }
             }, {
                 "id": 4,
                 "value": server.arcpurchase.get_user_present(c, user_id)
             }, {
                 "id": 5,
                 "value": {
                     "current_map": server.arcworld.get_current_map(user_id),
                     "user_id": user_id,
                     "maps": server.arcworld.get_world_all(user_id)
                 }
             }
             ]}

    return r
