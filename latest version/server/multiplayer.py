from flask import Blueprint, request

from core.config_manager import Config
from core.error import ArcError
from core.linkplay import Player, RemoteMultiPlayer, Room
from core.sql import Connect

from .auth import auth_required
from .func import arc_try, success_return

bp = Blueprint('multiplayer', __name__, url_prefix='/multiplayer')


@bp.route('/me/room/create', methods=['POST'])  # 创建房间
@auth_required(request)
@arc_try
def room_create(user_id):
    if not Config.LINKPLAY_HOST:
        raise ArcError('The link play server is unavailable.', 151, status=404)

    with Connect() as c:
        x = RemoteMultiPlayer()
        user = Player(c, user_id)
        user.get_song_unlock(request.json['clientSongMap'])
        x.create_room(user)
        r = x.to_dict()
        r['endPoint'] = request.host.split(
            ':')[0] if Config.LINKPLAY_DISPLAY_HOST == '' else Config.LINKPLAY_DISPLAY_HOST
        r['port'] = int(Config.LINKPLAY_UDP_PORT)
        return success_return(r)


@bp.route('/me/room/join/<room_code>', methods=['POST'])  # 加入房间
@auth_required(request)
@arc_try
def room_join(user_id, room_code):
    if not Config.LINKPLAY_HOST:
        raise ArcError('The link play server is unavailable.', 151, status=404)

    with Connect() as c:
        x = RemoteMultiPlayer()
        user = Player(c, user_id)
        user.get_song_unlock(request.json['clientSongMap'])
        room = Room()
        room.room_code = room_code
        x.join_room(room, user)
        r = x.to_dict()
        r['endPoint'] = request.host.split(
            ':')[0] if Config.LINKPLAY_DISPLAY_HOST == '' else Config.LINKPLAY_DISPLAY_HOST
        r['port'] = int(Config.LINKPLAY_UDP_PORT)
        return success_return(r)


@bp.route('/me/update', methods=['POST'])  # 更新房间
@auth_required(request)
@arc_try
def multiplayer_update(user_id):
    if not Config.LINKPLAY_HOST:
        raise ArcError('The link play server is unavailable.', 151, status=404)

    with Connect() as c:
        x = RemoteMultiPlayer()
        user = Player(c, user_id)
        user.token = int(request.json['token'])
        x.update_room(user)
        r = x.to_dict()
        r['endPoint'] = request.host.split(
            ':')[0] if Config.LINKPLAY_DISPLAY_HOST == '' else Config.LINKPLAY_DISPLAY_HOST
        r['port'] = int(Config.LINKPLAY_UDP_PORT)
        return success_return(r)
