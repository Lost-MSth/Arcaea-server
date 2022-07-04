import json
from urllib.parse import parse_qs, urlparse

from core.download import DownloadList
from core.error import ArcError
from core.sql import Connect
from core.system import GameInfo
from core.user import UserOnline
from flask import Blueprint, jsonify, request
from werkzeug.datastructures import ImmutableMultiDict

from .auth import auth_required
from .func import error_return, success_return
from .present import present_info
from .purchase import bundle_pack
from .score import song_score_friend
from .user import user_me
from .world import world_all

bp = Blueprint('others', __name__)


@bp.route('/game/info', methods=['GET'])  # 系统信息
def game_info():
    return success_return(GameInfo().to_dict())


@bp.route('/serve/download/me/song', methods=['GET'])  # 歌曲下载
@auth_required(request)
def download_song(user_id):
    with Connect() as c:
        try:
            x = DownloadList(c, UserOnline(c, user_id))
            x.song_ids = request.args.getlist('sid')
            x.url_flag = json.loads(request.args.get('url', 'true'))
            x.clear_user_download()
            if x.is_limited and x.url_flag:
                raise ArcError('You have reached the download limit.', 903)

            x.add_songs()
            return success_return(x.urls)
        except ArcError as e:
            return error_return(e)
    return error_return()


map_dict = {'/user/me': user_me,
            '/purchase/bundle/pack': bundle_pack,
            '/serve/download/me/song': download_song,
            '/game/info': game_info,
            '/present/me': present_info,
            '/world/map/me': world_all,
            '/score/song/friend': song_score_friend}


@bp.route('/compose/aggregate', methods=['GET'])  # 集成式请求
def aggregate():
    try:
        #global request
        finally_response = {'success': True, 'value': []}
        #request_ = request
        get_list = json.loads(request.args.get('calls'))
        if len(get_list) > 10:
            # 请求太多驳回
            return error_return()

        for i in get_list:
            endpoint = i['endpoint']
            request.args = ImmutableMultiDict(
                {key: value[0] for key, value in parse_qs(urlparse(endpoint).query).items()})

            resp_t = map_dict[urlparse(endpoint).path]()

            if hasattr(resp_t, "response"):
                resp_t = resp_t.response[0].decode().rstrip('\n')
            resp = json.loads(resp_t)

            if hasattr(resp, 'get') and resp.get('success') is False:
                finally_response = {'success': False, 'error_code': 7, 'extra': {
                    "id": i['id'], 'error_code': resp.get('error_code')}}
                if "extra" in resp:
                    finally_response['extra']['extra'] = resp['extra']
                #request = request_
                return jsonify(finally_response)

            finally_response['value'].append(
                {'id': i.get('id'), 'value': resp['value'] if hasattr(resp, 'get') else resp})

        #request = request_
        return jsonify(finally_response)
    except KeyError:
        return error_return()
