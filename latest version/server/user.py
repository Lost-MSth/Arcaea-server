from core.character import UserCharacter
from core.error import ArcError, NoAccess
from core.item import ItemCore
from core.save import SaveData
from core.sql import Connect
from core.user import User, UserLogin, UserOnline, UserRegister
from flask import Blueprint, request
from setting import Config

from .auth import auth_required
from .func import error_return, success_return

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


@bp.route('/me', methods=['GET'])  # 用户信息
@auth_required(request)
def user_me(user_id):
    with Connect() as c:
        try:
            return success_return(UserOnline(c, user_id).to_dict())
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
            character = UserCharacter(c, character_id)
            character.change_uncap_override(user)
            character.select_character_info(user)
            return success_return({'user_id': user.user_id, 'character': [character.to_dict()]})
        except ArcError as e:
            return error_return(e)
    return error_return()


# 角色觉醒
@bp.route('/me/character/<int:character_id>/uncap', methods=['POST'])
@auth_required(request)
def character_first_uncap(user_id, character_id):
    with Connect() as c:
        try:
            user = UserOnline(c, user_id)
            character = UserCharacter(c, character_id)
            character.select_character_info(user)
            character.character_uncap(user)
            return success_return({'user_id': user.user_id, 'character': [character.to_dict()], 'cores': user.cores})
        except ArcError as e:
            return error_return(e)
    return error_return()


# 角色使用以太之滴
@bp.route('/me/character/<int:character_id>/exp', methods=['POST'])
@auth_required(request)
def character_exp(user_id, character_id):
    with Connect() as c:
        try:
            user = UserOnline(c, user_id)
            character = UserCharacter(c, character_id)
            character.select_character_info(user)
            core = ItemCore(c)
            core.amount = - int(request.form['amount'])
            core.item_id = 'core_generic'
            character.upgrade_by_core(user, core)
            return success_return({'user_id': user.user_id, 'character': [character.to_dict], 'cores': user.cores})
        except ArcError as e:
            return error_return(e)
    return error_return()


@bp.route('/me/save', methods=['GET'])  # 从云端同步
@auth_required(request)
def cloud_get(user_id):
    with Connect() as c:
        try:
            user = User()
            user.user_id = user_id
            save = SaveData(c)
            save.select_all(user)
            return success_return(save.to_dict())
        except ArcError as e:
            return error_return(e)
    return error_return()


@bp.route('/me/save', methods=['POST'])  # 向云端同步
@auth_required(request)
def cloud_post(user_id):
    with Connect() as c:
        try:
            user = User()
            user.user_id = user_id
            save = SaveData(c)
            save.set_value(
                'scores_data', request.form['scores_data'], request.form['scores_checksum'])
            save.set_value(
                'clearlamps_data', request.form['clearlamps_data'], request.form['clearlamps_checksum'])
            save.set_value(
                'clearedsongs_data', request.form['clearedsongs_data'], request.form['clearedsongs_checksum'])
            save.set_value(
                'unlocklist_data', request.form['unlocklist_data'], request.form['unlocklist_checksum'])
            save.set_value(
                'installid_data', request.form['installid_data'], request.form['installid_checksum'])
            save.set_value('devicemodelname_data',
                           request.form['devicemodelname_data'], request.form['devicemodelname_checksum'])
            save.set_value(
                'story_data', request.form['story_data'], request.form['story_checksum'])
            save.set_value(
                'finalestate_data', request.form['finalestate_data'], request.form['finalestate_checksum'])

            save.update_all(user)
            return success_return({'user_id': user.user_id})
        except ArcError as e:
            return error_return(e)
    return error_return()


@bp.route('/me/setting/<set_arg>', methods=['POST'])  # 三个设置
@auth_required(request)
def sys_set(user_id, set_arg):
    with Connect() as c:
        try:
            value = request.form['value']
            user = UserOnline(c, user_id)
            if 'favorite_character' == set_arg:
                user.change_favorite_character(int(value))
            else:
                value = 'true' == value
                if 'is_hide_rating' == set_arg or 'max_stamina_notification_enabled' == set_arg:
                    user.update_user_one_column(set_arg, value)
            return success_return(user.to_dict())
        except ArcError as e:
            return error_return(e)
    return error_return()


@bp.route('/me/request_delete', methods=['POST'])  # 删除账号
@auth_required(request)
def user_delete(user_id):
    return error_return(ArcError('Cannot delete the account.', 151)), 404
