import os
import hashlib
from flask import url_for


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


def get_one_song(song_id, file_dir='./database/songs'):
    # 获取一首歌的下载链接，返回字典
    dir_list = os.listdir(os.path.join(file_dir, song_id))
    re = {}
    for i in dir_list:
        if os.path.isfile(os.path.join(file_dir, song_id, i)) and i in ['0.aff', '1.aff', '2.aff', '3.aff', 'base.ogg']:
            if i == 'base.ogg':
                re['audio'] = {"checksum": get_file_md5(os.path.join(file_dir, song_id, 'base.ogg')),
                               "url": url_for('download', file_path=song_id+'/base.ogg', _external=True)}
            else:
                if 'chart' not in re:
                    re['chart'] = {}

                re['chart'][i[0]] = {"checksum": get_file_md5(os.path.join(file_dir, song_id, i)),
                                     "url": url_for('download', file_path=song_id+'/'+i, _external=True)}

    return {song_id: re}


def get_all_songs(file_dir='./database/songs'):
    # 获取所有歌的下载链接，返回字典
    dir_list = os.listdir(file_dir)
    re = {}
    for i in dir_list:
        if os.path.isdir(os.path.join(file_dir, i)):
            re.update(get_one_song(i))

    return re
