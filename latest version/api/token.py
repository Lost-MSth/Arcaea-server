from base64 import b64decode

from core.api_user import APIUser
from core.error import ArcError, PostError
from core.sql import Connect
from flask import Blueprint, request

from .api_auth import request_json_handle, role_required
from .api_code import error_return, success_return

bp = Blueprint('token', __name__, url_prefix='/token')


@bp.route('', methods=['POST'])
@request_json_handle(request, required_keys=['auth'])
def token_post(data):
    '''
        登录，获取token\ 
        {'auth': base64('<user_id>:<password>')}
    '''
    try:
        auth_decode = bytes.decode(b64decode(data['auth']))
    except:
        return error_return(PostError(api_error_code=-100))
    if not ':' in auth_decode:
        return error_return(PostError(api_error_code=-100))
    name, password = auth_decode.split(':', 1)

    with Connect() as c:
        try:
            user = APIUser(c)
            user.login(name, password, request.remote_addr)
            return success_return({'token': user.token, 'user_id': user.user_id})
        except ArcError as e:
            return error_return(e)
    return error_return()


@bp.route('', methods=['GET'])
@role_required(request, ['select_me', 'select'])
def token_get(user):
    '''判断登录有效性'''
    return success_return()


@bp.route('', methods=['DELETE'])
@role_required(request, ['change_me', 'select_me', 'select'])
def token_delete(user):
    '''登出'''
    with Connect() as c:
        try:
            user.c = c
            user.logout()
            return success_return()
        except ArcError as e:
            return error_return(e)
    return error_return()
