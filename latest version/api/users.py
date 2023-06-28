from flask import Blueprint, request

from core.api_user import APIUser
from core.config_manager import Config
from core.error import InputError, NoAccess, NoData
from core.score import Potential, UserScoreList
from core.sql import Connect, Query, Sql
from core.user import UserChanger, UserInfo, UserRegister
from core.util import get_today_timestamp

from .api_auth import api_try, request_json_handle, role_required
from .api_code import error_return, success_return
from .constant import Constant

bp = Blueprint('users', __name__, url_prefix='/users')


@bp.route('', methods=['POST'])
@role_required(request, ['change'])
@request_json_handle(request, ['name', 'password', 'email'])
@api_try
def users_post(data, user):
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
        query = Query(A, A, B).from_dict(data)
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
            'rating_ptt': x.rating_ptt,
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
        return error_return(InputError(api_error_code=-110))
    # 查别人需要select权限
    if user_id != user.user_id and not user.role.has_power('select'):
        return error_return(NoAccess('No permission', api_error_code=-1), 403)

    with Connect() as c:
        u = UserInfo(c, user_id)
        return success_return(u.to_dict())


@bp.route('/<int:user_id>', methods=['PUT'])
@role_required(request, ['change'])
@request_json_handle(request, optional_keys=['name', 'password', 'user_code', 'ticket', 'email'], must_change=True)
@api_try
def users_user_put(data, user, user_id):
    '''修改一个用户'''
    with Connect() as c:
        u = UserChanger(c, user_id)
        r = {}
        r['user_id'] = user_id
        if 'name' in data:
            u.set_name(data['name'])
            r['name'] = u.name
        if 'password' in data:
            if data['password'] == '':
                u.password = ''
                r['password'] = ''
            else:
                u.set_password(data['password'])
                r['password'] = u.hash_pwd
        if 'email' in data:
            u.set_email(data['email'])
            r['email'] = u.email
        if 'user_code' in data:
            u.set_user_code(data['user_code'])
            r['user_code'] = u.user_code
        if 'ticket' in data:
            if not isinstance(data['ticket'], int):
                raise InputError('Ticket must be int')
            u.ticket = data['ticket']
            r['ticket'] = u.ticket
        u.update_columns(d=r)
        return success_return(r)


@bp.route('/<int:user_id>/b30', methods=['GET'])
@role_required(request, ['select', 'select_me'])
@api_try
def users_user_b30_get(user, user_id):
    '''查询用户b30'''
    if user_id <= 0:
        return error_return(InputError(api_error_code=-110))
    # 查别人需要select权限
    if user_id != user.user_id and not user.role.has_power('select'):
        return error_return(NoAccess('No permission', api_error_code=-1), 403)

    with Connect() as c:
        x = UserScoreList(c, UserInfo(c, user_id))
        x.query.limit = 30
        x.select_from_user()
        if not x.scores:
            raise NoData(
                f'No best30 data of user `{user_id}`', api_error_code=-3)
        x.select_song_name()
        r = x.to_dict_list()
        rating_sum = sum(i.rating for i in x.scores)
        return success_return({'user_id': user_id, 'b30_ptt': rating_sum / 30, 'data': r})


@bp.route('/<int:user_id>/best', methods=['GET'])
@role_required(request, ['select', 'select_me'])
@request_json_handle(request, optional_keys=Constant.QUERY_KEYS)
@api_try
def users_user_best_get(data, user, user_id):
    '''查询用户所有best成绩'''
    if user_id <= 0:
        return error_return(InputError(api_error_code=-110))
    # 查别人需要select权限
    if user_id != user.user_id and not user.role.has_power('select'):
        return error_return(NoAccess('No permission', api_error_code=-1), 403)

    with Connect() as c:
        x = UserScoreList(c, UserInfo(c, user_id))
        x.query.from_dict(data)
        x.select_from_user()
        if not x.scores:
            raise NoData(
                f'No best score data of user `{user_id}`', api_error_code=-3)
        r = x.to_dict_list()
        return success_return({'user_id': user_id, 'data': r})


@bp.route('/<int:user_id>/r30', methods=['GET'])
@role_required(request, ['select', 'select_me'])
@api_try
def users_user_r30_get(user, user_id):
    '''查询用户r30'''

    if user_id <= 0:
        return error_return(InputError(api_error_code=-110))
    # 查别人需要select权限
    if user_id != user.user_id and not user.role.has_power('select'):
        return error_return(NoAccess('No permission', api_error_code=-1), 403)

    with Connect() as c:
        p = Potential(c, UserInfo(c, user_id))
        return success_return({'user_id': user_id, 'r10_ptt': p.recent_10 / 10, 'data': p.recent_30_to_dict_list()})


@bp.route('/<int:user_id>/role', methods=['GET'])
@role_required(request, ['select', 'select_me'])
@api_try
def users_user_role_get(user, user_id):
    '''查询用户role和powers'''

    if user_id <= 0:
        return error_return(InputError(api_error_code=-110))

    if user_id == user.user_id:
        return success_return({'user_id': user.user_id, 'role': user.role.role_id, 'powers': [i.power_id for i in user.role.powers]})
    # 查别人需要select权限
    if not user.role.has_power('select'):
        return error_return(NoAccess('No permission', api_error_code=-1), 403)

    with Connect() as c:
        x = APIUser(c, user_id)
        x.select_role_and_powers()
        return success_return({'user_id': x.user_id, 'role': x.role.role_id, 'powers': [i.power_id for i in x.role.powers]})


@bp.route('/<int:user_id>/rating', methods=['GET'])
@role_required(request, ['select', 'select_me'])
@request_json_handle(request, optional_keys=['start_timestamp', 'end_timestamp', 'duration'])
@api_try
def users_user_rating_get(data, user, user_id):
    '''查询用户历史rating，`duration`是相对于今天的天数'''
    # 查别人需要select权限
    if user_id != user.user_id and not user.role.has_power('select'):
        return error_return(NoAccess('No permission', api_error_code=-1), 403)

    start_timestamp = data.get('start_timestamp', None)
    end_timestamp = data.get('end_timestamp', None)
    duration = data.get('duration', None)
    sql = '''select time, rating_ptt from user_rating where user_id = ?'''
    sql_data = [user_id]
    if start_timestamp is not None and end_timestamp is not None:
        sql += ''' and time between ? and ?'''
        sql_data += [start_timestamp, end_timestamp]
    elif duration is not None:
        sql += ''' and time between ? and ?'''
        t = get_today_timestamp()
        sql_data += [t - duration * 24 * 3600, t]

    with Connect(Config.SQLITE_LOG_DATABASE_PATH) as c:
        c.execute(sql, sql_data)
        r = c.fetchall()
        return success_return({'user_id': user_id, 'data': [{'time': i[0], 'rating_ptt': i[1]} for i in r]})
