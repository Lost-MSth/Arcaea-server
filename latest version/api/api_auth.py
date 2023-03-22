from base64 import b64decode
from functools import wraps
from json import loads
from traceback import format_exc

from flask import current_app

from core.api_user import APIUser
from core.config_manager import Config
from core.error import ArcError, InputError, NoAccess, PostError
from core.sql import Connect

from .api_code import error_return
from .constant import Constant


def role_required(request, powers=[]):
    '''api token验证，写成了修饰器'''
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            try:
                if request.data:
                    request.json  # 检查请求json格式
            except:
                return error_return(PostError('Payload must be a valid json', api_error_code=-1), 400)

            if not 'Token' in request.headers:
                return error_return(PostError('No token', api_error_code=-1), 401)

            user = APIUser()
            with Connect() as c:
                user.c = c
                if Config.API_TOKEN == request.headers['Token'] and Config.API_TOKEN != '':
                    user.set_role_system()
                else:
                    try:
                        user.select_user_id_from_api_token(
                            request.headers['Token'])
                        user.select_role_and_powers()

                        if not any(user.role.has_power(y) for y in powers):
                            return error_return(NoAccess('No permission', api_error_code=-1), 403)
                    except ArcError as e:
                        return error_return(e, 401)

            return view(user, *args, **kwargs)

        return wrapped_view
    return decorator


def request_json_handle(request, required_keys: list = [], optional_keys: list = [], must_change: bool = False, is_batch: bool = False):
    '''
        提取post参数，返回dict，写成了修饰器

        parameters:
        `request`: `Request` - 当前请求
        `required_keys`: `list` - 必须的参数
        `optional_keys`: `list` - 可选的参数
        `must_change`: `bool` - 当全都是可选参数时，是否必须有至少一项修改
    '''

    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):

            data = {}
            if request.data:
                json_data = request.get_json()
            else:
                if request.method == 'GET' and 'query' in request.args:
                    # 处理axios没法GET传data的问题
                    try:
                        json_data = loads(
                            b64decode(request.args['query']).decode())
                    except:
                        raise PostError(api_error_code=-105)
                else:
                    json_data = {}

            for key in required_keys:
                if key not in json_data:
                    return error_return(InputError(f'Missing parameter: {key}', api_error_code=-100))
                data[key] = json_data[key]

            if is_batch:
                for key in Constant.PATCH_KEYS:
                    if key in json_data:
                        data[key] = json_data[key]
                        if not isinstance(data[key], list):
                            return error_return(InputError(f'Parameter {key} must be a list', api_error_code=-100))
                if not data:
                    return error_return(InputError('No change', api_error_code=-100))
            else:
                for key in optional_keys:
                    if key in json_data:
                        data[key] = json_data[key]

                if must_change and not data:
                    return error_return(InputError('No change', api_error_code=-100))

            return view(data, *args, **kwargs)

        return wrapped_view
    return decorator


def api_try(view):
    '''替代try/except，记录`ArcError`为warning'''
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        try:
            data = view(*args, **kwargs)
            if data is None:
                return error_return()
            return data
        except ArcError as e:
            if Config.ALLOW_WARNING_LOG:
                current_app.logger.warning(format_exc())
            return error_return(e, e.status)

    return wrapped_view
