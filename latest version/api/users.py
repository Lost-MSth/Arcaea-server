from core.error import InputError, NoAccess, NoData
from core.score import Potential, UserScoreList
from core.sql import Connect, Query, Sql
from core.user import UserInfo, UserRegister
from flask import Blueprint, request

from .api_auth import api_try, request_json_handle, role_required
from .api_code import error_return, success_return
from .constant import Constant

bp = Blueprint('users', __name__, url_prefix='/users')


@bp.route('', methods=['POST'])
@role_required(request, ['change'])
@request_json_handle(request, ['name', 'password', 'email'])
@api_try
def users_post(data, _):
    '''注册一个用户'''
    with Connect() as c:
        new_user = UserRegister(c)
        new_user.set_name(data['name'])
        new_user.set_password(data['password'])
        new_user.set_email(data['email'])
        new_user.register()
        return success_return({'user_id': new_user.user_id, 'user_code': new_user.user_code})


@bp.route('', methods=['GET'])
@role_required(request, ['select'])
@request_json_handle(request, optional_keys=Constant.QUERY_KEYS)
@api_try
def users_get(data, user):
    '''查询全用户信息'''
    A = ['user_id', 'name', 'user_code']
    B = ['user_id', 'name', 'user_code', 'join_date',
         'rating_ptt', 'time_played', 'ticket', 'world_rank_score']
    with Connect() as c:
        query = Query(A, A, B).from_data(data)
        x = Sql(c).select('user', query=query)
        r = []
        for i in x:
            r.append(UserInfo(c).from_list(i))

        if not r:
            raise NoData(api_error_code=-2)

        return success_return([{
            'user_id': x.user_id,
            'name': x.name,
            'join_date': x.join_date,
            'user_code': x.user_code,
            'rating_ptt': x.rating_ptt/100,
            'character_id': x.character.character_id,
            'is_char_uncapped': x.character.is_uncapped,
            'is_char_uncapped_override': x.character.is_uncapped_override,
            'is_hide_rating': x.is_hide_rating,
            'ticket': x.ticket
        } for x in r])


@bp.route('/<int:user_id>', methods=['GET'])
@role_required(request, ['select', 'select_me'])
@api_try
def users_user_get(user, user_id):
    '''查询用户信息'''
    if user_id <= 0:
        return error_return(InputError(api_error_code=-4))
    # 查别人需要select权限
    if user_id != user.user_id and user.user_id != 0 and not user.role.has_power('select'):
        return error_return(NoAccess('No permission', api_error_code=-1), 403)

    with Connect() as c:
        u = UserInfo(c, user_id)
        return success_return(u.to_dict())


@bp.route('/<int:user_id>/b30', methods=['GET'])
@role_required(request, ['select', 'select_me'])
@api_try
def users_user_b30_get(user, user_id):
    '''查询用户b30'''
    if user_id <= 0:
        return error_return(InputError(api_error_code=-4))
    # 查别人需要select权限
    if user_id != user.user_id and user.user_id != 0 and not user.role.has_power('select'):
        return error_return(NoAccess('No permission', api_error_code=-1), 403)

    with Connect() as c:
        x = UserScoreList(c, UserInfo(c, user_id))
        x.query.limit = 30
        x.select_from_user()
        x.select_song_name()
        r = x.to_dict_list()
        rating_sum = sum([i.rating for i in x.scores])
        return success_return({'user_id': user_id, 'b30_ptt': rating_sum / 30, 'data': r})


@bp.route('/<int:user_id>/best', methods=['GET'])
@role_required(request, ['select', 'select_me'])
@request_json_handle(request, optional_keys=Constant.QUERY_KEYS)
@api_try
def users_user_best_get(data, user, user_id):
    '''查询用户所有best成绩'''
    if user_id <= 0:
        return error_return(InputError(api_error_code=-4))
    # 查别人需要select权限
    if user_id != user.user_id and user.user_id != 0 and not user.role.has_power('select'):
        return error_return(NoAccess('No permission', api_error_code=-1), 403)

    with Connect() as c:
        x = UserScoreList(c, UserInfo(c, user_id))
        x.query.from_data(data)
        x.select_from_user()
        r = x.to_dict_list()
        return success_return({'user_id': user_id, 'data': r})


@bp.route('/<int:user_id>/r30', methods=['GET'])
@role_required(request, ['select', 'select_me'])
@api_try
def users_user_r30_get(user, user_id):
    '''查询用户r30'''

    if user_id <= 0:
        return error_return(InputError(api_error_code=-4))
    # 查别人需要select权限
    if user_id != user.user_id and user.user_id != 0 and not user.role.has_power('select'):
        return error_return(NoAccess('No permission', api_error_code=-1), 403)

    with Connect() as c:
        p = Potential(c, UserInfo(c, user_id))
        return success_return({'user_id': user_id, 'r10_ptt': p.recent_10 / 10, 'data': p.recent_30_to_dict_list()})
