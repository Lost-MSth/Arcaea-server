from flask import Blueprint, request

from core.config_manager import Config
from core.error import ArcError
from core.linkplay import MatchStore, Player, RemoteMultiPlayer, Room
from core.notification import RoomInviteNotification
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


@bp.route('/me/room/<room_code>/invite', methods=['POST'])  # 邀请
@auth_required(request)
@arc_try
def room_invite(user_id, room_code):
    if not Config.LINKPLAY_HOST:
        raise ArcError('The link play server is unavailable.', 151, status=404)

    other_user_id = request.form.get('to', type=int)

    x = RemoteMultiPlayer()
    share_token = x.select_room(room_code=room_code)['share_token']

    with Connect(in_memory=True) as c_m:
        with Connect() as c:
            sender = Player(c, user_id)
            sender.select_user_about_link_play()
            n = RoomInviteNotification.from_sender(
                sender, Player(c, other_user_id), share_token, c_m)
            n.insert()

    return success_return({})  # 无返回


@bp.route('/me/room/status', methods=['POST'])  # 房间号码获取
@auth_required(request)
@arc_try
def room_status(user_id):
    if not Config.LINKPLAY_HOST:
        raise ArcError('The link play server is unavailable.', 151, status=404)

    share_token = request.form.get('shareToken', type=str)

    x = RemoteMultiPlayer()
    room_code = x.select_room(share_token=share_token)['room_code']

    return success_return({
        'roomId': room_code,
    })


@bp.route('/me/matchmaking/join/', methods=['POST'])  # 匹配
@auth_required(request)
@arc_try
def matchmaking_join(user_id):
    if not Config.LINKPLAY_HOST:
        raise ArcError('The link play server is unavailable.', 151, status=404)

    with Connect() as c:
        user = Player(None, user_id)
        user.get_song_unlock(request.json['clientSongMap'])

        x = MatchStore(c)
        x.init_player(user)
        r = x.match(user_id)

        if r is None:
            return success_return({
                'userId': user_id,
                'status': 2,
            })

        r['endPoint'] = request.host.split(
            ':')[0] if Config.LINKPLAY_DISPLAY_HOST == '' else Config.LINKPLAY_DISPLAY_HOST
        r['port'] = int(Config.LINKPLAY_UDP_PORT)
        return success_return(r)


@bp.route('/me/matchmaking/status/', methods=['POST'])  # 匹配状态，5s 一次
@auth_required(request)
@arc_try
def matchmaking_status(user_id):
    if not Config.LINKPLAY_HOST:
        raise ArcError('The link play server is unavailable.', 151, status=404)

    with Connect() as c:

        r = MatchStore(c).match(user_id)
        if r is None:
            return success_return({
                'userId': user_id,
                'status': 0,
            })

        r['endPoint'] = request.host.split(
            ':')[0] if Config.LINKPLAY_DISPLAY_HOST == '' else Config.LINKPLAY_DISPLAY_HOST
        r['port'] = int(Config.LINKPLAY_UDP_PORT)
        return success_return(r)


@bp.route('/me/matchmaking/leave/', methods=['POST'])  # 退出匹配
@auth_required(request)
@arc_try
def matchmaking_leave(user_id):
    if not Config.LINKPLAY_HOST:
        raise ArcError('The link play server is unavailable.', 151, status=404)

    MatchStore().clear_player(user_id)

    return success_return({})
