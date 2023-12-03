create table if not exists config(id text primary key, value text);
create table if not exists user(user_id int primary key,
name text unique,
password text,
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
stamina int,
world_mode_locked_end_ts int,
beyond_boost_gauge real default 0
);
create table if not exists login(access_token text,
user_id int,
login_time int,
login_ip text,
login_device text,
primary key(access_token, user_id)
);
create table if not exists friend(user_id_me int,
user_id_other int,
primary key (user_id_me, user_id_other)
);
create table if not exists best_score(user_id int,
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
);
create table if not exists user_char(user_id int,
character_id int,
level int,
exp real,
is_uncapped int,
is_uncapped_override int,
skill_flag int,
primary key(user_id, character_id)
);
create table if not exists user_char_full(user_id int,
character_id int,
level int,
exp real,
is_uncapped int,
is_uncapped_override int,
skill_flag int,
primary key(user_id, character_id)
);
create table if not exists character(character_id int primary key,
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
);
create table if not exists char_item(character_id int,
item_id text,
type text,
amount int,
primary key(character_id, item_id, type)
);
create table if not exists recent30(user_id int primary key,
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
);
create table if not exists user_world(user_id int,
map_id text,
curr_position int,
curr_capture real,
is_locked int,
primary key(user_id, map_id)
);
create table if not exists songplay_token(token text primary key,
user_id int,
song_id text,
difficulty int,
course_id text,
course_state int,
course_score int,
course_clear_type int,
stamina_multiply int,
fragment_multiply int,
prog_boost_multiply int,
beyond_boost_gauge_usage int,
skill_cytusii_flag text
);
create table if not exists item(item_id text,
type text,
is_available int,
primary key(item_id, type)
);
create table if not exists user_item(user_id int,
item_id text,
type text,
amount int,
primary key(user_id, item_id, type)
);
create table if not exists purchase(purchase_name text primary key,
price int,
orig_price int,
discount_from int,
discount_to int,
discount_reason text
);
create table if not exists purchase_item(purchase_name text,
item_id text,
type text,
amount int,
primary key(purchase_name, item_id, type)
);
create table if not exists user_save(user_id int primary key,
scores_data text,
clearlamps_data text,
clearedsongs_data text,
unlocklist_data text,
installid_data text,
devicemodelname_data text,
story_data text,
createdAt int,
finalestate_data text
);
create table if not exists present(present_id text primary key,
expire_ts int,
description text
);
create table if not exists user_present(user_id int,
present_id text,
primary key(user_id, present_id)
);
create table if not exists present_item(present_id text,
item_id text,
type text,
amount int,
primary key(present_id, item_id, type)
);
create table if not exists chart(song_id text primary key,
name text,
rating_pst int,
rating_prs int,
rating_ftr int,
rating_byn int
);
create table if not exists redeem(code text primary key,
type int
);
create table if not exists user_redeem(user_id int,
code text,
primary key(user_id, code)
);
create table if not exists redeem_item(code text,
item_id text,
type text,
amount int,
primary key(code, item_id, type)
);

create table if not exists role(role_id text primary key,
caption text
);
create table if not exists user_role(user_id int,
role_id text,
primary key(user_id, role_id)
);
create table if not exists power(power_id text primary key,
caption text
);
create table if not exists role_power(role_id text,
power_id text,
primary key(role_id, power_id)
);
create table if not exists api_login(user_id int,
token text,
login_time int,
login_ip text,
primary key(user_id, token)
);
create table if not exists course(course_id text primary key,
course_name text,
dan_name text,
style int,
gauge_requirement text,
flag_as_hidden_when_requirements_not_met int,
can_start int
);
create table if not exists user_course(user_id int,
course_id text,
high_score int,
best_clear_type int,
primary key(user_id, course_id)
);
create table if not exists course_chart(course_id text,
song_id text,
difficulty int,
flag_as_hidden int,
song_index int,
primary key(course_id, song_index)
);
create table if not exists course_requirement(course_id text,
required_id text,
primary key(course_id, required_id)
);
create table if not exists course_item(course_id text,
item_id text,
type text,
amount int,
primary key(course_id, item_id, type)
);

create index if not exists best_score_1 on best_score (song_id, difficulty);

PRAGMA journal_mode = WAL;
PRAGMA default_cache_size = 8000;