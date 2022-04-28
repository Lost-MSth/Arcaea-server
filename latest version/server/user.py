from flask import Blueprint, request
from core.error import ArcError, NoAccess
from core.sql import Connect
from core.user import UserRegister, UserLogin, User, UserOnline
from core.character import UserCharacter
from .func import error_return, success_return
from .auth import auth_required
from setting import Config

bp = Blueprint('user', __name__, url_prefix='/user')


@bp.route('', methods=['POST'])  # 注册接口
def register():
    if 'AppVersion' in request.headers:  # 版本检查
        if Config.ALLOW_APPVERSION:
            if request.headers['AppVersion'] not in Config.ALLOW_APPVERSION:
                return error_return(NoAccess('Wrong app version.', 1203))

    with Connect() as c:
        try:
            new_user = UserRegister(c)
            new_user.set_name(request.form['name'])
            new_user.set_password(request.form['password'])
            new_user.set_email(request.form['email'])
            if 'device_id' in request.form:
                device_id = request.form['device_id']
            else:
                device_id = 'low_version'

            new_user.register()

            # 注册后自动登录
            user = UserLogin(c)
            user.login(new_user.name, new_user.password,
                       device_id, request.remote_addr)
            return success_return({'user_id': user.user_id, 'access_token': user.token})
        except ArcError as e:
            return error_return(e)
    return error_return()


@bp.route('/me/character', methods=['POST'])  # 角色切换
@auth_required(request)
def character_change(user_id):
    with Connect() as c:
        try:
            user = UserOnline(c, user_id)
            user.change_character(
                int(request.form['character']), request.form['skill_sealed'] == 'true')

            return success_return({'user_id': user.user_id, 'character': user.character.character_id})
        except ArcError as e:
            return error_return(e)
    return error_return()


# 角色觉醒切换
@bp.route('/me/character/<int:character_id>/toggle_uncap', methods=['POST'])
@auth_required(request)
def toggle_uncap(user_id, character_id):
    with Connect() as c:
        try:
            user = User()
            user.user_id = user_id
            character = UserCharacter(c)
            character.character_id = character_id
            character.change_uncap_override(user)
            character.select_character_info(user)
            return success_return({'user_id': user.user_id, 'character': [character.to_dict]})
        except ArcError as e:
            return error_return(e)
    return error_return()
