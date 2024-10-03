from flask import Blueprint, jsonify

from core.config_manager import Config

from . import (auth, course, friend, multiplayer, others, present, purchase,
               score, user, world, mission)


__bp_old = Blueprint('old_server', __name__)


@__bp_old.route('/<path:any>', methods=['GET', 'POST'])  # 旧版 API 提示
def server_hello(any):
    return jsonify({"success": False, "error_code": 5})


def get_bps():
    def string_to_list(s):
        if isinstance(s, str):
            s = [s]
        elif not isinstance(s, list):
            s = []
        return s

    bp = Blueprint('server', __name__)
    list(map(bp.register_blueprint, [user.bp, auth.bp, friend.bp, score.bp,
                                     world.bp, purchase.bp, present.bp, others.bp, multiplayer.bp, course.bp, mission.bp]))

    bps = [Blueprint(x, __name__, url_prefix=x)
           for x in string_to_list(Config.GAME_API_PREFIX)]
    for x in bps:
        x.register_blueprint(bp)

    old_bps = [Blueprint(x, __name__, url_prefix=x)
               for x in string_to_list(Config.OLD_GAME_API_PREFIX)]
    for x in old_bps:
        x.register_blueprint(__bp_old)

    return bps + old_bps
