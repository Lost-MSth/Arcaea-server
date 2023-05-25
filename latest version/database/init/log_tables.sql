create table if not exists cache(key text primary key,
value text,
expire_time int
);
create table if not exists user_score(user_id int,
song_id text,
difficulty int,
time_played int,
score int,
shiny_perfect_count int,
perfect_count int,
near_count int,
miss_count int,
health int,
modifier int,
clear_type int,
rating real,
primary key(user_id, song_id, difficulty, time_played)
);
create table if not exists user_rating(user_id int,
time int,
rating_ptt real,
primary key(user_id, time)
);

create index if not exists user_score_1 on user_score (song_id, difficulty);
create index if not exists user_score_2 on user_score (time_played);

PRAGMA journal_mode = WAL;
PRAGMA default_cache_size = 4000;