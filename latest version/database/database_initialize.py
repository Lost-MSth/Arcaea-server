import sqlite3
import time
import json

# 数据库初始化文件，删掉arcaea_database.db文件后运行即可，谨慎使用

ARCAEA_SERVER_VERSION = 'v2.7.2'


def main(path='./'):
    conn = sqlite3.connect(path+'arcaea_database.db')
    c = conn.cursor()
    c.execute('''create table if not exists config(id text primary key,
    value text
    );''')
    c.execute('''insert into config values("version", :a);''',
              {'a': ARCAEA_SERVER_VERSION})
    c.execute('''create table if not exists user(user_id int primary key,
    name text unique,
    password text not null,
    join_date char(20),
    user_code char(10),
    rating_ptt int,
    character_id int,
    is_skill_sealed int,
    is_char_uncapped int,
    is_char_uncapped_override int,
    is_hide_rating int,
    song_id text,
    difficulty int,
    score int,
    shiny_perfect_count int,
    perfect_count int,
    near_count int,
    miss_count int,
    health int,
    modifier int,
    time_played int,
    clear_type int,
    rating real,
    favorite_character int,
    max_stamina_notification_enabled int,
    current_map text,
    ticket int,
    prog_boost int,
    email text,
    world_rank_score int,
    ban_flag text,
    next_fragstam_ts int,
    max_stamina_ts int,
    stamina int
    );''')
    c.execute('''create table if not exists login(access_token text,
    user_id int,
    login_time int,
    login_ip text,
    login_device text,
    primary key(access_token, user_id)
    );''')
    c.execute('''create table if not exists friend(user_id_me int,
    user_id_other int,
    primary key (user_id_me, user_id_other)
    );''')
    c.execute('''create table if not exists best_score(user_id int,
    song_id text,
    difficulty int,
    score int,
    shiny_perfect_count int,
    perfect_count int,
    near_count int,
    miss_count int,
    health int,
    modifier int,
    time_played int,
    best_clear_type int,
    clear_type int,
    rating real,
    primary key(user_id, song_id, difficulty)
    );''')
    c.execute('''create table if not exists user_char(user_id int,
    character_id int,
    level int,
    exp real,
    is_uncapped int,
    is_uncapped_override int,
    primary key(user_id, character_id)
    );''')
    c.execute('''create table if not exists user_char_full(user_id int,
    character_id int,
    level int,
    exp real,
    is_uncapped int,
    is_uncapped_override int,
    primary key(user_id, character_id)
    );''')
    c.execute('''create table if not exists character(character_id int primary key,
    name text,
    max_level int,
    frag1 real,
    prog1 real,
    overdrive1 real,
    frag20 real,
    prog20 real,
    overdrive20 real,
    frag30 real,
    prog30 real,
    overdrive30 real,
    skill_id text,
    skill_unlock_level int,
    skill_requires_uncap int,
    skill_id_uncap text,
    char_type int,
    is_uncapped int
    );''')
    c.execute('''create table if not exists char_item(character_id int,
    item_id text,
    type text,
    amount int,
    primary key(character_id, item_id, type)
    );''')
    c.execute('''create table if not exists recent30(user_id int primary key,
    r0 real,
    song_id0 text,
    r1 real,
    song_id1 text,
    r2 real,
    song_id2 text,
    r3 real,
    song_id3 text,
    r4 real,
    song_id4 text,
    r5 real,
    song_id5 text,
    r6 real,
    song_id6 text,
    r7 real,
    song_id7 text,
    r8 real,
    song_id8 text,
    r9 real,
    song_id9 text,
    r10 real,
    song_id10 text,
    r11 real,
    song_id11 text,
    r12 real,
    song_id12 text,
    r13 real,
    song_id13 text,
    r14 real,
    song_id14 text,
    r15 real,
    song_id15 text,
    r16 real,
    song_id16 text,
    r17 real,
    song_id17 text,
    r18 real,
    song_id18 text,
    r19 real,
    song_id19 text,
    r20 real,
    song_id20 text,
    r21 real,
    song_id21 text,
    r22 real,
    song_id22 text,
    r23 real,
    song_id23 text,
    r24 real,
    song_id24 text,
    r25 real,
    song_id25 text,
    r26 real,
    song_id26 text,
    r27 real,
    song_id27 text,
    r28 real,
    song_id28 text,
    r29 real,
    song_id29 text
    );''')
    c.execute('''create table if not exists user_world(user_id int,
    map_id text,
    curr_position int,
    curr_capture real,
    is_locked int,
    primary key(user_id, map_id)
    );''')
    c.execute('''create table if not exists world_songplay(user_id int,
    song_id text,
    difficulty int,
    stamina_multiply int,
    fragment_multiply int,
    prog_boost_multiply int,
    primary key(user_id, song_id, difficulty)
    );''')
    c.execute('''create table if not exists download_token(user_id int,
    song_id text,
    file_name text,
    token text,
    time int,
    primary key(user_id, song_id, file_name)
    );''')
    c.execute('''create table if not exists user_download(user_id int,
    token text,
    time int,
    primary key(user_id, token, time)
    );''')
    c.execute('''create table if not exists item(item_id text,
    type text,
    is_available int,
    _id text,
    primary key(item_id, type)
    );''')
    c.execute('''create table if not exists user_item(user_id int,
    item_id text,
    type text,
    amount int,
    primary key(user_id, item_id, type)
    );''')
    c.execute('''create table if not exists purchase(purchase_name text primary key,
    price int,
    orig_price int,
    discount_from int,
    discount_to int
    );''')
    c.execute('''create table if not exists purchase_item(purchase_name text,
    item_id text,
    type text,
    amount int,
    primary key(purchase_name, item_id, type)
    );''')
    c.execute('''create table if not exists user_save(user_id int primary key,
    scores_data text,
    clearlamps_data text,
    clearedsongs_data text,
    unlocklist_data text,
    installid_data text,
    devicemodelname_data text,
    story_data text,
    createdAt int
    );''')
    c.execute('''create table if not exists present(present_id text primary key,
    expire_ts int,
    description text
    );''')
    c.execute('''create table if not exists user_present(user_id int,
    present_id text,
    primary key(user_id, present_id)
    );''')
    c.execute('''create table if not exists present_item(present_id text,
    item_id text,
    type text,
    amount int,
    primary key(present_id, item_id, type)
    );''')
    c.execute('''create table if not exists songfile(song_id text,
    file_type int,
    md5 text,
    primary key(song_id, file_type)
    );''')
    c.execute('''create table if not exists redeem(code text primary key,
    type int
    );''')
    c.execute('''create table if not exists user_redeem(user_id int,
    code text,
    primary key(user_id, code)
    );''')
    c.execute('''create table if not exists redeem_item(code text,
    item_id text,
    type text,
    amount int,
    primary key(code, item_id, type)
    );''')

    c.execute('''create table if not exists role(role_id int primary key,
    role_name text,
    caption text
    );''')
    c.execute('''create table if not exists user_role(user_id int,
    role_id int,
    primary key(user_id, role_id)
    );''')
    c.execute('''create table if not exists power(power_id int primary key,
    power_name text,
    caption text
    );''')
    c.execute('''create table if not exists role_power(role_id int,
    power_id int,
    primary key(role_id, power_id)
    );''')
    c.execute('''create table if not exists api_login(user_id int,
    token text,
    login_time int,
    login_ip text,
    primary key(user_id, token)
    );''')

    # 搭档初始化
    char = ['hikari', 'tairitsu', 'kou', 'sapphire', 'lethe', '', 'Tairitsu(Axium)', 'Tairitsu(Grievous Lady)', 'stella', 'Hikari & Fisica', 'ilith', 'eto', 'luna', 'shirabe', 'Hikari(Zero)', 'Hikari(Fracture)', 'Hikari(Summer)', 'Tairitsu(Summer)', 'Tairitsu & Trin',
            'ayu', 'Eto & Luna', 'yume', 'Seine & Hikari', 'saya', 'Tairitsu & Chuni Penguin', 'Chuni Penguin', 'haruna', 'nono', 'MTA-XXX', 'MDA-21', 'kanae', 'Hikari(Fantasia)', 'Tairitsu(Sonata)', 'sia', 'DORO*C', 'Tairitsu(Tempest)', 'brillante', 'Ilith(Summer)', 'etude', 'Alice & Tenniel', 'Luna & Mia', 'areus', 'seele', 'isabelle', 'mir', 'lagrange', 'linka', 'nami', 'Saya & Elizabeth', 'lily', 'kanae(midsummer)', 'alice&tenniel(minuet)', 'tairitsu(elegy)', 'marija']

    skill_id = ['gauge_easy', '', '', '', 'note_mirror', '', '', 'gauge_hard', 'frag_plus_10_pack_stellights', 'gauge_easy|frag_plus_15_pst&prs', 'gauge_hard|fail_frag_minus_100', 'frag_plus_5_side_light', 'visual_hide_hp', 'frag_plus_5_side_conflict', 'challenge_fullcombo_0gauge', 'gauge_overflow', 'gauge_easy|note_mirror', 'note_mirror', 'visual_tomato_pack_tonesphere',
                'frag_rng_ayu', 'gaugestart_30|gaugegain_70', 'combo_100-frag_1', 'audio_gcemptyhit_pack_groovecoaster', 'gauge_saya', 'gauge_chuni', 'kantandeshou', 'gauge_haruna', 'frags_nono', 'gauge_pandora', 'gauge_regulus', 'omatsuri_daynight', '', '', 'sometimes(note_mirror|frag_plus_5)', 'scoreclear_aa|visual_scoregauge', 'gauge_tempest', 'gauge_hard', 'gauge_ilith_summer', '', 'note_mirror|visual_hide_far', 'frags_ongeki', 'gauge_areus', 'gauge_seele', 'gauge_isabelle', 'gauge_exhaustion', 'skill_lagrange', 'gauge_safe_10', 'frags_nami', 'skill_elizabeth', 'skill_lily', 'skill_kanae_midsummer', '', '', 'visual_ghost_skynotes']

    skill_id_uncap = ['', '', 'frags_kou', '', 'visual_ink', '', '', '', '', '', '', 'eto_uncap', 'luna_uncap', 'shirabe_entry_fee',
                      '', '', '', '', '', '', '', 'frags_yume', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']

    skill_unlock_level = [0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 8, 8, 8, 0, 0, 0, 0, 0,
                          0, 0, 0, 8, 0, 14, 0, 0, 8, 8, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8]

    frag1 = [55, 55, 60, 50, 47, 0, 47, 57, 41, 22, 50, 54, 60, 56, 78, 42, 41, 61, 52, 50, 52, 32,
             42, 55, 45, 58, 43, 0.5, 68, 50, 62, 45, 45, 52, 44, 27, 59, 0, 45, 50, 50, 47, 47, 61, 43, 42, 50, 25, 58, 50, 61, 45, 45, 38]

    prog1 = [35, 55, 47, 50, 60, 0, 60, 70, 58, 45, 70, 45, 42, 46, 61, 67, 49, 44, 28, 45, 24, 46, 52,
             59, 62, 33, 58, 25, 63, 69, 50, 45, 45, 51, 34, 70, 62, 70, 45, 32, 32, 61, 47, 47, 37, 42, 50, 50, 45, 41, 61, 45, 45, 58]

    overdrive1 = [35, 55, 25, 50, 47, 0, 72, 57, 41, 7, 10, 32, 65, 31, 61, 53, 31, 47, 38, 12, 39, 18,
                  48, 65, 45, 55, 44, 25, 46, 44, 33, 45, 45, 37, 25, 27, 50, 20, 45, 63, 21, 47, 61, 47, 65, 80, 50, 30, 49, 15, 34, 45, 45, 38]

    frag20 = [78, 80, 90, 75, 70, 0, 70, 79, 65, 40, 50, 80, 90, 82, 0, 61, 67, 92, 85, 50, 86, 52,
              65, 85, 67, 88, 64, 0.5, 95, 70, 95, 50, 80, 87, 71, 50, 85, 0, 80, 75, 50, 70, 70, 90, 65, 80, 100, 50, 68, 60, 90, 67, 50, 60]

    prog20 = [61, 80, 70, 75, 90, 0, 90, 102, 84, 78, 105, 67, 63, 68, 0, 99, 80, 66, 46, 83, 40, 73,
              80, 90, 93, 50, 86, 78, 89, 98, 75, 80, 50, 64, 55, 100, 90, 110, 80, 50, 74, 90, 70, 70, 56, 80, 100, 55, 65, 59, 90, 50, 90, 90]

    overdrive20 = [61, 80, 47, 75, 70, 0, 95, 79, 65, 31, 50, 59, 90, 58, 0, 78, 50, 70, 62, 49, 64,
                   46, 73, 95, 67, 84, 70, 78, 69, 70, 50, 80, 80, 63, 25, 50, 72, 55, 50, 95, 55, 70, 90, 70, 99, 80, 100, 40, 69, 62, 51, 90, 67, 60]

    frag30 = [88, 90, 100, 75, 80, 0, 70, 79, 65, 40, 50, 90, 100, 92, 0, 61, 67, 92, 85, 50, 86, 62,
              65, 85, 67, 88, 74, 0.5, 105, 80, 95, 50, 80, 87, 71, 50, 95, 0, 80, 75, 50, 70, 80, 100, 65, 80, 100, 50, 68, 60, 90, 67, 50, 60]

    prog30 = [71, 90, 80, 75, 100, 0, 90, 102, 84, 78, 105, 77, 73, 78, 0, 99, 80, 66, 46, 83, 40, 83,
              80, 90, 93, 50, 96, 88, 99, 108, 75, 80, 50, 64, 55, 100, 100, 110, 80, 50, 74, 90, 80, 80, 56, 80, 100, 55, 65, 59, 90, 50, 90, 90]

    overdrive30 = [71, 90, 57, 75, 80, 0, 95, 79, 65, 31, 50, 69, 100, 68, 0, 78, 50, 70, 62, 49, 64,
                   56, 73, 95, 67, 84, 80, 88, 79, 80, 50, 80, 80, 63, 25, 50, 82, 55, 50, 95, 55, 70, 100, 80, 99, 80, 100, 40, 69, 62, 51, 90, 67, 60]

    char_type = [1, 0, 0, 0, 0, 0, 0, 2, 0, 1, 2, 0, 0, 0, 2, 3, 1, 0, 0, 0, 1,
                 0, 0, 0, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 2, 2, 2, 0, 0, 0, 2, 2, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    char_core = {
        0: [{'core_id': 'core_hollow', 'amount': 25}, {'core_id': 'core_desolate', 'amount': 5}],
        1: [{'core_id': 'core_hollow', 'amount': 5}, {'core_id': 'core_desolate', 'amount': 25}],
        2: [{'core_id': 'core_hollow', 'amount': 5}, {'core_id': 'core_crimson', 'amount': 25}],
        4: [{'core_id': 'core_ambivalent', 'amount': 25}, {'core_id': 'core_desolate', 'amount': 5}],
        13: [{'core_id': 'core_scarlet', 'amount': 30}],
        21: [{'core_id': 'core_scarlet', 'amount': 30}],
        26: [{'core_id': 'core_chunithm', 'amount': 15}],
        27: [{'core_id': 'core_chunithm', 'amount': 15}],
        28: [{'core_id': 'core_chunithm', 'amount': 15}],
        29: [{'core_id': 'core_chunithm', 'amount': 15}],
        36: [{'core_id': 'core_chunithm', 'amount': 15}],
        42: [{'core_id': 'core_chunithm', 'amount': 15}],
        43: [{'core_id': 'core_chunithm', 'amount': 15}],
        11: [{'core_id': 'core_binary', 'amount': 25}, {'core_id': 'core_hollow', 'amount': 5}],
        12: [{'core_id': 'core_binary', 'amount': 25}, {'core_id': 'core_desolate', 'amount': 5}]
    }

    for i in range(0, 54):
        skill_requires_uncap = 1 if i == 2 else 0

        if i in [0, 1, 2, 4, 13, 26, 27, 28, 29, 36, 21, 42, 43, 11, 12]:
            sql = '''insert into character values(?,?,30,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)'''
            c.execute(sql, (i, char[i], frag1[i], prog1[i], overdrive1[i], frag20[i], prog20[i], overdrive20[i],
                            frag30[i], prog30[i], overdrive30[i], skill_id[i], skill_unlock_level[i], skill_requires_uncap, skill_id_uncap[i], char_type[i]))
        else:
            if i != 5 and i != 46:
                sql = '''insert into character values(?,?,20,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)'''
                c.execute(sql, (i, char[i], frag1[i], prog1[i], overdrive1[i], frag20[i], prog20[i], overdrive20[i],
                                frag30[i], prog30[i], overdrive30[i], skill_id[i], skill_unlock_level[i], skill_requires_uncap, skill_id_uncap[i], char_type[i]))

    c.execute('''insert into character values(?,?,20,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)''', (99,
                                                                                         'shirahime', 38, 33, 28, 66, 58, 50, 66, 58, 50, 'frags_preferred_song', 0, 0, '', 0))

    for i in char_core:
        for j in char_core[i]:
            c.execute('''insert into char_item values(?,?,'core',?)''',
                      (i, j['core_id'], j['amount']))
    cores = ['core_hollow', 'core_desolate', 'core_chunithm', 'core_crimson',
             'core_ambivalent', 'core_scarlet', 'core_groove', 'core_generic', 'core_binary']

    for i in cores:
        c.execute('''insert into item values(?,"core",1,'')''', (i,))

    world_songs = ["babaroque", "shadesoflight", "kanagawa", "lucifer", "anokumene", "ignotus", "rabbitintheblackroom", "qualia", "redandblue", "bookmaker", "darakunosono", "espebranch", "blacklotus", "givemeanightmare", "vividtheory", "onefr", "gekka", "vexaria3", "infinityheaven3", "fairytale3", "goodtek3", "suomi", "rugie", "faintlight", "harutopia", "goodtek", "dreaminattraction", "syro", "diode", "freefall", "grimheart", "blaster",
                   "cyberneciacatharsis", "monochromeprincess", "revixy", "vector", "supernova", "nhelv", "purgatorium3", "dement3", "crossover", "guardina", "axiumcrisis", "worldvanquisher", "sheriruth", "pragmatism", "gloryroad", "etherstrike", "corpssansorganes", "lostdesire", "blrink", "essenceoftwilight", "lapis", "solitarydream", "lumia3", "purpleverse", "moonheart3", "glow", "enchantedlove", "take", "lifeispiano", "vandalism", "nexttoyou3", "lostcivilization3", "turbocharger", "bookmaker3", "laqryma3", "kyogenkigo", "hivemind", "seclusion", "quonwacca3", "bluecomet", "energysynergymatrix", "gengaozo", "lastendconductor3", "antithese3", "qualia3", "kanagawa3", "heavensdoor3", "pragmatism3"]
    for i in world_songs:
        c.execute('''insert into item values(?,"world_song",1,'')''', (i,))

    world_unlocks = ["scenery_chap1", "scenery_chap2",
                     "scenery_chap3", "scenery_chap4", "scenery_chap5"]
    for i in world_unlocks:
        c.execute('''insert into item values(?,"world_unlock",1,'')''', (i,))

    c.execute('''insert into item values(?,?,?,?)''',
              ('fragment', 'fragment', 1, ''))
    c.execute('''insert into item values(?,?,?,?)''',
              ('memory', 'memory', 1, ''))

    def insert_items(c, items):
        # 物品数据导入
        for i in items:
            if 'discount_from' not in i:
                discount_from = -1
            else:
                discount_from = i['discount_from']
            if 'discount_to' not in i:
                discount_to = -1
            else:
                discount_to = i['discount_to']
            c.execute('''insert into purchase values(?,?,?,?,?)''',
                      (i['name'], i['price'], i['orig_price'], discount_from, discount_to))
            for j in i['items']:
                if "_id" not in j:
                    _id = ''
                else:
                    _id = j['_id']
                c.execute(
                    '''select exists(select * from item where item_id=?)''', (j['id'],))
                if c.fetchone() == (0,):
                    c.execute('''insert into item values(?,?,?,?)''',
                              (j['id'], j['type'], j['is_available'], _id))
                if 'amount' in j:
                    amount = j['amount']
                else:
                    amount = 1
                c.execute('''insert into purchase_item values(?,?,?,?)''',
                          (i['name'], j['id'], j['type'], amount))

    # item初始化
    f = open(path+'singles.json', 'r')
    singles = json.load(f)
    f.close()
    insert_items(c, singles)

    f = open(path+'packs.json', 'r')
    packs = json.load(f)
    f.close()
    insert_items(c, packs)

    # api权限与权限组初始化
    role = ['admin', 'user', 'selecter']
    role_caption = ['管理员', '用户', '查询接口']

    power = ['select', 'select_me', 'change', 'change_me', 'grant',
             'grant_inf', 'select_song_rank', 'select_song_info']
    power_caption = ['总体查询权限', '自我查询权限', '总体修改权限',
                     '自我修改权限', '授权权限', '下级授权权限', '歌曲排行榜查询权限', '歌曲信息查询权限']

    role_power = {'0': [0, 1, 3, 5, 6, 7],
                  '1': [1, 3, 6, 7],
                  '2': [0]
                  }

    for i in range(0, len(role)):
        c.execute('''insert into role values(:a,:b,:c)''', {
            'a': i, 'b': role[i], 'c': role_caption[i]})
    for i in range(0, len(power)):
        c.execute('''insert into power values(:a,:b,:c)''', {
            'a': i, 'b': power[i], 'c': power_caption[i]})
    for i in role_power:
        for j in role_power[i]:
            c.execute('''insert into role_power values(:a,:b)''',
                      {'a': int(i), 'b': j})

    conn.commit()
    conn.close()

    def arc_register(name: str):
        def build_user_code(c):
            return '123456789'

        def build_user_id(c):
            return 2000000

        def insert_user_char(c, user_id):
            # 为用户添加可用角色
            c.execute('''insert into user_char values(?,?,?,?,?,?)''',
                      (user_id, 0, 30, 25000, 1, 0))
            c.execute('''insert into user_char values(?,?,?,?,?,?)''',
                      (user_id, 1, 30, 25000, 1, 0))

            c.execute(
                '''select character_id, max_level, is_uncapped from character''')
            x = c.fetchall()
            if x:
                for i in x:
                    exp = 25000 if i[1] == 30 else 10000
                    c.execute('''insert into user_char_full values(?,?,?,?,?,?)''',
                              (user_id, i[0], i[1], exp, i[2], 0))

        conn = sqlite3.connect(path+'arcaea_database.db')
        c = conn.cursor()
        hash_pwd = '41e5653fc7aeb894026d6bb7b2db7f65902b454945fa8fd65a6327047b5277fb'
        c.execute(
            '''select exists(select * from user where name = :name)''', {'name': name})
        if c.fetchone() == (0,):
            user_code = build_user_code(c)
            user_id = build_user_id(c)
            now = int(time.time() * 1000)
            c.execute('''insert into user(user_id, name, password, join_date, user_code, rating_ptt,
            character_id, is_skill_sealed, is_char_uncapped, is_char_uncapped_override, is_hide_rating, favorite_character, max_stamina_notification_enabled, current_map, ticket)
            values(:user_id, :name, :password, :join_date, :user_code, 1250, 1, 0, 1, 0, 0, -1, 0, '', 114514)
            ''', {'user_code': user_code, 'user_id': user_id, 'join_date': now, 'name': name, 'password': hash_pwd})
            c.execute('''insert into recent30(user_id) values(:user_id)''', {
                'user_id': user_id})
            c.execute(
                '''insert into best_score values(2000000,'vexaria',3,10000000,100,0,0,0,100,0,1599667200,3,3,10.8)''')
            insert_user_char(c, user_id)
            conn.commit()
            conn.close()
            return None
        else:
            conn.commit()
            conn.close()
            return None

    arc_register('admin')


if __name__ == '__main__':
    main()
