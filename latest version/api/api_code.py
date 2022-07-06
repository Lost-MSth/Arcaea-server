from core.error import ArcError
from flask import jsonify

default_error = ArcError('Unknown Error')


CODE_MSG = {
    0: '',
    -1: 'See status code',
    -2: 'No data',
    -3: 'No data or user',
    -4: 'No user_id',
    -100: 'Wrong post data',
    -101: 'Wrong data type',
    -102: 'Wrong query parameter',
    -103: 'Wrong sort parameter',
    -104: 'Wrong sort order parameter',
    -200: 'No permission',
    -201: 'Wrong username or password',
    -202: 'User is banned',
    -203: 'Username exists',
    -204: 'Email address exists',
    -999: 'Unknown error'
}


def success_return(data: dict = {}, status: int = 200, msg: str = ''):
    return jsonify({'code': 0, 'data': data, 'msg': msg}), status


def error_return(e: 'ArcError' = default_error, status: int = 200):
    return jsonify({'code': e.api_error_code, 'data': {} if e.extra_data is None else e.extra_data, 'msg': CODE_MSG[e.api_error_code] if e.message is None else e.message}), status
