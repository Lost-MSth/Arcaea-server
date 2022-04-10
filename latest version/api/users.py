from flask import (
    Blueprint, request, jsonify
)

from .api_code import code_get_msg, return_encode
from .api_auth import role_required
from core.user import RegisterUser
from core.error import ArcError, PostError
from server.sql import Connect
from server.sql import Sql
import time
import web.webscore
import server.info

bp = Blueprint('users', __name__, url_prefix='/users')


@bp.route('', methods=['POST'])
@role_required(request, ['change'])
def users_post(user):
    # 注册用户
    with Connect() as c:
        new_user = RegisterUser(c)
        try:
            if 'name' in request.json:
                new_user.set_name(request.json['name'])
            else:
                raise PostError('No name provided.')

            if 'password' in request.json:
                new_user.set_password(request.json['password'])
            else:
                raise PostError('No password provided.')

            if 'email' in request.json:
                new_user.set_email(request.json['email'])
            else:
                raise PostError('No email provided.')

            new_user.register()
        except ArcError as e:
            return return_encode(e.api_error_code)

    return return_encode(0, {'user_id': new_user.user_id, 'user_code': new_user.user_code})


def get_users(query=None):
    # 获取全用户信息，返回字典列表

    r = []
    with Connect() as c:
        x = Sql.select(c, 'user', [], query)

        if x:
            for i in x:
                if i[23] != -1:
                    character_id = i[23]
                else:
                    character_id = i[6]
                r.append({
                    'user_id': i[0],
                    'name': i[1],
                    'join_date': i[3],
                    'user_code': i[4],
                    'rating_ptt': i[5]/100,
                    'character_id': character_id,
                    'is_char_uncapped': i[8] == 1,
                    'is_char_uncapped_override': i[9] == 1,
                    'is_hide_rating': i[10],
                    'ticket': i[26]
                })

    return r


def get_user_info(user_id):
    # 获取用户信息，返回字典，其实就是调用user/me信息

    r = {}
    with Connect() as c:
        r = server.info.get_user_me(c, user_id)

    return r


def get_user_b30(user_id):
    # 获取用户b30信息，返回字典

    r = []
    with Connect() as c:
        r = web.webscore.get_user_score(c, user_id, 30)

    bestptt = 0
    for i in r:
        if i['rating']:
            bestptt += i['rating']
        if 'time_played' in i:
            i['time_played'] = int(time.mktime(time.strptime(
                i['time_played'], '%Y-%m-%d %H:%M:%S')))

    return {'user_id': user_id, 'b30_ptt': bestptt / 30, 'data': r}


def get_user_best(user_id, query=None):
    # 获取用户b30信息，返回字典

    r = []
    with Connect() as c:
        x = Sql.select(c, 'best_score', [], query)
        if x:
            for i in x:
                r.append({
                    "song_id": i[1],
                    "difficulty": i[2],
                    "score": i[3],
                    "shiny_perfect_count": i[4],
                    "perfect_count": i[5],
                    "near_count": i[6],
                    "miss_count": i[7],
                    "health": i[8],
                    "modifier": i[9],
                    "time_played": i[10],
                    "best_clear_type": i[11],
                    "clear_type": i[12],
                    "rating": i[13]
                })

    return {'user_id': user_id, 'data': r}


def get_user_r30(user_id):
    # 获取用户r30信息，返回字典

    r = []
    with Connect() as c:
        r, r10_ptt = web.webscore.get_user_recent30(c, user_id)

    return {'user_id': user_id, 'r10_ptt': r10_ptt, 'data': r}
