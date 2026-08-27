from flask import Blueprint, current_app, request

from core.character import UserCharacter
from core.config_manager import Config
from core.error import ArcError
from core.item import ItemCore
from core.operation import DeleteOneUser
from core.save import SaveData
from core.sql import Connect
from core.user import User, UserLogin, UserOnline, UserRegister

from .auth import auth_required
from .func import arc_try, header_check, success_return

bp = Blueprint('user', __name__, url_prefix='/user')

bp2 = Blueprint('account', __name__, url_prefix='/account')


@bp.route('', methods=['POST'])  # 注册接口
@bp2.route('', methods=['POST'])
@arc_try
def register():
    error = header_check(request)
    if error is not None:
        raise error

    with Connect(begin_mode='IMMEDIATE') as c:
        new_user = UserRegister(c)
        new_user.set_name(request.form['name'])
        new_user.set_password(request.form['password'])
        new_user.set_email(request.form['email'])
        if 'device_id' in request.form:
            device_id = request.form['device_id']
        else:
            device_id = 'low_version'
        if 'is_allow_marketing_email' in request.form:
            new_user.is_allow_marketing_email = request.form['is_allow_marketing_email'] == 'true'

        ip = request.remote_addr
        new_user.register(device_id, ip)

        # 注册后自动登录
        user = UserLogin(c)
        user.login(new_user.name, new_user.password, device_id, ip)
        current_app.logger.info(f'New user `{user.user_id}` registered')
        return success_return({'user_id': user.user_id, 'access_token': user.token})


@bp.route('/me', methods=['GET'])  # 用户信息
@auth_required(request)
@arc_try
def user_me(user_id):
    with Connect() as c:
        return success_return(UserOnline(c, user_id).to_dict())


@bp.route('/me/toggle_invasion', methods=['POST'])  # insight skill
@auth_required(request)
@arc_try
def toggle_invasion(user_id):
    with Connect() as c:
        user = UserOnline(c, user_id)
        user.toggle_invasion()
        return success_return({'user_id': user.user_id, 'insight_state': user.insight_state})


@bp.route('/me/character', methods=['POST'])  # 角色切换
@auth_required(request)
@arc_try
def character_change(user_id):
    with Connect() as c:
        user = UserOnline(c, user_id)
        user.change_character(
            int(request.form['character']), request.form['skill_sealed'] == 'true')

        return success_return({'user_id': user.user_id, 'character': user.character.character_id})


# 角色觉醒切换
@bp.route('/me/character/<int:character_id>/toggle_uncap', methods=['POST'])
@auth_required(request)
@arc_try
def toggle_uncap(user_id, character_id):
    with Connect() as c:
        user = User()
        user.user_id = user_id
        character = UserCharacter(c, character_id)
        character.change_uncap_override(user)
        character.select_character_info(user)
        return success_return({'user_id': user.user_id, 'character': [character.to_dict()]})


# 角色觉醒
@bp.route('/me/character/<int:character_id>/uncap', methods=['POST'])
@auth_required(request)
@arc_try
def character_first_uncap(user_id, character_id):
    with Connect() as c:
        user = UserOnline(c, user_id)
        character = UserCharacter(c, character_id)
        character.select_character_info(user)
        character.character_uncap(user)
        return success_return({'user_id': user.user_id, 'character': [character.to_dict()], 'cores': user.cores})


# 角色使用以太之滴
@bp.route('/me/character/<int:character_id>/exp', methods=['POST'])
@auth_required(request)
@arc_try
def character_exp(user_id, character_id):
    with Connect() as c:
        user = UserOnline(c, user_id)
        character = UserCharacter(c, character_id)
        character.select_character_info(user)
        core = ItemCore(c)
        core.amount = - int(request.form['amount'])
        core.item_id = 'core_generic'
        character.upgrade_by_core(user, core)
        return success_return({'user_id': user.user_id, 'character': [character.to_dict()], 'cores': user.cores})


@bp.route('/me/save', methods=['GET'])  # 从云端同步
@auth_required(request)
@arc_try
def cloud_get(user_id):
    with Connect() as c:
        user = User()
        user.user_id = user_id
        save = SaveData(c)
        save.select_all(user)
        return success_return(save.to_dict())


@bp.route('/me/save', methods=['POST'])  # 向云端同步
@auth_required(request)
@arc_try
def cloud_post(user_id):
    with Connect() as c:
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
            'finalestate_data', request.form.get('finalestate_data'), request.form.get('finalestate_checksum'))

        save.update_all(user)
        return success_return({'user_id': user.user_id})


@bp.route('/me/profile', methods=['POST'])
@auth_required(request)
@arc_try
def profile_post(user_id):
    with Connect() as c:
        user = UserOnline(c, user_id)
        is_profile_public = request.form.get('is_profile_public')
        sc_char_1 = request.form.get('sc_char_1', -1, type=int)
        sc_char_2 = request.form.get('sc_char_2', -1, type=int)
        sc_char_3 = request.form.get('sc_char_3', -1, type=int)
        # world_unlock = request.form.get('world_unlock')
        banner = request.form.get('banner')
        # print(is_profile_public, world_unlock, banner)
        user.select_user_about_profile()
        user.change_profile(is_profile_public == 'true', banner, [
                            sc_char_1, sc_char_2, sc_char_3])

        return success_return({
            "is_profile_public": user.is_profile_public,
            "showcase_characters": user.showcase_characters,
            "world_unlock": "",
            "custom_banner": user.custom_banner
        })


@bp.route('/me/setting/<set_arg>', methods=['POST'])  # 三个设置
@auth_required(request)
@arc_try
def sys_set(user_id, set_arg):
    with Connect() as c:
        value = request.form['value']
        user = UserOnline(c, user_id)
        if 'favorite_character' == set_arg:
            user.change_favorite_character(int(value))
        else:
            value = 'true' == value
            if set_arg in ('is_hide_rating', 'max_stamina_notification_enabled', 'mp_notification_enabled', 'is_allow_marketing_email'):
                user.update_user_one_column(set_arg, value)
        return success_return(user.to_dict())


@bp.route('/me/request_delete', methods=['POST'])  # 删除账号
@bp2.route('/me/request_delete', methods=['POST'])
@auth_required(request)
@arc_try
def user_delete(user_id):
    if not Config.ALLOW_SELF_ACCOUNT_DELETE:
        raise ArcError('Cannot delete the account.', 151, status=404)
    DeleteOneUser().set_params(user_id).run()
    return success_return({'user_id': user_id})


@bp.route('/email/resend_verify', methods=['POST'])  # 邮箱验证重发
@bp2.route('/email/resend_verify', methods=['POST'])
@arc_try
def email_resend_verify():
    raise ArcError('Email verification unavailable.', 151, status=404)


@bp.route('/verify', methods=['POST'])  # 邮箱验证状态查询
@bp2.route('/verify', methods=['POST'])
@arc_try
def email_verify():
    raise ArcError('Email verification unavailable.', 151, status=404)
