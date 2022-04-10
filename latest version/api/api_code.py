from flask import jsonify


def code_get_msg(code):
    # api接口code获取msg，返回字符串
    msg = {
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
        -201: 'Wrong username or password',
        -202: 'User is banned',
        -203: 'Username exists',
        -204: 'Email address exists',
        -999: 'Unknown error'
    }

    return msg[code]


def return_encode(code: int = 0, data: dict = {}, status: int = 200, msg: str = ''):
    # 构造返回，返回jsonify处理过后的response_class
    if msg == '':
        msg = code_get_msg(code)
    if code < 0:
        return jsonify({'status': status, 'code': code, 'data': {}, 'msg': msg})
    else:
        return jsonify({'status': status, 'code': code, 'data': data, 'msg': msg})
