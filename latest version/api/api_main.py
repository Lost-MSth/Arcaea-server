from flask import (
    Blueprint, request, jsonify
)
import api.api_auth
import api.users
import api.songs
from api.api_code import code_get_msg


bp = Blueprint('api', __name__, url_prefix='/api/v1')


def get_query_parameter(request, query_able=[], sort_able=[]):
    # 提取查询请求参数，返回四个参数和code

    limit = -1
    offset = 0
    query = {}  # {'name': 'admin'}
    sort = []  # [{'column': 'user_id', 'order': 'ASC'}, ...]

    if 'limit' in request.json:
        try:
            limit = int(request.json['limit'])
        except:
            return -1, 0, {}, {}, -101
    if 'offset' in request.json:
        try:
            offset = int(request.json['offset'])
        except:
            return -1, 0, {}, {}, -101
    if 'query' in request.json:
        query = request.json['query']
        for i in query:
            if i not in query_able:
                return -1, 0, {}, {}, -102
    if 'sort' in request.json:
        sort = request.json['sort']
        for i in sort:
            if 'column' not in i or i['column'] not in sort_able:
                return -1, 0, {}, {}, -103
            if not 'order' in i:
                i['order'] = 'ASC'
            else:
                if i['order'] not in ['ASC', 'DESC']:
                    return -1, 0, {}, {}, -104

    return limit, offset, query, sort, 0


@bp.route('/')
def ping():
    return jsonify({'status': 200, 'code': 0, 'data': {}, 'msg': ''})


@bp.route('/token', methods=['POST'])
def token_post():
    # 登录，获取token

    if 'auth' in request.json:
        data, code = api.api_auth.login(
            request.json['auth'], request.remote_addr)
        if code < 0:
            return jsonify({'status': 200, 'code': code, 'data': {}, 'msg': code_get_msg(code)})
        else:
            return jsonify({'status': 200, 'code': 0, 'data': data, 'msg': ''})
    else:
        return jsonify({'status': 401, 'code': -1, 'data': {}, 'msg': 'No authentication'})


@bp.route('/token', methods=['GET'])
@api.api_auth.role_required(request, ['select_me', 'select'])
def token_get(user):
    # 判断登录有效性
    return jsonify({'status': 200, 'code': 0, 'data': {}, 'msg': ''})


@bp.route('/token', methods=['DELETE'])
@api.api_auth.role_required(request, ['change_me', 'select_me', 'select'])
def token_delete(user):
    # 登出
    return jsonify({'status': 200, 'code': 0, 'data': {}, 'msg': ''})


@bp.route('/users', methods=['GET'])
@api.api_auth.role_required(request, ['select'])
def users_get(user):
    # 查询全用户信息

    limit, offset, query, sort, code = get_query_parameter(request, ['user_id', 'name', 'user_code'], [
        'user_id', 'name', 'user_code', 'join_date', 'rating_ptt', 'time_played', 'ticket'])
    if code < 0:
        return jsonify({'status': 200, 'code': code, 'data': {}, 'msg': code_get_msg(code)})

    data = api.users.get_users(limit, offset, query, sort)

    if not data:
        return jsonify({'status': 200, 'code': -2, 'data': {}, 'msg': code_get_msg(-2)})

    return jsonify({'status': 200, 'code': 0, 'data': data, 'msg': ''})


@bp.route('/users/<int:user_id>', methods=['GET'])
@api.api_auth.role_required(request, ['select', 'select_me'])
def users_user_get(user, user_id):
    # 查询用户信息

    if user_id == 'me':
        user_id = user.user_id

    if user_id <= 0:
        return jsonify({'status': 200, 'code': -4, 'data': {}, 'msg': code_get_msg(-4)})

    if user_id != user.user_id and not 'select' in user.power and user.user_id != 0:  # 查别人需要select权限
        return jsonify({'status': 403, 'code': -1, 'data': {}, 'msg': 'No permission'})

    data = api.users.get_user_info(user_id)

    if not data:
        return jsonify({'status': 200, 'code': -3, 'data': {}, 'msg': code_get_msg(-3)})

    return jsonify({'status': 200, 'code': 0, 'data': data, 'msg': ''})


@bp.route('/users/<int:user_id>/b30', methods=['GET'])
@api.api_auth.role_required(request, ['select', 'select_me'])
def users_user_b30_get(user, user_id):
    # 查询用户b30

    if user_id == 'me':
        user_id = user.user_id

    if user_id <= 0:
        return jsonify({'status': 200, 'code': -4, 'data': {}, 'msg': code_get_msg(-4)})

    if user_id != user.user_id and not 'select' in user.power and user.user_id != 0:  # 查别人需要select权限
        return jsonify({'status': 403, 'code': -1, 'data': {}, 'msg': 'No permission'})

    data = api.users.get_user_b30(user_id)

    if data['data'] == []:
        return jsonify({'status': 200, 'code': -3, 'data': {}, 'msg': code_get_msg(-3)})

    return jsonify({'status': 200, 'code': 0, 'data': data, 'msg': ''})


@bp.route('/users/<int:user_id>/best', methods=['GET'])
@api.api_auth.role_required(request, ['select', 'select_me'])
def users_user_best_get(user, user_id):
    # 查询用户所有best成绩

    if user_id == 'me':
        user_id = user.user_id

    if user_id <= 0:
        return jsonify({'status': 200, 'code': -4, 'data': {}, 'msg': code_get_msg(-4)})

    if user_id != user.user_id and not 'select' in user.power and user.user_id != 0:  # 查别人需要select权限
        return jsonify({'status': 403, 'code': -1, 'data': {}, 'msg': 'No permission'})

    limit, offset, query, sort, code = get_query_parameter(request, ['song_id', 'difficulty'], [
        'song_id', 'difficulty', 'score', 'time_played', 'rating'])
    if code < 0:
        return jsonify({'status': 200, 'code': code, 'data': {}, 'msg': code_get_msg(code)})

    data = api.users.get_user_best(user_id, limit, offset, query, sort)

    if data['data'] == []:
        return jsonify({'status': 200, 'code': -3, 'data': {}, 'msg': code_get_msg(-3)})

    return jsonify({'status': 200, 'code': 0, 'data': data, 'msg': ''})


@bp.route('/users/<int:user_id>/r30', methods=['GET'])
@api.api_auth.role_required(request, ['select', 'select_me'])
def users_user_r30_get(user, user_id):
    # 查询用户r30

    if user_id == 'me':
        user_id = user.user_id

    if user_id <= 0:
        return jsonify({'status': 200, 'code': -4, 'data': {}, 'msg': code_get_msg(-4)})

    if user_id != user.user_id and not 'select' in user.power and user.user_id != 0:  # 查别人需要select权限
        return jsonify({'status': 403, 'code': -1, 'data': {}, 'msg': 'No permission'})

    data = api.users.get_user_r30(user_id)

    if data['data'] == []:
        return jsonify({'status': 200, 'code': -3, 'data': {}, 'msg': code_get_msg(-3)})

    return jsonify({'status': 200, 'code': 0, 'data': data, 'msg': ''})


@bp.route('/songs/<string:song_id>', methods=['GET'])
@api.api_auth.role_required(request, ['select', 'select_song_info'])
def songs_song_get(user, song_id):
    # 查询歌曲信息

    data = api.songs.get_song_info(song_id)

    if not data:
        return jsonify({'status': 200, 'code': -2, 'data': {}, 'msg': code_get_msg(-2)})

    return jsonify({'status': 200, 'code': 0, 'data': data, 'msg': ''})


@bp.route('/songs', methods=['GET'])
@api.api_auth.role_required(request, ['select', 'select_song_info'])
def songs_get(user):
    # 查询全歌曲信息

    limit, offset, query, sort, code = get_query_parameter(request, ['sid', 'name_en', 'name_jp', 'pakset', 'artist'], [
                                                           'sid', 'name_en', 'name_jp', 'pakset', 'artist', 'date', 'rating_pst', 'rating_prs', 'rating_ftr', 'rating_byn'])
    if code < 0:
        return jsonify({'status': 200, 'code': code, 'data': {}, 'msg': code_get_msg(code)})

    data = api.songs.get_songs(limit, offset, query, sort)

    if not data:
        return jsonify({'status': 200, 'code': -2, 'data': {}, 'msg': code_get_msg(-2)})

    return jsonify({'status': 200, 'code': 0, 'data': data, 'msg': ''})
