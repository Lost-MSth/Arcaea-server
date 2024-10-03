import json
from urllib.parse import parse_qs, urlparse

from flask import Blueprint, jsonify, request
from werkzeug.datastructures import ImmutableMultiDict

from core.bundle import BundleDownload
from core.download import DownloadList
from core.error import RateLimit
from core.item import ItemCharacter
from core.notification import NotificationFactory
from core.sql import Connect
from core.system import GameInfo
from core.user import UserOnline

from .auth import auth_required
from .func import arc_try, error_return, success_return
from .present import present_info
from .purchase import bundle_bundle, bundle_pack, get_single
from .score import song_score_friend
from .user import user_me
from .world import world_all

bp = Blueprint('others', __name__)


@bp.route('/game/info', methods=['GET'])  # 系统信息
def game_info():
    return success_return(GameInfo().to_dict())


@bp.route('/notification/me', methods=['GET'])  # 通知
@auth_required(request)
@arc_try
def notification_me(user_id):
    with Connect(in_memory=True) as c_m:
        x = NotificationFactory(c_m, UserOnline(c_m, user_id))
        return success_return([i.to_dict() for i in x.get_notification()])


@bp.route('/game/content_bundle', methods=['GET'])  # 热更新
@arc_try
def game_content_bundle():
    # error code 5, 9 work
    app_version = request.headers.get('AppVersion')
    bundle_version = request.headers.get('ContentBundle')
    device_id = request.headers.get('DeviceId')
    with Connect(in_memory=True) as c_m:
        x = BundleDownload(c_m)
        x.set_client_info(app_version, bundle_version, device_id)
        return success_return({
            'orderedResults': x.get_bundle_list()
        })


@bp.route('/serve/download/me/song', methods=['GET'])  # 歌曲下载
@auth_required(request)
@arc_try
def download_song(user_id):
    with Connect(in_memory=True) as c_m:
        with Connect() as c:
            x = DownloadList(c_m, UserOnline(c, user_id))
            x.song_ids = request.args.getlist('sid')
            x.url_flag = json.loads(request.args.get('url', 'true'))
            if x.url_flag and x.is_limited:
                raise RateLimit('You have reached the download limit.', 903)

            x.add_songs()
            return success_return(x.urls)


@bp.route('/finale/progress', methods=['GET'])
def finale_progress():
    # 世界boss血条
    return success_return({'percentage': 100000})


@bp.route('/finale/finale_start', methods=['POST'])
@auth_required(request)
@arc_try
def finale_start(user_id):
    # testify开始，对立再见
    # 但是对立不再见

    with Connect() as c:
        item = ItemCharacter(c)
        item.set_id('55')  # Hikari (Fatalis)
        item.user_claim_item(UserOnline(c, user_id))
        return success_return({})


@bp.route('/finale/finale_end', methods=['POST'])
@auth_required(request)
@arc_try
def finale_end(user_id):

    with Connect() as c:
        item = ItemCharacter(c)
        item.set_id('5')  # Hikari & Tairitsu (Reunion)
        item.user_claim_item(UserOnline(c, user_id))
        return success_return({})


@bp.route('/applog/me/log', methods=['POST'])
def applog_me():
    # 异常日志，不处理
    return success_return({})


map_dict = {
    '/user/me': user_me,
    '/purchase/bundle/pack': bundle_pack,
    '/serve/download/me/song': download_song,
    '/game/info': game_info,
    '/present/me': present_info,
    '/world/map/me': world_all,
    '/score/song/friend': song_score_friend,
    '/purchase/bundle/bundle': bundle_bundle,
    '/finale/progress': finale_progress,
    '/purchase/bundle/single': get_single
}


@bp.route('/compose/aggregate', methods=['GET'])  # 集成式请求
def aggregate():
    try:
        # global request
        finally_response = {'success': True, 'value': []}
        # request_ = request
        get_list = json.loads(request.args.get('calls'))
        if len(get_list) > 10:
            # 请求太多驳回
            return error_return()

        for i in get_list:
            endpoint = i['endpoint']
            request.args = ImmutableMultiDict(
                {key: value[0] for key, value in parse_qs(urlparse(endpoint).query).items()})

            resp_t = map_dict[urlparse(endpoint).path]()
            if isinstance(resp_t, tuple):
                # The response may be a tuple, if it is an error response
                resp_t = resp_t[0]

            if hasattr(resp_t, "response"):
                resp_t = resp_t.response[0].decode().rstrip('\n')
            resp = json.loads(resp_t)

            if hasattr(resp, 'get') and resp.get('success') is False:
                finally_response = {'success': False, 'error_code': resp.get(
                    'error_code'), 'id': i['id']}
                if "extra" in resp:
                    finally_response['extra'] = resp['extra']
                # request = request_
                return jsonify(finally_response)

            finally_response['value'].append(
                {'id': i.get('id'), 'value': resp['value'] if hasattr(resp, 'get') else resp})

        # request = request_
        return jsonify(finally_response)
    except KeyError:
        return error_return()
