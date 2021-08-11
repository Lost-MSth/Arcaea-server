from flask import (
    Blueprint, request, jsonify
)
import functools
import api.api_auth
import api.users
import api.songs
from api.api_code import code_get_msg


bp = Blueprint('api', __name__, url_prefix='/api/v1')


class Query():
    # 查询类，当查询附加参数的数据类型用
    def __init__(self, limit=-1, offset=0, query={}, sort=[]) -> None:
        self.limit = limit
        self.offset = offset
        self.query = query  # {'name': 'admin'}
        self.sort = sort  # [{'column': 'user_id', 'order': 'ASC'}, ...]


def get_query_parameter(request, query_able=[], sort_able=[]):
    # 提取查询请求参数，返回Query类查询参数，写成修饰器

    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(*args, **kwargs):

            re = Query()

            if 'limit' in request.json:
                try:
                    re.limit = int(request.json['limit'])
                except:
                    return jsonify({'status': 200, 'code': -101, 'data': {}, 'msg': code_get_msg(-101)})

            if 'offset' in request.json:
                try:
                    re.offset = int(request.json['offset'])
                except:
                    return jsonify({'status': 200, 'code': -101, 'data': {}, 'msg': code_get_msg(-101)})
            if 'query' in request.json:
                re.query = request.json['query']
                for i in re.query:
                    if i not in query_able:
                        return jsonify({'status': 200, 'code': -102, 'data': {}, 'msg': code_get_msg(-102)})
            if 'sort' in request.json:
                re.sort = request.json['sort']
                for i in re.sort:
                    if 'column' not in i or i['column'] not in sort_able:
                        return jsonify({'status': 200, 'code': -103, 'data': {}, 'msg': code_get_msg(-103)})
                    if not 'order' in i:
                        i['order'] = 'ASC'
                    else:
                        if i['order'] not in ['ASC', 'DESC']:
                            return jsonify({'status': 200, 'code': -104, 'data': {}, 'msg': code_get_msg(-104)})

            return view(re, *args, **kwargs)

        return wrapped_view
    return decorator


def return_encode(code: int = 0, data: dict = {}, status: int = 200, msg: str = ''):
    # 构造返回，返回jsonify处理过后的response_class
    if msg == '':
        msg = code_get_msg(code)
    if code < 0:
        return jsonify({'status': status, 'code': code, 'data': {}, 'msg': msg})
    else:
        return jsonify({'status': status, 'code': code, 'data': data, 'msg': msg})


@bp.route('/')
def ping():
    return return_encode()


@bp.route('/token', methods=['POST'])
def token_post():
    # 登录，获取token
    # {'auth': `base64(user_id:password)`}

    if 'auth' in request.json:
        data, code = api.api_auth.login(
            str(request.json['auth']), request.remote_addr)
        return return_encode(code, data)
    else:
        return return_encode(-1, {}, 401, 'No authentication')


@bp.route('/token', methods=['GET'])
@api.api_auth.role_required(request, ['select_me', 'select'])
def token_get(user):
    # 判断登录有效性
    return return_encode()


@bp.route('/token', methods=['DELETE'])
@api.api_auth.role_required(request, ['change_me', 'select_me', 'select'])
def token_delete(user):
    # 登出
    return return_encode()


@bp.route('/users', methods=['GET'])
@api.api_auth.role_required(request, ['select'])
@get_query_parameter(request, ['user_id', 'name', 'user_code'], [
    'user_id', 'name', 'user_code', 'join_date', 'rating_ptt', 'time_played', 'ticket', 'world_rank_score'])
def users_get(query, user):
    # 查询全用户信息

    data = api.users.get_users(query)

    if not data:
        return return_encode(-2)

    return return_encode(0, data)


@bp.route('/users/<int:user_id>', methods=['GET'])
@api.api_auth.role_required(request, ['select', 'select_me'])
def users_user_get(user, user_id):
    # 查询用户信息

    if user_id == 'me':
        user_id = user.user_id

    if user_id <= 0:
        return return_encode(-4)

    if user_id != user.user_id and not 'select' in user.power and user.user_id != 0:  # 查别人需要select权限
        return return_encode(-1, {}, 403, 'No permission')

    data = api.users.get_user_info(user_id)

    if not data:
        return return_encode(-3)

    return return_encode(0, data)


@bp.route('/users/<int:user_id>/b30', methods=['GET'])
@api.api_auth.role_required(request, ['select', 'select_me'])
def users_user_b30_get(user, user_id):
    # 查询用户b30

    if user_id <= 0:
        return return_encode(-4)

    if user_id != user.user_id and not 'select' in user.power and user.user_id != 0:  # 查别人需要select权限
        return return_encode(-1, {}, 403, 'No permission')

    data = api.users.get_user_b30(user_id)

    if data['data'] == []:
        return return_encode(-3)

    return return_encode(0, data)


@bp.route('/users/<int:user_id>/best', methods=['GET'])
@api.api_auth.role_required(request, ['select', 'select_me'])
@get_query_parameter(request, ['song_id', 'difficulty'], [
    'song_id', 'difficulty', 'score', 'time_played', 'rating'])
def users_user_best_get(query, user, user_id):
    # 查询用户所有best成绩

    if user_id <= 0:
        return return_encode(-4)

    if user_id != user.user_id and not 'select' in user.power and user.user_id != 0:  # 查别人需要select权限
        return return_encode(-1, {}, 403, 'No permission')

    data = api.users.get_user_best(user_id, query)

    if data['data'] == []:
        return return_encode(-3)

    return return_encode(0, data)


@bp.route('/users/<int:user_id>/r30', methods=['GET'])
@api.api_auth.role_required(request, ['select', 'select_me'])
def users_user_r30_get(user, user_id):
    # 查询用户r30

    if user_id <= 0:
        return return_encode(-4)

    if user_id != user.user_id and not 'select' in user.power and user.user_id != 0:  # 查别人需要select权限
        return return_encode(-1, {}, 403, 'No permission')

    data = api.users.get_user_r30(user_id)

    if data['data'] == []:
        return return_encode(-3)

    return return_encode(0, data)


@bp.route('/songs/<string:song_id>', methods=['GET'])
@api.api_auth.role_required(request, ['select', 'select_song_info'])
def songs_song_get(user, song_id):
    # 查询歌曲信息

    data = api.songs.get_song_info(song_id)

    if not data:
        return return_encode(-2)

    return return_encode(0, data)


@bp.route('/songs', methods=['GET'])
@api.api_auth.role_required(request, ['select', 'select_song_info'])
@get_query_parameter(request, ['sid', 'name_en', 'name_jp', 'pakset', 'artist'], [
    'sid', 'name_en', 'name_jp', 'pakset', 'artist', 'date', 'rating_pst', 'rating_prs', 'rating_ftr', 'rating_byn'])
def songs_get(query, user):
    # 查询全歌曲信息

    data = api.songs.get_songs(query)

    if not data:
        return return_encode(-2)

    return return_encode(0, data)
