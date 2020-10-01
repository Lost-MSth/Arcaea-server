import sqlite3


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
            s.append({
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
            })

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
            y=c.fetchone()
            if y is not None:
                s.append({
                "is_mutual": is_mutual,
                "is_char_uncapped_override": int2b(y[9]),
                "is_char_uncapped": int2b(y[8]),
                "is_skill_sealed": int2b(y[7]),
                "rating": y[5],
                "join_date": int(y[3]),
                "character": y[6],
                "recent_score": get_recent_score(c, i[0]),
                "name": y[1],
                "user_id": i[0]
                })

    return s


def get_value_0(c, user_id):
    # 构造value id=0的数据，返回字典
    c.execute('''select * from user where user_id = :x''', {'x': user_id})
    x = c.fetchone()
    r = {}
    if x is not None:
        r = {"is_aprilfools": False,
                "curr_available_maps": [],
                "character_stats": get_user_character(c, user_id),
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
                "ticket": 114514,
                "character": x[6],
                "is_locked_name_duplicate": False,
                "is_skill_sealed": int2b(x[7]),
                "current_map": "",
                "prog_boost": 0,
                "next_fragstam_ts": -1,
                "max_stamina_ts": 1586274871917,
                "stamina": 0,
                "world_unlocks": [],
                "world_songs": ["babaroque", "shadesoflight", "kanagawa", "lucifer", "anokumene", "ignotus", "rabbitintheblackroom", "qualia", "redandblue", "bookmaker", "darakunosono", "espebranch", "blacklotus", "givemeanightmare", "vividtheory", "onefr", "gekka", "vexaria3", "infinityheaven3", "fairytale3", "goodtek3", "suomi", "rugie", "faintlight", "harutopia", "goodtek", "dreaminattraction", "syro"],
                "singles": [],
                "packs": [],
                "characters":[0,1,2,3,4]+[x for x in range(6, 38)],
                "cores": [],
                "recent_score": get_recent_score(c, user_id),
                "max_friend": 50,
                "rating": x[5],
                "join_date": int(x[3])
            }

    return r


def arc_aggregate_small(user_id):
    # 返回用户数据
    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    r = {"success": True,
	    "value": [{
		"id": 0,
		"value": get_value_0(c, user_id)
	    }]}

    conn.commit()
    conn.close()
    return r


def arc_aggregate_big(user_id):
    # 返回用户数据和地图歌曲信息
    # 因为没有整理地图和曲包数据（不需要世界模式），所以直接复制了

    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    r = {"success": True,
	    "value": [{
		"id": 0,
		"value": get_value_0(c, user_id)
	    }, {
		"id": 1,
		"value": [{
			"name": "core",
			"items": [{
				"id": "core",
				"type": "pack",
				"is_available": True
			}],
			"price": 500,
			"orig_price": 500,
			"discount_from": 1583712000000,
			"discount_to": 1584316799000
		}, {
			"name": "shiawase",
			"items": [{
				"id": "shiawase",
				"type": "pack",
				"is_available": True
			}, {
				"id": "kou",
				"type": "character",
				"is_available": True
			}],
			"price": 500,
			"orig_price": 500,
			"discount_from": 1552089600000,
			"discount_to": 1552694399000
		}, {
			"name": "dynamix",
			"items": [{
				"id": "dynamix",
				"type": "pack",
				"is_available": True
			}, {
				"id": "sapphire",
				"type": "character",
				"is_available": True
			}],
			"price": 500,
			"orig_price": 500,
			"discount_from": 1583712000000,
			"discount_to": 1584316799000
		}, {
			"name": "mirai",
			"items": [{
				"id": "mirai",
				"type": "pack",
				"is_available": True
			}, {
				"id": "lethe",
				"type": "character",
				"is_available": True
			}],
			"price": 500,
			"orig_price": 500,
			"discount_from": 1552089600000,
			"discount_to": 1552694399000
		}, {
			"name": "yugamu",
			"items": [{
				"id": "yugamu",
				"type": "pack",
				"is_available": True
			}],
			"price": 500,
			"orig_price": 500,
			"discount_from": 1583712000000,
			"discount_to": 1584316799000
		}, {
			"name": "lanota",
			"items": [{
				"id": "lanota",
				"type": "pack",
				"is_available": True
			}],
			"price": 500,
			"orig_price": 500,
			"discount_from": 1583712000000,
			"discount_to": 1584316799000
		}, {
			"name": "nijuusei",
			"items": [{
				"id": "nijuusei",
				"type": "pack",
				"is_available": True
			}],
			"price": 500,
			"orig_price": 500,
			"discount_from": 1583712000000,
			"discount_to": 1584316799000
		}, {
			"name": "rei",
			"items": [{
				"id": "rei",
				"type": "pack",
				"is_available": True
			}],
			"price": 500,
			"orig_price": 500,
			"discount_from": 1583712000000,
			"discount_to": 1584316799000
		}, {
			"name": "tonesphere",
			"items": [{
				"id": "tonesphere",
				"type": "pack",
				"is_available": True
			}],
			"price": 500,
			"orig_price": 500,
			"discount_from": 1583712000000,
			"discount_to": 1584316799000
		}, {
			"name": "groovecoaster",
			"items": [{
				"id": "groovecoaster",
				"type": "pack",
				"is_available": True
			}],
			"price": 500,
			"orig_price": 500,
			"discount_from": 1583712000000,
			"discount_to": 1584316799000
		}, {
			"name": "zettai",
			"items": [{
				"id": "zettai",
				"type": "pack",
				"is_available": True
			}],
			"price": 500,
			"orig_price": 500,
			"discount_from": 1583712000000,
			"discount_to": 1584316799000
		}, {
			"name": "chunithm",
			"items": [{
				"id": "chunithm",
				"type": "pack",
				"is_available": True
			}],
			"price": 300,
			"orig_price": 300
		}, {
			"name": "prelude",
			"items": [{
				"id": "prelude",
				"type": "pack",
				"is_available": True
			}],
			"price": 400,
			"orig_price": 400
		}, {
			"name": "omatsuri",
			"items": [{
				"id": "omatsuri",
				"type": "pack",
				"is_available": True
			}],
			"price": 500,
			"orig_price": 500
		}, {
			"name": "vs",
			"items": [{
				"id": "vs",
				"type": "pack",
				"is_available": True
			}],
			"price": 500,
			"orig_price": 500
		}, {
			"name": "extend",
			"items": [{
				"id": "extend",
				"type": "pack",
				"is_available": True
			}],
			"price": 700,
			"orig_price": 700
		}]
	}, {
		"id": 2,
		"value": {}
	}, {
		"id": 3,
		"value": {
			"max_stamina": 12,
			"stamina_recover_tick": 1800000,
			"core_exp": 250,
			"curr_ts": 1599547606825,
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
		"value": []
	}, {
		"id": 5,
		"value": {
			"user_id": user_id,
			"current_map": "",
			"maps": [{
				"map_id": "hikari_art",
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 1,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "",
				"require_type": "",
				"require_value": 1,
				"is_legacy": True,
				"stamina_cost": 1,
				"coordinate": "-270,150",
				"step_count": 91,
				"custom_bg": "",
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"id": "babaroque",
						"type": "world_song"
					}],
					"position": 5
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 10
				}, {
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 15
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 20
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 25
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 27
				}, {
					"items": [{
						"id": "shadesoflight",
						"type": "world_song"
					}],
					"position": 30
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 35
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 40
				}, {
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 45
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 50
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 55
				}, {
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 60
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 65
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 70
				}, {
					"items": [{
						"id": "kanagawa",
						"type": "world_song"
					}],
					"position": 75
				}, {
					"items": [{
						"type": "core",
						"id": "core_hollow",
						"amount": 5
					}],
					"position": 80
				}, {
					"items": [{
						"type": "core",
						"id": "core_hollow",
						"amount": 5
					}],
					"position": 85
				}, {
					"items": [{
						"type": "core",
						"id": "core_hollow",
						"amount": 5
					}],
					"position": 90
				}]
			}, {
				"map_id": "hikari_happy",
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 1,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "",
				"require_type": "fragment",
				"require_value": 200,
				"is_legacy": True,
				"stamina_cost": 1,
				"coordinate": "270,150",
				"step_count": 136,
				"custom_bg": "",
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 5
				}, {
					"items": [{
						"id": "harutopia",
						"type": "world_song"
					}],
					"position": 10
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 15
				}, {
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 20
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 25
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 30
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 32
				}, {
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 35
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 40
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 45
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 50
				}, {
					"items": [{
						"id": "goodtek",
						"type": "world_song"
					}],
					"position": 55
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 60
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 65
				}, {
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 70
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 75
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 80
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 82
				}, {
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 85
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 90
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 95
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 97
				}, {
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 100
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 105
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 110
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 115
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 120
				}, {
					"items": [{
						"id": "dreaminattraction",
						"type": "world_song"
					}],
					"position": 125
				}, {
					"items": [{
						"type": "core",
						"id": "core_hollow",
						"amount": 5
					}],
					"position": 135
				}]
			}, {
				"map_id": "tairitsu_arcs",
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 1,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "",
				"require_type": "fragment",
				"require_value": 200,
				"is_legacy": True,
				"stamina_cost": 1,
				"coordinate": "-270,-150",
				"step_count": 136,
				"custom_bg": "",
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 5
				}, {
					"items": [{
						"id": "rabbitintheblackroom",
						"type": "world_song"
					}],
					"position": 10
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 15
				}, {
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 20
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 25
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 30
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 32
				}, {
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 35
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 40
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 45
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 50
				}, {
					"items": [{
						"id": "qualia",
						"type": "world_song"
					}],
					"position": 55
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 60
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 65
				}, {
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 70
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 75
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 80
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 82
				}, {
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 85
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 90
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 95
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 97
				}, {
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 100
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 105
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 110
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 115
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 120
				}, {
					"items": [{
						"id": "redandblue",
						"type": "world_song"
					}],
					"position": 125
				}, {
					"items": [{
						"type": "core",
						"id": "core_desolate",
						"amount": 5
					}],
					"position": 135
				}]
			}, {
				"map_id": "tairitsu_tech",
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 1,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "",
				"require_type": "",
				"require_value": 1,
				"is_legacy": True,
				"stamina_cost": 1,
				"coordinate": "270,-150",
				"step_count": 91,
				"custom_bg": "",
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"id": "lucifer",
						"type": "world_song"
					}],
					"position": 5
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 10
				}, {
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 15
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 20
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 25
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 27
				}, {
					"items": [{
						"id": "anokumene",
						"type": "world_song"
					}],
					"position": 30
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 35
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 40
				}, {
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 45
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 50
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 55
				}, {
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 60
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 65
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 70
				}, {
					"items": [{
						"id": "ignotus",
						"type": "world_song"
					}],
					"position": 75
				}, {
					"items": [{
						"type": "core",
						"id": "core_desolate",
						"amount": 5
					}],
					"position": 80
				}, {
					"items": [{
						"type": "core",
						"id": "core_desolate",
						"amount": 5
					}],
					"position": 85
				}, {
					"items": [{
						"type": "core",
						"id": "core_desolate",
						"amount": 5
					}],
					"position": 90
				}]
			}, {
				"map_id": "eternal",
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 1,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "core",
				"require_type": "pack",
				"require_value": 1,
				"is_legacy": True,
				"stamina_cost": 1,
				"coordinate": "-500,0",
				"step_count": 66,
				"custom_bg": "",
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 5
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 10
				}, {
					"items": [{
						"id": "essenceoftwilight",
						"type": "world_song"
					}],
					"position": 15
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 2
					}],
					"position": 20
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 28
				}, {
					"items": [{
						"type": "fragment",
						"amount": 200
					}],
					"position": 35
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 2
					}],
					"position": 40
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 42
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 44
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 46
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 48
				}, {
					"items": [{
						"id": "pragmatism",
						"type": "world_song"
					}],
					"position": 50
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 52
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 54
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 56
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 58
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 60
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 62
				}, {
					"items": [{
						"id": "sheriruth",
						"type": "world_song"
					}],
					"position": 65
				}]
			}, {
				"map_id": "axiumcrisis",
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 1,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "yugamu",
				"require_type": "pack",
				"is_legacy": True,
				"stamina_cost": 1,
				"coordinate": "500,0",
				"step_count": 61,
				"custom_bg": "",
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 5
				}, {
					"items": [{
						"id": "axiumcrisis",
						"type": "world_song"
					}],
					"position": 10
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 2
					}],
					"position": 15
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 24
				}, {
					"items": [{
						"type": "fragment",
						"amount": 200
					}],
					"position": 30
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 2
					}],
					"position": 35
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 37
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 39
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 41
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 43
				}, {
					"items": [{
						"type": "fragment",
						"amount": 150
					}],
					"position": 45
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 51
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 53
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 55
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 57
				}, {
					"items": [{
						"id": "6",
						"type": "character"
					}],
					"position": 60
				}]
			}, {
				"map_id": "grievouslady",
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 1,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "yugamu",
				"require_type": "pack",
				"require_localunlock_songid": "grievouslady",
				"is_legacy": True,
				"stamina_cost": 1,
				"coordinate": "0,-150",
				"step_count": 21,
				"custom_bg": "",
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 300
					}],
					"position": 18
				}, {
					"items": [{
						"id": "7",
						"type": "character"
					}],
					"position": 20
				}]
			}, {
				"map_id": "lanota",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 2,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "lanota",
				"require_type": "pack",
				"coordinate": "460,-160",
				"step_count": 35,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 40
					}],
					"position": 5
				}, {
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 10
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 12
				}, {
					"items": [{
						"type": "fragment",
						"amount": 60
					}],
					"position": 15
				}, {
					"items": [{
						"type": "fragment",
						"amount": 70
					}],
					"position": 20
				}, {
					"items": [{
						"type": "fragment",
						"amount": 80
					}],
					"position": 25
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 27
				}, {
					"items": [{
						"type": "fragment",
						"amount": 90
					}],
					"position": 33
				}, {
					"items": [{
						"id": "9",
						"type": "character"
					}],
					"position": 34
				}]
			}, {
				"map_id": "nijuusei_light",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 2,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "nijuusei",
				"require_type": "pack",
				"coordinate": "-260,160",
				"step_count": 22,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 4
				}, {
					"items": [{
						"type": "fragment",
						"amount": 175
					}],
					"position": 10
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 14
				}, {
					"items": [{
						"type": "fragment",
						"amount": 178
					}],
					"position": 20
				}, {
					"items": [{
						"id": "11",
						"type": "character"
					}],
					"position": 21
				}]
			}, {
				"map_id": "nijuusei_conflict",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 2,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "nijuusei",
				"require_type": "pack",
				"require_localunlock_challengeid": "singularity",
				"coordinate": "260,160",
				"step_count": 36,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 175
					}],
					"position": 2
				}, {
					"items": [{
						"type": "fragment",
						"amount": 175
					}],
					"position": 3
				}, {
					"items": [{
						"type": "fragment",
						"amount": 175
					}],
					"position": 4
				}, {
					"items": [{
						"type": "fragment",
						"amount": 178
					}],
					"position": 5
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 6
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 7
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 8
				}, {
					"items": [{
						"id": "12",
						"type": "character"
					}],
					"position": 35
				}]
			}, {
				"map_id": "extra_originals",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 2,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "",
				"require_type": "",
				"require_value": 1,
				"coordinate": "0,-200",
				"step_count": 101,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 5
				}, {
					"items": [{
						"type": "fragment",
						"amount": 60
					}],
					"position": 10
				}, {
					"items": [{
						"type": "fragment",
						"amount": 70
					}],
					"position": 15
				}, {
					"items": [{
						"type": "fragment",
						"amount": 60
					}],
					"position": 20
				}, {
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 25
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 29
				}, {
					"items": [{
						"id": "syro",
						"type": "world_song"
					}],
					"position": 30
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 31
				}, {
					"items": [{
						"type": "fragment",
						"amount": 60
					}],
					"position": 35
				}, {
					"items": [{
						"type": "fragment",
						"amount": 70
					}],
					"position": 40
				}, {
					"items": [{
						"type": "fragment",
						"amount": 80
					}],
					"position": 45
				}, {
					"items": [{
						"type": "fragment",
						"amount": 70
					}],
					"position": 50
				}, {
					"items": [{
						"type": "fragment",
						"amount": 60
					}],
					"position": 55
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 59
				}, {
					"items": [{
						"id": "blaster",
						"type": "world_song"
					}],
					"position": 60
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 61
				}, {
					"items": [{
						"type": "fragment",
						"amount": 70
					}],
					"position": 65
				}, {
					"items": [{
						"type": "fragment",
						"amount": 80
					}],
					"position": 70
				}, {
					"items": [{
						"type": "fragment",
						"amount": 90
					}],
					"position": 75
				}, {
					"items": [{
						"type": "fragment",
						"amount": 90
					}],
					"position": 80
				}, {
					"items": [{
						"type": "fragment",
						"amount": 80
					}],
					"position": 85
				}, {
					"items": [{
						"type": "fragment",
						"amount": 70
					}],
					"position": 90
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 94
				}, {
					"items": [{
						"id": "cyberneciacatharsis",
						"type": "world_song"
					}],
					"position": 95
				}, {
					"items": [{
						"type": "core",
						"id": "core_crimson",
						"amount": 5
					}],
					"position": 98
				}, {
					"items": [{
						"type": "core",
						"id": "core_crimson",
						"amount": 5
					}],
					"position": 100
				}]
			}, {
				"map_id": "guardina",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 2,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "dynamix",
				"require_type": "pack",
				"coordinate": "-460,-160",
				"step_count": 35,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 60
					}],
					"position": 1
				}, {
					"items": [{
						"type": "fragment",
						"amount": 60
					}],
					"position": 9
				}, {
					"items": [{
						"type": "fragment",
						"amount": 60
					}],
					"position": 16
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 2
					}],
					"position": 17
				}, {
					"items": [{
						"type": "fragment",
						"amount": 60
					}],
					"position": 18
				}, {
					"items": [{
						"type": "fragment",
						"amount": 60
					}],
					"position": 25
				}, {
					"items": [{
						"type": "fragment",
						"amount": 60
					}],
					"position": 33
				}, {
					"items": [{
						"id": "guardina",
						"type": "world_song"
					}],
					"position": 34
				}]
			}, {
				"map_id": "etherstrike",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 3,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "rei",
				"require_type": "pack",
				"coordinate": "0,-40",
				"step_count": 36,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 5
				}, {
					"items": [{
						"id": "etherstrike",
						"type": "world_song"
					}],
					"position": 10
				}, {
					"items": [{
						"type": "fragment",
						"amount": 0
					}],
					"position": 26
				}, {
					"items": [{
						"type": "fragment",
						"amount": 0
					}],
					"position": 27
				}, {
					"items": [{
						"type": "fragment",
						"amount": 0
					}],
					"position": 28
				}, {
					"items": [{
						"type": "fragment",
						"amount": 0
					}],
					"position": 29
				}, {
					"items": [{
						"type": "fragment",
						"amount": 0
					}],
					"position": 30
				}, {
					"items": [{
						"type": "fragment",
						"amount": 0
					}],
					"position": 31
				}, {
					"items": [{
						"type": "fragment",
						"amount": 0
					}],
					"position": 32
				}, {
					"items": [{
						"type": "fragment",
						"amount": 0
					}],
					"position": 33
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 34
				}, {
					"items": [{
						"id": "14",
						"type": "character"
					}],
					"position": 35
				}]
			}, {
				"map_id": "fractureray",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 3,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "rei",
				"require_type": "pack",
				"require_localunlock_songid": "fractureray",
				"coordinate": "0,160",
				"step_count": 23,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 150
					}],
					"position": 13
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 14
				}, {
					"items": [{
						"type": "fragment",
						"amount": 250
					}],
					"position": 16
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 17
				}, {
					"items": [{
						"type": "fragment",
						"amount": 350
					}],
					"position": 19
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 20
				}, {
					"items": [{
						"id": "15",
						"type": "character"
					}],
					"position": 22
				}]
			}, {
				"map_id": "chapter3_light",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 3,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "",
				"require_type": "fragment",
				"require_value": 200,
				"coordinate": "-480,180",
				"step_count": 76,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 144
					}],
					"position": 10
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 13
				}, {
					"items": [{
						"type": "fragment",
						"amount": 169
					}],
					"position": 20
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 23
				}, {
					"items": [{
						"id": "suomi",
						"type": "world_song"
					}],
					"position": 30
				}, {
					"items": [{
						"type": "fragment",
						"amount": 225
					}],
					"position": 40
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 43
				}, {
					"items": [{
						"type": "fragment",
						"amount": 256
					}],
					"position": 50
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 53
				}, {
					"items": [{
						"id": "rugie",
						"type": "world_song"
					}],
					"position": 59
				}, {
					"items": [{
						"type": "core",
						"id": "core_hollow",
						"amount": 5
					}],
					"position": 65
				}, {
					"items": [{
						"type": "core",
						"id": "core_hollow",
						"amount": 5
					}],
					"position": 70
				}, {
					"items": [{
						"type": "core",
						"id": "core_hollow",
						"amount": 5
					}],
					"position": 75
				}]
			}, {
				"map_id": "chapter3_conflict",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 3,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "",
				"require_type": "fragment",
				"require_value": 200,
				"coordinate": "-360,0",
				"step_count": 85,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 5
				}, {
					"items": [{
						"type": "fragment",
						"amount": 10
					}],
					"position": 10
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 15
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 19
				}, {
					"items": [{
						"type": "fragment",
						"amount": 15
					}],
					"position": 20
				}, {
					"items": [{
						"type": "fragment",
						"amount": 150
					}],
					"position": 25
				}, {
					"items": [{
						"id": "bookmaker",
						"type": "world_song"
					}],
					"position": 30
				}, {
					"items": [{
						"type": "fragment",
						"amount": 200
					}],
					"position": 35
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 2
					}],
					"position": 39
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 40
				}, {
					"items": [{
						"type": "fragment",
						"amount": 250
					}],
					"position": 45
				}, {
					"items": [{
						"id": "darakunosono",
						"type": "world_song"
					}],
					"position": 49
				}, {
					"items": [{
						"type": "fragment",
						"amount": 30
					}],
					"position": 50
				}, {
					"items": [{
						"type": "fragment",
						"amount": 300
					}],
					"position": 55
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 3
					}],
					"position": 59
				}, {
					"items": [{
						"type": "fragment",
						"amount": 40
					}],
					"position": 60
				}, {
					"items": [{
						"id": "espebranch",
						"type": "world_song"
					}],
					"position": 62
				}, {
					"items": [{
						"type": "core",
						"id": "core_desolate",
						"amount": 5
					}],
					"position": 70
				}, {
					"items": [{
						"type": "core",
						"id": "core_desolate",
						"amount": 5
					}],
					"position": 75
				}, {
					"items": [{
						"type": "core",
						"id": "core_desolate",
						"amount": 5
					}],
					"position": 84
				}]
			}, {
				"map_id": "chapter3_conflict_2",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 3,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "",
				"require_type": "fragment",
				"require_value": 200,
				"coordinate": "-240,-180",
				"step_count": 51,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 4
				}, {
					"items": [{
						"type": "fragment",
						"amount": 125
					}],
					"position": 9
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 14
				}, {
					"items": [{
						"type": "fragment",
						"amount": 125
					}],
					"position": 19
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 24
				}, {
					"items": [{
						"type": "fragment",
						"amount": 125
					}],
					"position": 29
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 34
				}, {
					"items": [{
						"type": "fragment",
						"amount": 125
					}],
					"position": 39
				}, {
					"items": [{
						"id": "nhelv",
						"type": "world_song"
					}],
					"position": 40
				}, {
					"items": [{
						"type": "core",
						"id": "core_ambivalent",
						"amount": 5
					}],
					"position": 45
				}, {
					"items": [{
						"type": "core",
						"id": "core_ambivalent",
						"amount": 5
					}],
					"position": 50
				}]
			}, {
				"map_id": "tonesphere",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 3,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "tonesphere",
				"require_type": "pack",
				"coordinate": "480,180",
				"step_count": 38,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 90
					}],
					"position": 4
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 10
				}, {
					"items": [{
						"type": "fragment",
						"amount": 90
					}],
					"position": 14
				}, {
					"items": [{
						"type": "fragment",
						"amount": 90
					}],
					"position": 22
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 28
				}, {
					"items": [{
						"type": "fragment",
						"amount": 90
					}],
					"position": 32
				}, {
					"items": [{
						"id": "18",
						"type": "character"
					}],
					"position": 37
				}]
			}, {
				"map_id": "groovecoaster",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 3,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "groovecoaster",
				"require_type": "pack",
				"coordinate": "360,0",
				"step_count": 46,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 55
					}],
					"position": 15
				}, {
					"items": [{
						"type": "fragment",
						"amount": 66
					}],
					"position": 23
				}, {
					"items": [{
						"type": "fragment",
						"amount": 77
					}],
					"position": 29
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 30
				}, {
					"items": [{
						"type": "fragment",
						"amount": 88
					}],
					"position": 34
				}, {
					"items": [{
						"type": "fragment",
						"amount": 99
					}],
					"position": 39
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 40
				}, {
					"items": [{
						"id": "22",
						"type": "character"
					}],
					"position": 45
				}]
			}, {
				"map_id": "solitarydream",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 5,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "core",
				"require_type": "pack",
				"coordinate": "-250,0",
				"step_count": 10,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"id": "solitarydream",
						"type": "world_song"
					}],
					"position": 9
				}]
			}, {
				"map_id": "zettai",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 4,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "zettai",
				"require_type": "pack",
				"coordinate": "-100,115",
				"step_count": 26,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 5
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 10
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 15
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 20
				}, {
					"items": [{
						"id": "23",
						"type": "character"
					}],
					"position": 25
				}]
			}, {
				"map_id": "chapter4_ripples",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 4,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "",
				"require_type": "fragment",
				"require_value": 200,
				"coordinate": "-280,-200",
				"step_count": 51,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 170
					}],
					"position": 4
				}, {
					"items": [{
						"type": "fragment",
						"amount": 170
					}],
					"position": 12
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 16
				}, {
					"items": [{
						"id": "grimheart",
						"type": "world_song"
					}],
					"position": 20
				}, {
					"items": [{
						"type": "fragment",
						"amount": 190
					}],
					"position": 26
				}, {
					"items": [{
						"type": "fragment",
						"amount": 190
					}],
					"position": 42
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 46
				}, {
					"items": [{
						"id": "vector",
						"type": "world_song"
					}],
					"position": 50
				}]
			}, {
				"map_id": "chapter4_waves",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 4,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "",
				"require_type": "fragment",
				"require_value": 200,
				"coordinate": "-480,-200",
				"step_count": 41,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 150
					}],
					"position": 5
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 8
				}, {
					"items": [{
						"type": "fragment",
						"amount": 150
					}],
					"position": 15
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 18
				}, {
					"items": [{
						"id": "revixy",
						"type": "world_song"
					}],
					"position": 25
				}, {
					"items": [{
						"type": "fragment",
						"amount": 400
					}],
					"position": 30
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 33
				}, {
					"items": [{
						"id": "supernova",
						"type": "world_song"
					}],
					"position": 40
				}]
			}, {
				"map_id": "chunithm",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 4,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "chunithm",
				"require_type": "pack",
				"coordinate": "480,200",
				"step_count": 28,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 110
					}],
					"position": 5
				}, {
					"items": [{
						"type": "fragment",
						"amount": 120
					}],
					"position": 10
				}, {
					"items": [{
						"id": "worldvanquisher",
						"type": "world_song"
					}],
					"position": 15
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 2
					}],
					"position": 20
				}, {
					"items": [{
						"id": "24",
						"type": "character"
					}],
					"position": 27
				}]
			}, {
				"map_id": "omatsuri",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 4,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "omatsuri",
				"require_type": "pack",
				"coordinate": "280,200",
				"step_count": 21,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 230
					}],
					"position": 3
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 6
				}, {
					"items": [{
						"type": "fragment",
						"amount": 230
					}],
					"position": 9
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 12
				}, {
					"items": [{
						"id": "30",
						"type": "character"
					}],
					"position": 15
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 2
					}],
					"position": 20
				}]
			}, {
				"map_id": "chapter4_the_calm",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 4,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "",
				"require_type": "fragment",
				"require_value": 200,
				"coordinate": "-380,-30",
				"step_count": 146,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 10
					}],
					"position": 1
				}, {
					"items": [{
						"type": "fragment",
						"amount": 10
					}],
					"position": 2
				}, {
					"items": [{
						"type": "fragment",
						"amount": 10
					}],
					"position": 3
				}, {
					"items": [{
						"type": "fragment",
						"amount": 10
					}],
					"position": 4
				}, {
					"items": [{
						"type": "fragment",
						"amount": 15
					}],
					"position": 11
				}, {
					"items": [{
						"type": "fragment",
						"amount": 15
					}],
					"position": 12
				}, {
					"items": [{
						"type": "fragment",
						"amount": 15
					}],
					"position": 13
				}, {
					"items": [{
						"type": "fragment",
						"amount": 15
					}],
					"position": 14
				}, {
					"items": [{
						"type": "fragment",
						"amount": 20
					}],
					"position": 21
				}, {
					"items": [{
						"type": "fragment",
						"amount": 20
					}],
					"position": 22
				}, {
					"items": [{
						"type": "fragment",
						"amount": 20
					}],
					"position": 23
				}, {
					"items": [{
						"type": "fragment",
						"amount": 20
					}],
					"position": 24
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 31
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 32
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 33
				}, {
					"items": [{
						"type": "fragment",
						"amount": 25
					}],
					"position": 34
				}, {
					"items": [{
						"type": "fragment",
						"amount": 30
					}],
					"position": 41
				}, {
					"items": [{
						"type": "fragment",
						"amount": 30
					}],
					"position": 42
				}, {
					"items": [{
						"type": "fragment",
						"amount": 30
					}],
					"position": 43
				}, {
					"items": [{
						"type": "fragment",
						"amount": 30
					}],
					"position": 44
				}, {
					"items": [{
						"type": "fragment",
						"amount": 35
					}],
					"position": 51
				}, {
					"items": [{
						"type": "fragment",
						"amount": 35
					}],
					"position": 52
				}, {
					"items": [{
						"type": "fragment",
						"amount": 35
					}],
					"position": 53
				}, {
					"items": [{
						"id": "diode",
						"type": "world_song"
					}],
					"position": 54
				}, {
					"items": [{
						"type": "fragment",
						"amount": 40
					}],
					"position": 62
				}, {
					"items": [{
						"type": "fragment",
						"amount": 40
					}],
					"position": 64
				}, {
					"items": [{
						"type": "fragment",
						"amount": 45
					}],
					"position": 72
				}, {
					"items": [{
						"type": "fragment",
						"amount": 45
					}],
					"position": 74
				}, {
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 82
				}, {
					"items": [{
						"type": "fragment",
						"amount": 50
					}],
					"position": 84
				}, {
					"items": [{
						"type": "fragment",
						"amount": 55
					}],
					"position": 92
				}, {
					"items": [{
						"id": "freefall",
						"type": "world_song"
					}],
					"position": 94
				}, {
					"items": [{
						"type": "fragment",
						"amount": 60
					}],
					"position": 102
				}, {
					"items": [{
						"type": "fragment",
						"amount": 60
					}],
					"position": 104
				}, {
					"items": [{
						"type": "fragment",
						"amount": 65
					}],
					"position": 112
				}, {
					"items": [{
						"type": "fragment",
						"amount": 65
					}],
					"position": 114
				}, {
					"items": [{
						"type": "fragment",
						"amount": 70
					}],
					"position": 122
				}, {
					"items": [{
						"type": "fragment",
						"amount": 70
					}],
					"position": 124
				}, {
					"items": [{
						"type": "fragment",
						"amount": 75
					}],
					"position": 132
				}, {
					"items": [{
						"id": "monochromeprincess",
						"type": "world_song"
					}],
					"position": 134
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 3
					}],
					"position": 145
				}]
			}, {
				"map_id": "gloryroad",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 4,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "shiawase",
				"require_type": "pack",
				"coordinate": "380,30",
				"step_count": 28,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 1
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 4
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 11
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 14
				}, {
					"items": [{
						"id": "gloryroad",
						"type": "world_song"
					}],
					"position": 20
				}, {
					"items": [{
						"type": "core",
						"id": "core_crimson",
						"amount": 5
					}],
					"position": 23
				}, {
					"items": [{
						"type": "core",
						"id": "core_crimson",
						"amount": 5
					}],
					"position": 25
				}, {
					"items": [{
						"type": "core",
						"id": "core_crimson",
						"amount": 5
					}],
					"position": 27
				}]
			}, {
				"map_id": "blrink",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 5,
				"available_from": -1,
				"available_to": 9999999999999,
				"is_repeatable": False,
				"require_id": "prelude",
				"require_type": "pack",
				"coordinate": "250,0",
				"step_count": 17,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"id": "blrink",
						"type": "world_song"
					}],
					"position": 16
				}]
			}, {
				"map_id": "corpssansorganes",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 2,
				"available_from": -1,
				"available_to": 2106124800000,
				"is_repeatable": False,
				"require_id": "mirai",
				"require_type": "pack",
				"coordinate": "0,200",
				"step_count": 42,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 105
					}],
					"position": 6
				}, {
					"items": [{
						"type": "fragment",
						"amount": 105
					}],
					"position": 12
				}, {
					"items": [{
						"type": "fragment",
						"amount": 105
					}],
					"position": 22
				}, {
					"items": [{
						"type": "fragment",
						"amount": 105
					}],
					"position": 28
				}, {
					"items": [{
						"id": "corpssansorganes",
						"type": "world_song"
					}],
					"position": 31
				}, {
					"items": [{
						"type": "core",
						"id": "core_ambivalent",
						"amount": 5
					}],
					"position": 35
				}, {
					"items": [{
						"type": "core",
						"id": "core_ambivalent",
						"amount": 5
					}],
					"position": 38
				}, {
					"items": [{
						"type": "core",
						"id": "core_ambivalent",
						"amount": 5
					}],
					"position": 41
				}]
			}, {
				"map_id": "lostdesire",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 5,
				"available_from": -1,
				"available_to": 9999999999999,
				"is_repeatable": False,
				"require_id": "vs",
				"require_type": "pack",
				"coordinate": "0,0",
				"step_count": 36,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"id": "lostdesire",
						"type": "world_song"
					}],
					"position": 5
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 2
					}],
					"position": 15
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 2
					}],
					"position": 25
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 2
					}],
					"position": 35
				}]
			}, {
				"map_id": "tempestissimo",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 5,
				"available_from": -1,
				"available_to": 9999999999999,
				"is_repeatable": False,
				"require_id": "vs",
				"require_type": "pack",
				"require_localunlock_challengeid": "tempestissimo",
				"coordinate": "0,160",
				"step_count": 16,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"id": "35",
						"type": "character"
					}],
					"position": 3
				}, {
					"items": [{
						"type": "fragment",
						"amount": 1000
					}],
					"position": 15
				}]
			}, {
				"map_id": "chapter_1_scenery",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 1,
				"available_from": -1,
				"available_to": 9999999999999,
				"is_repeatable": True,
				"require_id": "",
				"require_type": "chapter_step",
				"require_value": 455,
				"coordinate": "0,150",
				"step_count": 51,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "world_unlock",
						"id": "scenery_chap1"
					}],
					"position": 5
				}, {
					"items": [{
						"type": "fragment",
						"amount": 70
					}],
					"position": 10
				}, {
					"items": [{
						"type": "fragment",
						"amount": 80
					}],
					"position": 15
				}, {
					"items": [{
						"type": "fragment",
						"amount": 90
					}],
					"position": 20
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 25
				}, {
					"items": [{
						"type": "fragment",
						"amount": 110
					}],
					"position": 30
				}, {
					"items": [{
						"type": "fragment",
						"amount": 120
					}],
					"position": 35
				}, {
					"items": [{
						"type": "fragment",
						"amount": 130
					}],
					"position": 40
				}, {
					"items": [{
						"type": "fragment",
						"amount": 250
					}],
					"position": 50
				}]
			}, {
				"map_id": "chapter_2_scenery",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 2,
				"available_from": -1,
				"available_to": 9999999999999,
				"is_repeatable": True,
				"require_id": "",
				"require_type": "chapter_step",
				"require_value": 105,
				"coordinate": "0,-20",
				"step_count": 51,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "world_unlock",
						"id": "scenery_chap2"
					}],
					"position": 5
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 11
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 12
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 13
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 14
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 31
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 32
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 33
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 34
				}, {
					"items": [{
						"type": "fragment",
						"amount": 150
					}],
					"position": 50
				}]
			}, {
				"map_id": "chapter_3_scenery",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 3,
				"available_from": -1,
				"available_to": 9999999999999,
				"is_repeatable": True,
				"require_id": "",
				"require_type": "chapter_step",
				"require_value": 205,
				"coordinate": "240,-180",
				"step_count": 17,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "world_unlock",
						"id": "scenery_chap3"
					}],
					"position": 5
				}, {
					"items": [{
						"type": "fragment",
						"amount": 400
					}],
					"position": 16
				}]
			}, {
				"map_id": "chapter_4_scenery",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 4,
				"available_from": -1,
				"available_to": 9999999999999,
				"is_repeatable": True,
				"require_id": "",
				"require_type": "chapter_step",
				"require_value": 240,
				"coordinate": "100,-115",
				"step_count": 101,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "world_unlock",
						"id": "scenery_chap4"
					}],
					"position": 5
				}, {
					"items": [{
						"type": "fragment",
						"amount": 2000
					}],
					"position": 100
				}]
			}, {
				"map_id": "chapter_5_scenery",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 5,
				"available_from": -1,
				"available_to": 9999999999999,
				"is_repeatable": True,
				"require_id": "",
				"require_type": "chapter_step",
				"require_value": 75,
				"coordinate": "0,-160",
				"step_count": 31,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "world_unlock",
						"id": "scenery_chap5"
					}],
					"position": 5
				}, {
					"items": [{
						"type": "fragment",
						"amount": 250
					}],
					"position": 10
				}, {
					"items": [{
						"type": "fragment",
						"amount": 250
					}],
					"position": 20
				}, {
					"items": [{
						"type": "fragment",
						"amount": 500
					}],
					"position": 30
				}]
			}, {
				"map_id": "byd_goodtek",
				"is_legacy": False,
				"chapter": 1001,
				"available_from": -1,
				"available_to": 9999999999999,
				"is_repeatable": False,
				"require_id": "goodtek2",
				"require_type": "chart_unlock",
				"coordinate": "900,650",
				"is_beyond": True,
				"stamina_cost": 3,
				"beyond_health": 250,
				"character_affinity": [0, 1],
				"affinity_multiplier": [2.5, 1.5],
				"step_count": 6,
				"custom_bg": "",
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 2
				}, {
					"items": [{
						"type": "fragment",
						"amount": 250
					}],
					"position": 10
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 24
				}, {
					"items": [{
						"type": "fragment",
						"amount": 275
					}],
					"position": 31
				}, {
					"items": [{
						"id": "goodtek3",
						"type": "world_song"
					}],
					"position": 33
				}]
			}, {
				"map_id": "byd_vexaria",
				"is_legacy": False,
				"chapter": 1001,
				"available_from": -1,
				"available_to": 9999999999999,
				"is_repeatable": False,
				"require_id": "vexaria2",
				"require_type": "chart_unlock",
				"coordinate": "650,400",
				"is_beyond": True,
				"stamina_cost": 3,
				"beyond_health": 150,
				"character_affinity": [0, 1],
				"affinity_multiplier": [2.5, 1.5],
				"step_count": 3,
				"custom_bg": "",
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 616
					}],
					"position": 42
				}, {
					"items": [{
						"id": "vexaria3",
						"type": "world_song"
					}],
					"position": 46
				}]
			}, {
				"map_id": "byd_fairytale",
				"is_legacy": False,
				"chapter": 1001,
				"available_from": -1,
				"available_to": 9999999999999,
				"is_repeatable": False,
				"require_id": "fairytale2",
				"require_type": "chart_unlock",
				"coordinate": "400,650",
				"is_beyond": True,
				"stamina_cost": 3,
				"beyond_health": 200,
				"character_affinity": [0, 1],
				"affinity_multiplier": [2.5, 1.5],
				"step_count": 3,
				"custom_bg": "",
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 4
					}],
					"position": 20
				}, {
					"items": [{
						"id": "fairytale3",
						"type": "world_song"
					}],
					"position": 55
				}]
			}, {
				"map_id": "byd_infinityheaven",
				"is_legacy": False,
				"chapter": 1001,
				"available_from": -1,
				"available_to": 9999999999999,
				"is_repeatable": False,
				"require_id": "infinityheaven2",
				"require_type": "chart_unlock",
				"coordinate": "650,900",
				"is_beyond": True,
				"stamina_cost": 3,
				"beyond_health": 200,
				"character_affinity": [0, 1],
				"affinity_multiplier": [2.5, 1.5],
				"step_count": 9,
				"custom_bg": "",
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 1
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 2
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 3
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 2
					}],
					"position": 4
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 5
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 6
				}, {
					"items": [{
						"type": "fragment",
						"amount": 100
					}],
					"position": 7
				}, {
					"items": [{
						"id": "infinityheaven3",
						"type": "world_song"
					}],
					"position": 8
				}]
			}, {
				"map_id": "byd_purgatorium",
				"is_legacy": False,
				"chapter": 1001,
				"available_from": -1,
				"available_to": 9999999999999,
				"is_repeatable": False,
				"require_id": "purgatorium2",
				"require_type": "chart_unlock",
				"coordinate": "-900,-650",
				"is_beyond": True,
				"stamina_cost": 3,
				"beyond_health": 200,
				"character_affinity": [13, 1],
				"affinity_multiplier": [2.6, 1.6],
				"step_count": 5,
				"custom_bg": "",
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 2
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 14
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 30
				}, {
					"items": [{
						"id": "purgatorium3",
						"type": "world_song"
					}],
					"position": 37
				}]
			}, {
				"map_id": "byd_dement",
				"is_legacy": False,
				"chapter": 1001,
				"available_from": -1,
				"available_to": 9999999999999,
				"is_repeatable": False,
				"require_id": "dement2",
				"require_type": "chart_unlock",
				"coordinate": "-400,-650",
				"is_beyond": True,
				"stamina_cost": 3,
				"beyond_health": 250,
				"character_affinity": [13, 1],
				"affinity_multiplier": [2.6, 1.6],
				"step_count": 4,
				"custom_bg": "",
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 1
					}],
					"position": 19
				}, {
					"items": [{
						"type": "fragment",
						"amount": 1200
					}],
					"position": 39
				}, {
					"items": [{
						"id": "dement3",
						"type": "world_song"
					}],
					"position": 43
				}]
			}, {
				"map_id": "maliciousmischance_event",
				"is_legacy": False,
				"is_beyond": False,
				"beyond_health": 100,
				"character_affinity": [],
				"affinity_multiplier": [],
				"chapter": 0,
				"available_from": 1599177600000,
				"available_to": 1599836400000,
				"is_repeatable": False,
				"require_id": "maliciousmischance",
				"require_type": "single",
				"coordinate": "0,0",
				"step_count": 87,
				"custom_bg": "",
				"stamina_cost": 2,
				"curr_position": 0,
				"curr_capture": 0,
				"is_locked": True,
				"rewards": [{
					"items": [{
						"type": "fragment",
						"amount": 250
					}],
					"position": 62
				}, {
					"items": [{
						"type": "fragment",
						"amount": 250
					}],
					"position": 63
				}, {
					"items": [{
						"type": "fragment",
						"amount": 250
					}],
					"position": 67
				}, {
					"items": [{
						"type": "fragment",
						"amount": 250
					}],
					"position": 68
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 2
					}],
					"position": 72
				}, {
					"items": [{
						"type": "core",
						"id": "core_generic",
						"amount": 2
					}],
					"position": 73
				}, {
					"items": [{
						"type": "fragment",
						"amount": 250
					}],
					"position": 77
				}, {
					"items": [{
						"type": "fragment",
						"amount": 250
					}],
					"position": 78
				}, {
					"items": [{
						"type": "fragment",
						"amount": 250
					}],
					"position": 82
				}, {
					"items": [{
						"type": "fragment",
						"amount": 250
					}],
					"position": 83
				}, {
					"items": [{
						"id": "37",
						"type": "character"
					}],
					"position": 86
				}]
			}]
		}}
        ]}

    conn.commit()
    conn.close()
    return r
