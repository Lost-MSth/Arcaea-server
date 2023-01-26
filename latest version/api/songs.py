from flask import Blueprint, request

from core.error import DataExist, InputError, NoData
from core.rank import RankList
from core.song import Song
from core.sql import Connect, Query, Sql

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


@bp.route('/<string:song_id>', methods=['PUT'])
@role_required(request, ['change'])
@request_json_handle(request, optional_keys=['name', 'charts'], must_change=True)
@api_try
def songs_song_put(data, user, song_id):
    '''修改歌曲信息'''
    with Connect() as c:
        s = Song(c, song_id).select()
        if 'name' in data:
            s.name = str(data['name'])
        if 'charts' in data:
            for i in data['charts']:
                if 'difficulty' in i and 'chart_const' in i:
                    s.charts[i['difficulty']].defnum = round(
                        i['chart_const'] * 10)

        s.update()
        return success_return(s.to_dict())


@bp.route('/<string:song_id>', methods=['DELETE'])
@role_required(request, ['change'])
@api_try
def songs_song_delete(user, song_id):
    '''删除歌曲信息'''
    with Connect() as c:
        s = Song(c, song_id)
        if not s.select_exists():
            raise NoData(f'No such song: `{song_id}`')
        s.delete()
        return success_return()


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


@bp.route('', methods=['POST'])
@role_required(request, ['change'])
@request_json_handle(request, ['song_id', 'charts'], ['name'])
@api_try
def songs_post(data, user):
    '''添加歌曲信息'''
    with Connect() as c:
        s = Song(c).from_dict(data)
        if s.select_exists():
            raise DataExist(f'Song `{s.song_id}` already exists')
        s.insert()
        return success_return(s.to_dict())


@bp.route('/<string:song_id>/<int:difficulty>/rank', methods=['GET'])
@role_required(request, ['select', 'select_song_rank', 'select_song_rank_top'])
@request_json_handle(request, optional_keys=['limit'])
@api_try
def songs_song_difficulty_rank_get(data, user, song_id, difficulty):
    '''查询歌曲某个难度的成绩排行榜，和游戏内接口相似，只允许limit'''
    if difficulty not in [0, 1, 2, 3]:
        raise InputError('Difficulty must be 0, 1, 2 or 3')
    limit = data.get('limit', 20)
    if not isinstance(limit, int):
        raise InputError('Limit must be int')
    if user.role.only_has_powers(['select_song_rank_top'], ['select', 'select_song_rank']):
        # 限制低权限只能查询前20名
        if limit > 20 or limit < 0:
            limit = 20
    with Connect() as c:
        rank_list = RankList(c)
        rank_list.song.set_chart(song_id, difficulty)
        rank_list.limit = limit
        # 不检查歌曲是否存在，不存在返回的是空列表
        rank_list.select_top()
        return success_return(rank_list.to_dict_list())
