from flask import Blueprint, request

from core.error import NoData
from core.mission import MISSION_DICT
from core.sql import Connect
from core.user import UserOnline

from .auth import auth_required
from .func import arc_try, success_return

bp = Blueprint('mission', __name__, url_prefix='/mission')


def parse_mission_form(multidict) -> list:
    r = []

    x = multidict.get('mission_1')
    i = 1
    while x:
        r.append(x)
        x = multidict.get(f'mission_{i + 1}')
        i += 1
    return r


@bp.route('/me/clear', methods=['POST'])  # 新手任务确认完成
@auth_required(request)
@arc_try
def mission_clear(user_id):
    m = parse_mission_form(request.form)
    r = []
    for i, mission_id in enumerate(m):
        if mission_id not in MISSION_DICT:
            return NoData(f'Mission `{mission_id}` not found')
        with Connect() as c:
            x = MISSION_DICT[mission_id](c)
            x.user_clear_mission(UserOnline(c, user_id))
            d = x.to_dict()
            d['request_id'] = i + 1
            r.append(d)

    return success_return({'missions': r})


@bp.route('/me/claim', methods=['POST'])  # 领取新手任务奖励
@auth_required(request)
@arc_try
def mission_claim(user_id):
    m = parse_mission_form(request.form)
    r = []

    with Connect() as c:
        user = UserOnline(c, user_id)

        for i, mission_id in enumerate(m):
            if mission_id not in MISSION_DICT:
                return NoData(f'Mission `{mission_id}` not found')

            x = MISSION_DICT[mission_id](c)
            x.user_claim_mission(user)
            d = x.to_dict(has_items=True)
            d['request_id'] = i + 1
            r.append(d)

        return success_return({
            'missions': r,
            'user': user.to_dict()
        })
