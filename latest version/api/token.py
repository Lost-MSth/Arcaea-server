from base64 import b64decode

from flask import Blueprint, current_app, request

from core.api_user import APIUser
from core.error import PostError
from core.sql import Connect

from .api_auth import api_try, request_json_handle, role_required
from .api_code import success_return

bp = Blueprint('token', __name__, url_prefix='/token')


@bp.route('', methods=['POST'])
@request_json_handle(request, required_keys=['auth'])
@api_try
def token_post(data):
    '''
        登录，获取token

        {'auth': base64('<user_id>:<password>')}
    '''
    try:
        auth_decode = bytes.decode(b64decode(data['auth']))
    except Exception as e:
        raise PostError(api_error_code=-100) from e
    if ':' not in auth_decode:
        raise PostError(api_error_code=-100)
    name, password = auth_decode.split(':', 1)

    with Connect() as c:
        user = APIUser(c)
        user.login(name, password, request.remote_addr)
        current_app.logger.info(f'API user `{user.user_id}` log in')
        return success_return({'token': user.api_token, 'user_id': user.user_id})


@bp.route('', methods=['GET'])
@role_required(request, ['select_me', 'select'])
@api_try
def token_get(user):
    '''判断登录有效性'''
    return success_return()


@bp.route('', methods=['DELETE'])
@role_required(request, ['change_me', 'select_me', 'select'])
@api_try
def token_delete(user):
    '''登出'''
    with Connect() as c:
        user.c = c
        user.logout()
        return success_return()
