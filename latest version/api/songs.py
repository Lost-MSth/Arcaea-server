from core.error import NoData
from core.song import Song
from core.sql import Connect, Query, Sql
from flask import Blueprint, request

from .api_auth import api_try, request_json_handle, role_required
from .api_code import success_return
from .constant import Constant

bp = Blueprint('songs', __name__, url_prefix='/songs')


@bp.route('/<string:song_id>', methods=['GET'])
@role_required(request, ['select', 'select_song_info'])
@api_try
def songs_song_get(user, song_id):
    '''查询歌曲信息'''
    with Connect() as c:
        s = Song(c, song_id).select()
        return success_return(s.to_dict())


@bp.route('', methods=['GET'])
@role_required(request, ['select', 'select_song_info'])
@request_json_handle(request, optional_keys=Constant.QUERY_KEYS)
@api_try
def songs_get(data, user):
    '''查询全歌曲信息'''
    A = ['song_id', 'name']
    B = ['song_id', 'name', 'rating_pst',
         'rating_prs', 'rating_ftr', 'rating_byn']
    with Connect() as c:
        query = Query(A, A, B).from_dict(data)
        x = Sql(c).select('chart', query=query)
        r = []
        for i in x:
            r.append(Song(c).from_list(i))

        if not r:
            raise NoData(api_error_code=-2)

        return success_return([x.to_dict() for x in r])
