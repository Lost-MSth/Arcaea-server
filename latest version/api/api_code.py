from flask import jsonify

from core.error import ArcError

default_error = ArcError('Unknown Error')


CODE_MSG = {
    0: '',
    -1: 'See status code',  # 基础错误
    -2: 'No data',
    -3: 'No data or user',  # 不确定是无数据还是无用户
    -4: 'Data exist',
    -100: 'Invalid post data',  # 1xx数据错误
    -101: 'Invalid data type',
    -102: 'Invalid query parameter',
    -103: 'Invalid sort parameter',
    -104: 'Invalid sort order parameter',
    -105: 'Invalid URL parameter',
    -110: 'Invalid user_id',
    -120: 'Invalid item type',
    -121: 'No such item',
    -122: 'Item already exists',
    -123: 'The collection already has this item',
    -124: 'The collection does not have this item',
    -130: 'No such character',
    -131: 'Invalid skill ID',
    -200: 'No permission',  # 2xx用户相关错误
    -201: 'Wrong username or password',
    -202: 'User is banned',
    -203: 'Too many login attempts',
    -210: 'Username exists',
    -211: 'Email address exists',
    -212: 'User code exists',
    -999: 'Unknown error'
}


def success_return(data: dict = {}, status: int = 200, msg: str = ''):
    return jsonify({'code': 0, 'data': data, 'msg': msg}), status


def error_return(e: 'ArcError' = default_error, status: int = 200):
    return jsonify({'code': e.api_error_code, 'data': {} if e.extra_data is None else e.extra_data, 'msg': CODE_MSG[e.api_error_code] if e.message is None else e.message}), status
