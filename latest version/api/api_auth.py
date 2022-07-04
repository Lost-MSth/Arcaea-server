import hashlib
import base64
import time
import random
from core.sql import Connect
import functools
from setting import Config
from flask import jsonify


class User():
    # 用户类，当数据类型用
    def __init__(self, user_id=None, role='', power=[]):
        self.user_id = user_id
        self.role = role
        self.power = power


def login(auth: str, ip: str):
    # 登录接口，返回字典和错误码

    try:
        auth_decode = bytes.decode(base64.b64decode(auth))
    except:
        return {}, -100

    if not ':' in auth_decode:
        return {}, -100

    name, password = auth_decode.split(':', 1)

    with Connect() as c:
        hash_pwd = hashlib.sha256(password.encode("utf8")).hexdigest()
        c.execute('''select user_id, password from user where name = :name''', {
            'name': name})
        x = c.fetchone()
        if x is None:
            return {}, -201
        if x[1] == '':
            return {}, -202
        if hash_pwd != x[1]:
            return {}, -201

        user_id = str(x[0])
        now = int(time.time() * 1000)
        token = hashlib.sha256(
            (user_id + str(random.randint(10000, 99999)) + str(now)).encode("utf8")).hexdigest()
        c.execute('''delete from api_login where user_id=?''', (user_id,))
        c.execute('''insert into api_login values(?,?,?,?)''',
                  (user_id, token, now, ip))

    return {'token': token, 'user_id': user_id}, 0


def logout(user: User):
    # 登出接口，返回错误码
    code = 999
    with Connect() as c:
        c.execute('''delete from api_login where user_id=?''', (user.user_id,))
        code = 0

    return code


def id_get_role_id(c, user_id):
    # user_id获取role_id
    role_id = 1
    c.execute('''select role_id from user_role where user_id = :a''',
              {'a': user_id})
    x = c.fetchone()
    if x is not None:
        role_id = int(x[0])

    return role_id


def role_id_get_role(c, role_id):
    # role_id获取role
    role = ''
    c.execute('''select role_name from role where role_id = :a''',
              {'a': role_id})
    x = c.fetchone()
    if x is not None:
        role = x[0]

    return role


def api_token_get_id(c, token):
    # api的token获取user_id
    user_id = None
    c.execute('''select user_id from api_login where token = :token''', {
        'token': token})
    x = c.fetchone()
    if x is not None:
        user_id = x[0]

    return user_id


def get_role_power(c, role_id):
    # 获取role_id对应power，返回列表

    role_power = []

    c.execute('''select power_name from power where power_id in (select power_id from role_power where role_id=:a)''', {
        'a': role_id})
    x = c.fetchall()
    for i in x:
        role_power.append(i[0])

    return role_power


def role_required(request, power=[]):
    # api token验证，写成了修饰器
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(*args, **kwargs):

            try:
                request.json  # 检查请求json格式
            except:
                return jsonify({'status': 400, 'code': -1, 'data': {}, 'msg': 'Payload must be a valid json'})

            if not 'Token' in request.headers:
                return jsonify({'status': 401, 'code': -1, 'data': {}, 'msg': 'No token'})

            user = User()
            if Config.API_TOKEN == request.headers['Token'] and Config.API_TOKEN != '':
                user.user_id = 0
            elif power == []:
                return jsonify({'status': 403, 'code': -1, 'data': {}, 'msg': 'No permission'})
            else:
                with Connect() as c:
                    user.user_id = api_token_get_id(
                        c, request.headers['Token'])
                    if user.user_id is None:
                        return jsonify({'status': 401, 'code': -1, 'data': {}, 'msg': 'No token'})

                    role_id = id_get_role_id(c, user.user_id)
                    user.role = role_id_get_role(c, role_id)
                    user.role_power = get_role_power(c, role_id)

                    f = False
                    for i in power:
                        if i in user.role_power:
                            f = True
                            break
                    if not f:
                        return jsonify({'status': 403, 'code': -1, 'data': {}, 'msg': 'No permission'})

            return view(user, *args, **kwargs)

        return wrapped_view
    return decorator
