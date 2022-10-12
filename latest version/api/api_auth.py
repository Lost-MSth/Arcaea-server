from functools import wraps
from traceback import format_exc

from core.api_user import APIUser
from core.error import ArcError, NoAccess, PostError
from core.sql import Connect
from flask import current_app
from setting import Config

from .api_code import error_return


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
            if Config.API_TOKEN == request.headers['Token'] and Config.API_TOKEN != '':
                user.set_role_system()
            else:
                with Connect() as c:
                    try:
                        user.c = c
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


def request_json_handle(request, required_keys=[], optional_keys=[]):
    '''
        提取post参数，返回dict，写成了修饰器\ 
        parameters: \ 
        `request`: `Request` - 当前请求\ 
        `required_keys`: `list` - 必须的参数\ 
        `optional_keys`: `list` - 可选的参数
    '''

    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):

            data = {}
            if not request.data:
                return view(data, *args, **kwargs)

            for key in required_keys:
                if key not in request.json:
                    return error_return(PostError('Missing parameter: ' + key, api_error_code=-100))
                data[key] = request.json[key]

            for key in optional_keys:
                if key in request.json:
                    data[key] = request.json[key]

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
            else:
                return data
        except ArcError as e:
            if Config.ALLOW_WARNING_LOG:
                current_app.logger.warning(format_exc())
            return error_return(e, e.status)

    return wrapped_view
