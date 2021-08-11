from server.sql import Connect
from server.sql import Sql
import time


def get_song_info(song_id):
    # 查询指定歌曲信息，返回字典
    r = {}

    with Connect('./database/arcsong.db') as c:
        c.execute('''select * from songs where sid=:a''', {'a': song_id})
        x = c.fetchone()
        if x:
            r = {'song_id': x[0],
                 'name': {'name_en': x[1],
                          'name_jp': x[2]},
                 'pakset': x[5],
                 'artist': x[6],
                 'date': x[9],
                 'rating_pst': x[13]/10,
                 'rating_prs': x[14]/10,
                 'rating_ftr': x[15]/10,
                 'rating_byn': x[16]/10,
                 'difficultly_pst': x[17]/2,
                 'difficultly_prs': x[18]/2,
                 'difficultly_ftr': x[19]/2,
                 'difficultly_byn': x[20]/2
                 }

    return r


def get_songs(query=None):
    # 查询全部歌曲信息，返回字典列表
    r = []

    with Connect('./database/arcsong.db') as c:
        x = Sql.select(c, 'songs', [], query)

        if x:
            for i in x:
                r.append({'sid': i[0],
                          'name': {'name_en': i[1],
                                   'name_jp': i[2]},
                          'pakset': i[5],
                          'artist': i[6],
                          'date': i[9],
                          'rating_pst': i[13]/10,
                          'rating_prs': i[14]/10,
                          'rating_ftr': i[15]/10,
                          'rating_byn': i[16]/10,
                          'difficultly_pst': i[17]/2,
                          'difficultly_prs': i[18]/2,
                          'difficultly_ftr': i[19]/2,
                          'difficultly_byn': i[20]/2
                          })

    return r
