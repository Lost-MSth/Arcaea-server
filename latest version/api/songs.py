from core.error import ArcError, NoData
from core.song import Song
from core.sql import Connect, Query, Sql
from flask import Blueprint, request

from .api_auth import request_json_handle, role_required
from .api_code import error_return, success_return
from .constant import Constant

bp = Blueprint('songs', __name__, url_prefix='/songs')


@bp.route('/<string:song_id>', methods=['GET'])
@role_required(request, ['select', 'select_song_info'])
def songs_song_get(user, song_id):
    '''查询歌曲信息'''
    with Connect() as c:
        try:
            s = Song(c, song_id).select()
            return success_return(s.to_dict())
        except ArcError as e:
            return error_return(e)
    return error_return()


@bp.route('', methods=['GET'])
@role_required(request, ['select', 'select_song_info'])
@request_json_handle(request, optional_keys=Constant.QUERY_KEYS)
def songs_get(data, user):
    '''查询全歌曲信息'''
    A = ['song_id', 'name']
    B = ['song_id', 'name', 'rating_pst',
         'rating_prs', 'rating_ftr', 'rating_byn']
    with Connect() as c:
        try:
            query = Query(A, A, B).from_data(data)
            x = Sql(c).select('chart', query=query)
            r = []
            for i in x:
                r.append(Song(c).from_list(i))

            if not r:
                raise NoData(api_error_code=-2)

            return success_return([x.to_dict() for x in r])
        except ArcError as e:
            return error_return(e)
    return error_return()
