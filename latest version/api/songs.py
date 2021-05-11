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
                 'rating_pst': x[12]/10,
                 'rating_prs': x[13]/10,
                 'rating_ftr': x[14]/10,
                 'rating_byn': x[15]/10,
                 'difficultly_pst': x[16]/2,
                 'difficultly_prs': x[17]/2,
                 'difficultly_ftr': x[18]/2,
                 'difficultly_byn': x[19]/2
                 }

    return r


def get_songs(limit=-1, offset=0, query={}, sort=[]):
    # 查询全部歌曲信息，返回字典列表
    r = []

    with Connect('./database/arcsong.db') as c:
        x = Sql.select(c, 'songs', [], limit, offset, query, sort)

        if x:
            for i in x:
                r.append({'sid': i[0],
                          'name': {'name_en': i[1],
                                   'name_jp': i[2]},
                          'pakset': i[5],
                          'artist': i[6],
                          'date': i[9],
                          'rating_pst': i[12]/10,
                          'rating_prs': i[13]/10,
                          'rating_ftr': i[14]/10,
                          'rating_byn': i[15]/10,
                          'difficultly_pst': i[16]/2,
                          'difficultly_prs': i[17]/2,
                          'difficultly_ftr': i[18]/2,
                          'difficultly_byn': i[19]/2
                          })

    return r
