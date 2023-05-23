import base64
from functools import wraps

from flask import Blueprint, current_app, g, jsonify, request

from core.error import ArcError, NoAccess
from core.sql import Connect
from core.user import UserAuth, UserLogin

from .func import arc_try, error_return, header_check

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['POST'])  # 登录接口
@arc_try
def login():
    headers = request.headers
    e = header_check(request)
    if e is not None:
        raise e

    request.form['grant_type']
    with Connect() as c:
        id_pwd = headers['Authorization']
        id_pwd = base64.b64decode(id_pwd[6:]).decode()
        name, password = id_pwd.split(':', 1)
        if 'DeviceId' in headers:
            device_id = headers['DeviceId']
        else:
            device_id = 'low_version'

        user = UserLogin(c)
        user.login(name, password, device_id, request.remote_addr)
        current_app.logger.info(f'User `{user.user_id}` log in')
        return jsonify({"success": True, "token_type": "Bearer", 'user_id': user.user_id, 'access_token': user.token})


@bp.route('/verify', methods=['POST'])  # 邮箱验证进度查询
@arc_try
def email_verify():
    raise ArcError('Email verification unavailable.', 151, status=404)


def auth_required(req):
    # arcaea登录验证，写成了修饰器
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):

            headers = req.headers

            e = header_check(req)
            if e is not None:
                current_app.logger.warning(
                    f' - {e.error_code}|{e.api_error_code}: {e}')
                return error_return(e)

            with Connect() as c:
                try:
                    user = UserAuth(c)
                    token = headers.get('Authorization')
                    if not token:
                        raise NoAccess('No token.', -4)
                    user.token = token[7:]
                    user_id = user.token_get_id()
                    g.user = user
                except ArcError as e:
                    return error_return(e)
            return view(user_id, *args, **kwargs)

        return wrapped_view
    return decorator
