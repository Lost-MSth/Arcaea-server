import base64
import functools

from core.error import ArcError, NoAccess
from core.sql import Connect
from core.user import UserAuth, UserLogin
from flask import Blueprint, jsonify, request
from setting import Config

from .func import error_return

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['POST'])  # 登录接口
def login():
    if 'AppVersion' in request.headers:  # 版本检查
        if Config.ALLOW_APPVERSION:
            if request.headers['AppVersion'] not in Config.ALLOW_APPVERSION:
                return error_return(NoAccess('Wrong app version.', 1203))

    headers = request.headers
    request.form['grant_type']
    with Connect() as c:
        try:
            id_pwd = headers['Authorization']
            id_pwd = base64.b64decode(id_pwd[6:]).decode()
            name, password = id_pwd.split(':', 1)
            if 'DeviceId' in headers:
                device_id = headers['DeviceId']
            else:
                device_id = 'low_version'

            user = UserLogin(c)
            user.login(name, password, device_id, request.remote_addr)

            return jsonify({"success": True, "token_type": "Bearer", 'user_id': user.user_id, 'access_token': user.token})
        except ArcError as e:
            return error_return(e)

    return error_return()


def auth_required(request):
    # arcaea登录验证，写成了修饰器
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(*args, **kwargs):

            headers = request.headers

            if 'AppVersion' in headers:  # 版本检查
                if Config.ALLOW_APPVERSION:
                    if headers['AppVersion'] not in Config.ALLOW_APPVERSION:
                        return error_return(NoAccess('Wrong app version.', 1203))

            with Connect() as c:
                try:
                    user = UserAuth(c)
                    user.token = headers['Authorization'][7:]
                    return view(user.token_get_id(), *args, **kwargs)
                except ArcError as e:
                    return error_return(e)

            return error_return()

        return wrapped_view
    return decorator
