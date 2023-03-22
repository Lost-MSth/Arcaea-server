from flask import Blueprint, request

from core.sql import Connect
from core.user import UserOnline
from core.world import UserMap, get_world_all

from .auth import auth_required
from .func import arc_try, success_return

bp = Blueprint('world', __name__, url_prefix='/world')


@bp.route('/map/me', methods=['GET'])  # 获得世界模式信息，所有地图
@auth_required(request)
@arc_try
def world_all(user_id):
    with Connect() as c:
        user = UserOnline(c, user_id)
        user.select_user_about_current_map()
        return success_return({
            "current_map": user.current_map.map_id,
            "user_id": user_id,
            "maps": [x.to_dict(has_map_info=True, has_rewards=True) for x in get_world_all(c, user)]
        })


@bp.route('/map/me', methods=['POST'])  # 进入地图
@auth_required(request)
@arc_try
def world_in(user_id):
    with Connect() as c:
        arcmap = UserMap(c, request.form['map_id'], UserOnline(c, user_id))
        if arcmap.unlock():
            return success_return(arcmap.to_dict())


@bp.route('/map/me/<map_id>', methods=['GET'])  # 获得单个地图完整信息
@auth_required(request)
@arc_try
def world_one(user_id, map_id):
    with Connect() as c:
        arcmap = UserMap(c, map_id, UserOnline(c, user_id))
        arcmap.change_user_current_map()
        return success_return({
            "user_id": user_id,
            "current_map": map_id,
            "maps": [arcmap.to_dict(has_map_info=True, has_steps=True)]
        })
