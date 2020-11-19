import sqlite3
import hashlib
import time

# 数据库初始化文件，删掉arcaea_database.db文件后运行即可，谨慎使用

conn = sqlite3.connect('arcaea_database.db')
c = conn.cursor()
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
ticket int
);''')
c.execute('''create table if not exists login(access_token text,
user_id int,
last_login_time int,
last_login_ip text,
last_login_device text
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
level_exp real,
frag real,
prog real,
overdrive real,
skill_id text,
skill_unlock_level int,
skill_requires_uncap int,
skill_id_uncap text,
char_type int,
is_uncapped int,
is_uncapped_override int,
primary key(user_id, character_id)
);''')
c.execute('''create table if not exists character(character_id int primary key,
name text,
level int,
exp real,
level_exp real,
frag real,
prog real,
overdrive real,
skill_id text,
skill_unlock_level int,
skill_requires_uncap int,
skill_id_uncap text,
char_type int,
uncap_cores text,
is_uncapped int,
is_uncapped_override int
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

char = ['Hikari','Tairitsu','Kou','Sapphire','Lethe','','Tairitsu(Axium)'
,'Tairitsu(Grievous Lady)','Stella','Hikari & Fisica','Ilith','Eto','Luna'
,'Shirabe','Hikari(Zero)','Hikari(Fracture)','Hikari(Summer)','Tairitsu(Summer)'
,'Tairitsu&Trin','Ayu','Eto&Luna','Yume','Seine & Hikari','Saya','Tairitsu & Chuni Penguin'
,'Chuni Penguin','Haruna','Nono','MTA-XXX','MDA-21','Kanae','Hikari(Fantasia)','Tairitsu(Sonata)','Sia','DORO*C'
,'Tairitsu(Tempest)','Brillante','Ilith(Summer)','Etude']

skill_id = ['gauge_easy','','','','note_mirror','','','gauge_hard','frag_plus_10_pack_stellights','gauge_easy|frag_plus_15_pst&prs'
            ,'gauge_hard|fail_frag_minus_100','frag_plus_5_side_light','visual_hide_hp','frag_plus_5_side_conflict'
            ,'challenge_fullcombo_0gauge','gauge_overflow','gauge_easy|note_mirror','note_mirror'
            ,'visual_tomato_pack_tonesphere','frag_rng_ayu','gaugestart_30|gaugegain_70','combo_100-frag_1'
            ,'audio_gcemptyhit_pack_groovecoaster','gauge_saya','gauge_chuni','kantandeshou'
            ,'gauge_haruna','frags_nono','gauge_pandora','gauge_regulus','omatsuri_daynight'
            ,'','','sometimes(note_mirror|frag_plus_5)','scoreclear_aa|visual_scoregauge','gauge_tempest'
            ,'gauge_hard','gauge_ilith_summer','']

skill_id_uncap = ['','','frags_kou','','visual_ink','','','','','','','','','shirabe_entry_fee','','','','','','','','frags_yume','','','','','','','','','','','','','','','','','']

for i in range(0, 39):
    if i in [0, 1, 2, 4, 13, 26, 27, 28, 29, 36, 21]:
        sql = 'insert into character values('+str(i)+',"'+char[i]+'''",30,25000,25000,90,90,90,"'''+skill_id[i]+'''",0,0,"'''+skill_id_uncap[i]+'''",0,'',1,1)'''
        c.execute(sql)
    else:
        if i != 5:
            sql = 'insert into character values('+str(i)+',"'+char[i]+'''",30,25000,25000,90,90,90,"'''+skill_id[i]+'''",0,0,"'''+skill_id_uncap[i]+'''",0,'',0,0)'''
            c.execute(sql)



conn.commit()
conn.close()



def arc_register(name: str, password: str): 
    def build_user_code(c):
        return '123456789'

    def build_user_id(c):
        return 2000000

##    def insert_user_char(c, user_id):
##        for i in range(0, 38):
##            if i in [0, 1, 2, 4, 13, 26, 27, 28, 29, 36, 21]:
##                sql = 'insert into user_char values('+str(user_id)+','+str(
##                    i)+''',30,25000,25000,90,90,90,'',0,0,'',0,1,1)'''
##                c.execute(sql)
##            else:
##                if i != 5:
##                    sql = 'insert into user_char values('+str(user_id)+','+str(
##                        i)+''',30,25000,25000,90,90,90,'',0,0,'',0,0,0)'''
##                    c.execute(sql)
    def insert_user_char(c, user_id):
        # 为用户添加所有可用角色
        c.execute('''select * from character''')
        x = c.fetchall()
        if x != []:
            for i in x:
                c.execute('''insert into user_char values(:a,:b,:c,:d,:e,:f,:g,:h,:i,:j,:k,:l,:m,:n,:o)''', {
                          'a': user_id, 'b': i[0], 'c': i[2], 'd': i[3], 'e': i[4], 'f': i[5], 'g': i[6], 'h': i[7], 'i': i[8], 'j': i[9], 'k': i[10], 'l': i[11], 'm': i[12], 'n': i[14], 'o': i[15]})

    
    conn = sqlite3.connect('arcaea_database.db')
    c = conn.cursor()
    hash_pwd = hashlib.sha256(password.encode("utf8")).hexdigest()
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
        c.execute('''insert into best_score values(2000000,'vexaria',3,10000000,100,0,0,0,100,0,1599667200,3,3,10.8)''')
        insert_user_char(c, user_id)
        conn.commit()
        conn.close()
        return None
    else:
        conn.commit()
        conn.close()
        return None


arc_register('admin', 'admin123')
