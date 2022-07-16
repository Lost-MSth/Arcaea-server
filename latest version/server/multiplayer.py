from multiprocessing import Pipe

from core.error import ArcError
from core.linkplay import LocalMultiPlayer, Player, Room
from core.sql import Connect
from flask import Blueprint, request
from setting import Config

from .auth import auth_required
from .func import arc_try, success_return

bp = Blueprint('multiplayer', __name__, url_prefix='/multiplayer')

conn1, conn2 = Pipe()


@bp.route('/me/room/create', methods=['POST'])  # 创建房间
@auth_required(request)
@arc_try
def room_create(user_id):
    if not Config.UDP_PORT or Config.UDP_PORT == '':
        raise ArcError('The local udp server is down.', 151, status=404)
    with Connect() as c:
        x = LocalMultiPlayer(conn1)
        user = Player(c, user_id)
        user.get_song_unlock(request.json['clientSongMap'])
        x.create_room(user)
        r = x.to_dict()
        r['endPoint'] = request.host.split(
            ':')[0] if Config.LINK_PLAY_HOST == '' else Config.LINK_PLAY_HOST
        r['port'] = int(Config.UDP_PORT)
        return success_return(r)


@bp.route('/me/room/join/<room_code>', methods=['POST'])  # 加入房间
@auth_required(request)
@arc_try
def room_join(user_id, room_code):
    if not Config.UDP_PORT or Config.UDP_PORT == '':
        raise ArcError('The local udp server is down.', 151, status=404)

    with Connect() as c:
        x = LocalMultiPlayer(conn1)
        user = Player(c, user_id)
        user.get_song_unlock(request.json['clientSongMap'])
        room = Room()
        room.room_code = room_code
        x.join_room(room, user)
        r = x.to_dict()
        r['endPoint'] = request.host.split(
            ':')[0] if Config.LINK_PLAY_HOST == '' else Config.LINK_PLAY_HOST
        r['port'] = int(Config.UDP_PORT)
        return success_return(r)


@bp.route('/me/update', methods=['POST'])  # 更新房间
@auth_required(request)
@arc_try
def multiplayer_update(user_id):
    if not Config.UDP_PORT or Config.UDP_PORT == '':
        raise ArcError('The local udp server is down.', 151, status=404)

    with Connect() as c:
        x = LocalMultiPlayer(conn1)
        user = Player(c, user_id)
        user.token = int(request.json['token'])
        x.update_room(user)
        r = x.to_dict()
        r['endPoint'] = request.host.split(
            ':')[0] if Config.LINK_PLAY_HOST == '' else Config.LINK_PLAY_HOST
        r['port'] = int(Config.UDP_PORT)
        return success_return(r)
