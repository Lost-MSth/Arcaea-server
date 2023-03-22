from flask import Blueprint, request

from core.constant import Constant
from core.course import UserCourseList
from core.item import ItemCore
from core.sql import Connect
from core.user import UserOnline

from .auth import auth_required
from .func import arc_try, success_return

bp = Blueprint('course', __name__, url_prefix='/course')


@bp.route('/me', methods=['GET'])
@auth_required(request)
@arc_try
def course_me(user_id):
    with Connect() as c:
        user = UserOnline(c, user_id)
        core = ItemCore(c)
        core.item_id = 'core_course_skip_purchase'
        core.select_user_item(user)
        x = UserCourseList(c, user)
        x.select_all()
        return success_return({
            'courses': x.to_dict_list(),
            "stamina_cost": Constant.COURSE_STAMINA_COST,
            "course_skip_purchase_ticket": core.amount
        })
