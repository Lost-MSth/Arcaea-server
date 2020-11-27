import os
import hashlib
from flask import url_for
import sqlite3
import time

time_limit = 3000  # 每个玩家24小时下载次数限制
time_gap_limit = 1000  # 下载链接有效秒数


def get_file_md5(file_path):
    # 计算文件MD5
    if not os.path.isfile(file_path):
        return None
    myhash = hashlib.md5()
    f = open(file_path, 'rb')
    while True:
        b = f.read(8096)
        if not b:
            break
        myhash.update(b)
    f.close()
    return myhash.hexdigest()


def get_one_song(c, user_id, song_id, file_dir='./database/songs'):
    # 获取一首歌的下载链接，返回字典
    dir_list = os.listdir(os.path.join(file_dir, song_id))
    re = {}
    now = int(time.time())
    c.execute('''delete from download_token where user_id=:a and song_id=:b''', {
        'a': user_id, 'b': song_id})

    for i in dir_list:
        if os.path.isfile(os.path.join(file_dir, song_id, i)) and i in ['0.aff', '1.aff', '2.aff', '3.aff', 'base.ogg']:
            token = hashlib.md5(
                (str(user_id) + song_id + i + str(now)).encode(encoding='UTF-8')).hexdigest()
            token = token[:8]

            if i == 'base.ogg':
                re['audio'] = {"checksum": get_file_md5(os.path.join(file_dir, song_id, 'base.ogg')),
                               "url": url_for('download', file_path=song_id+'/base.ogg', t=token, _external=True)}
            else:
                if 'chart' not in re:
                    re['chart'] = {}
                re['chart'][i[0]] = {"checksum": get_file_md5(os.path.join(file_dir, song_id, i)),
                                     "url": url_for('download', file_path=song_id+'/'+i, t=token, _external=True)}

            c.execute('''insert into download_token values(:a,:b,:c,:d,:e)''', {
                'a': user_id, 'b': song_id, 'c': i, 'd': token, 'e': now})

    return {song_id: re}


def get_all_songs(user_id, file_dir='./database/songs'):
    # 获取所有歌的下载链接，返回字典
    dir_list = os.listdir(file_dir)
    re = {}
    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    for i in dir_list:
        if os.path.isdir(os.path.join(file_dir, i)):
            re.update(get_one_song(c, user_id, i))

    conn.commit()
    conn.close()
    return re


def get_some_songs(user_id, song_ids):
    # 获取一些歌的下载链接，返回字典
    re = {}
    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    for song_id in song_ids:
        re.update(get_one_song(c, user_id, song_id))

    conn.commit()
    conn.close()
    return re


def is_token_able_download(t):
    # token是否可以下载，返回错误码，0即可以
    errorcode = 0
    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    c.execute('''select * from download_token where token = :t limit 1''',
              {'t': t})
    x = c.fetchone()
    now = int(time.time())
    if x and now - x[4] <= time_gap_limit:
        c.execute(
            '''select count(*) from user_download where user_id = :a''', {'a': x[0]})
        y = c.fetchone()
        if y and y[0] <= time_limit:
            c.execute('''insert into user_download values(:a,:b,:c)''', {
                      'a': x[0], 'b': x[3], 'c': now})
        else:
            errorcode = 903
    else:
        errorcode = 108

    conn.commit()
    conn.close()
    return errorcode


def is_able_download(user_id):
    # 是否可以下载，返回布尔值
    f = True
    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    now = int(time.time())
    c.execute(
        '''delete from user_download where user_id = :a and time <= :b''', {'a': user_id, 'b': now - 24*3600})
    c.execute(
        '''select count(*) from user_download where user_id = :a''', {'a': user_id})
    y = c.fetchone()
    if y and y[0] <= time_limit:
        pass
    else:
        f = False

    conn.commit()
    conn.close()
    return f
