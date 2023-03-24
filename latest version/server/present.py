from flask import Blueprint, request

from core.present import UserPresent, UserPresentList
from core.sql import Connect
from core.user import UserOnline

from .auth import auth_required
from .func import arc_try, success_return

bp = Blueprint('present', __name__, url_prefix='/present')


@bp.route('/me', methods=['GET'])  # 用户奖励信息
@auth_required(request)
@arc_try
def present_info(user_id):
    with Connect() as c:
        x = UserPresentList(c, UserOnline(c, user_id))
        x.select_user_presents()

        return success_return(x.to_dict_list())


@bp.route('/me/claim/<present_id>', methods=['POST'])  # 礼物确认
@auth_required(request)
@arc_try
def claim_present(user_id, present_id):
    with Connect() as c:
        x = UserPresent(c, UserOnline(c, user_id))
        x.claim_user_present(present_id)

        return success_return()
