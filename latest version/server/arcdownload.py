import os
import hashlib
from flask import url_for
import sqlite3
from server.sql import Connect
import time
from setting import Config

time_limit = Config.DOWNLOAD_TIMES_LIMIT  # 每个玩家24小时下载次数限制
time_gap_limit = Config.DOWNLOAD_TIME_GAP_LIMIT  # 下载链接有效秒数


def get_file_md5(file_path):
    # 计算文件MD5
    if not os.path.isfile(file_path):
        return None
    myhash = hashlib.md5()
    with open(file_path, 'rb') as f:
        while True:
            b = f.read(8096)
            if not b:
                break
            myhash.update(b)

    return myhash.hexdigest()


def get_url(file_path, **kwargs):
    # 获取下载地址

    t = ''
    if 't' in kwargs:
        t = kwargs['t']

    if Config.DOWNLOAD_LINK_PREFIX:
        prefix = Config.DOWNLOAD_LINK_PREFIX
        if prefix[-1] != '/':
            prefix += '/'

        return prefix + file_path + '?t=' + t
    else:
        return url_for('download', file_path=file_path, t=t, _external=True)


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

            if i == 'base.ogg':
                c.execute(
                    '''select md5 from songfile where song_id=:a and file_type=-1''', {'a': song_id})
                x = c.fetchone()
                if x:
                    checksum = x[0]
                else:
                    checksum = get_file_md5(os.path.join(
                        file_dir, song_id, 'base.ogg'))
                re['audio'] = {"checksum": checksum, "url": get_url(
                    file_path=song_id+'/base.ogg', t=token)}
            else:
                if 'chart' not in re:
                    re['chart'] = {}
                c.execute(
                    '''select md5 from songfile where song_id=:a and file_type=:b''', {'a': song_id, 'b': int(i[0])})
                x = c.fetchone()
                if x:
                    checksum = x[0]
                else:
                    checksum = get_file_md5(os.path.join(file_dir, song_id, i))
                re['chart'][i[0]] = {"checksum": checksum, "url": get_url(
                    file_path=song_id+'/'+i, t=token)}

            c.execute('''insert into download_token values(:a,:b,:c,:d,:e)''', {
                'a': user_id, 'b': song_id, 'c': i, 'd': token, 'e': now})

    return {song_id: re}


def get_all_songs(user_id, file_dir='./database/songs'):
    # 获取所有歌的下载链接，返回字典
    dir_list = os.listdir(file_dir)
    re = {}
    with Connect() as c:
        for i in dir_list:
            if os.path.isdir(os.path.join(file_dir, i)):
                re.update(get_one_song(c, user_id, i, file_dir))

    return re


def get_some_songs(user_id, song_ids):
    # 获取一些歌的下载链接，返回字典
    re = {}
    with Connect() as c:
        for song_id in song_ids:
            re.update(get_one_song(c, user_id, song_id))

    return re


def is_token_able_download(t):
    # token是否可以下载，返回错误码，0即可以
    errorcode = 108
    with Connect() as c:
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
                errorcode = 0
            else:
                errorcode = 903
        else:
            errorcode = 108

    return errorcode


def is_able_download(user_id):
    # 是否可以下载，返回布尔值
    f = False
    with Connect() as c:
        now = int(time.time())
        c.execute(
            '''delete from user_download where user_id = :a and time <= :b''', {'a': user_id, 'b': now - 24*3600})
        c.execute(
            '''select count(*) from user_download where user_id = :a''', {'a': user_id})
        y = c.fetchone()
        if y and y[0] <= time_limit:
            f = True
        else:
            f = False

    return f


def initialize_one_songfile(c, song_id, file_dir='./database/songs'):
    # 计算并添加歌曲md5到表中，无返回
    dir_list = os.listdir(os.path.join(file_dir, song_id))
    for i in dir_list:
        if os.path.isfile(os.path.join(file_dir, song_id, i)) and i in ['0.aff', '1.aff', '2.aff', '3.aff', 'base.ogg']:
            if i == 'base.ogg':
                c.execute('''insert into songfile values(:a,-1,:c)''', {
                          'a': song_id, 'c': get_file_md5(os.path.join(file_dir, song_id, 'base.ogg'))})
            else:
                c.execute('''insert into songfile values(:a,:b,:c)''', {
                          'a': song_id, 'b': int(i[0]), 'c': get_file_md5(os.path.join(file_dir, song_id, i))})

    return


def initialize_songfile(file_dir='./database/songs'):
    # 初始化歌曲数据的md5表，返回错误信息
    error = None
    try:
        dir_list = os.listdir(file_dir)
    except:
        error = 'OS error!'
        return error
    try:
        conn = sqlite3.connect('./database/arcaea_database.db')
        c = conn.cursor()
    except:
        error = 'Database error!'
        return error
    try:
        c.execute('''delete from songfile''')
        for i in dir_list:
            if os.path.isdir(os.path.join(file_dir, i)):
                initialize_one_songfile(c, i, file_dir)
    except:
        error = 'Initialization error!'
    finally:
        conn.commit()
        conn.close()
        return error
