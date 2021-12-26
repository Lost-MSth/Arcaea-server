# encoding: utf-8

from flask import Flask, json, request, jsonify, make_response, send_from_directory
from logging.config import dictConfig
from setting import Config
import base64
import server.auth
import server.info
import server.setme
import server.arcscore
import web.login
import web.index
import api.api_main
import server.arcworld
import server.arcdownload
import server.arcpurchase
import server.init
import server.character
import os
import sys


app = Flask(__name__)
wsgi_app = app.wsgi_app

os.chdir(sys.path[0])  # 更改工作路径，以便于愉快使用相对路径

app.config.from_mapping(SECRET_KEY=Config.SECRET_KEY)
app.config['SESSION_TYPE'] = 'filesystem'
app.register_blueprint(web.login.bp)
app.register_blueprint(web.index.bp)
app.register_blueprint(api.api_main.bp)

log_dict = {
    'version': 1,
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi', 'error_file']
    },
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "maxBytes": 1024 * 1024,
            "backupCount": 1,
            "encoding": "utf-8",
            "level": "ERROR",
            "formatter": "default",
            "filename": "./log/error.log"
        }
    },
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        }
    }
}
if Config.ALLOW_LOG_INFO:
    log_dict['root']['handlers'] = ['wsgi', 'info_file', 'error_file']
    log_dict['handlers']['info_file'] = {
        "class": "logging.handlers.RotatingFileHandler",
        "maxBytes": 1024 * 1024,
        "backupCount": 1,
        "encoding": "utf-8",
        "level": "INFO",
        "formatter": "default",
        "filename": "./log/info.log"
    }

dictConfig(log_dict)

if not server.init.check_before_run(app):
    app.logger.error('Something wrong. The server will not run.')
    input('Press ENTER key to exit.')
    sys.exit()

app.logger.info("Start to initialize data in 'songfile' table...")
try:
    error = server.arcdownload.initialize_songfile()
except:
    error = 'Something wrong.'
if error:
    app.logger.warning(error)
else:
    app.logger.info('Complete!')


def add_url_prefix(url, strange_flag=False):
    # 给url加前缀，返回字符串
    if not url or not Config.GAME_API_PREFIX:
        return Config.GAME_API_PREFIX + url

    prefix = Config.GAME_API_PREFIX
    if prefix[0] != '/':
        prefix = '/' + prefix
    if prefix[-1] == '/':
        prefix = prefix[:-1]

    if url[0] != '/':
        r = '/' + url
    else:
        r = url

    if strange_flag and prefix.count('/') >= 1:  # 为了方便处理双斜杠
        t = prefix[::-1]
        t = t[t.find('/')+1:]
        prefix = t[::-1]

    return prefix + r


def error_return(error_code, extra={}):  # 错误返回
    # -7 处理交易时发生了错误
    # -5 所有的曲目都已经下载完毕
    # -4 您的账号已在别处登录
    # -3 无法连接至服务器
    # 2 Arcaea服务器正在维护
    # 9 新版本请等待几分钟
    # 100 无法在此ip地址下登录游戏
    # 101 用户名占用
    # 102 电子邮箱已注册
    # 103 已有一个账号由此设备创建
    # 104 用户名密码错误
    # 105 24小时内登入两台设备
    # 106 121 账户冻结
    # 107 你没有足够的体力
    # 113 活动已结束
    # 114 该活动已结束，您的成绩不会提交
    # 115 请输入有效的电子邮箱地址
    # 120 封号警告
    # 122 账户暂时冻结
    # 123 账户被限制
    # 124 你今天不能再使用这个IP地址创建新的账号
    # 150 非常抱歉您已被限制使用此功能
    # 151 目前无法使用此功能
    # 401 用户不存在
    # 403 无法连接至服务器
    # 501 502 -6 此物品目前无法获取
    # 504 无效的序列码
    # 505 此序列码已被使用
    # 506 你已拥有了此物品
    # 601 好友列表已满
    # 602 此用户已是好友
    # 604 你不能加自己为好友
    # 903 下载量超过了限制，请24小时后重试
    # 905 请在再次使用此功能前等待24小时
    # 1001 设备数量达到上限
    # 1002 此设备已使用过此功能
    # 1201 房间已满
    # 1202 房间号码无效
    # 1203 请将Arcaea更新至最新版本
    # 1205 此房间目前无法加入
    # 9801 下载歌曲时发生问题，请再试一次
    # 9802 保存歌曲时发生问题，请检查设备空间容量
    # 9803 下载已取消
    # 9905 没有在云端发现任何数据
    # 9907 更新数据时发生了问题
    # 9908 服务器只支持最新的版本，请更新Arcaea
    # 其它 发生未知错误
    if extra:
        return jsonify({
            "success": False,
            "error_code": error_code,
            "extra": extra
        })
    else:
        return jsonify({
            "success": False,
            "error_code": error_code
        })


@app.route('/')
def hello():
    return "Hello World!"
# 自定义路径


@app.route('/favicon.ico', methods=['GET'])  # 图标
def favicon():
    # Pixiv ID: 82374369
    # 我觉得这张图虽然并不是那么精细，但很有感觉，色彩的强烈对比下给人带来一种惊艳
    # 然后在压缩之下什么也看不清了:(

    return app.send_static_file('favicon.ico')


@app.route(add_url_prefix('/auth/login'), methods=['POST'])  # 登录接口
def login():
    if 'AppVersion' in request.headers:  # 版本检查
        if Config.ALLOW_APPVERSION:
            if request.headers['AppVersion'] not in Config.ALLOW_APPVERSION:
                return error_return(1203)

    headers = request.headers
    id_pwd = headers['Authorization']
    id_pwd = base64.b64decode(id_pwd[6:]).decode()
    name, password = id_pwd.split(':', 1)
    if 'DeviceId' in headers:
        device_id = headers['DeviceId']
    else:
        device_id = 'low_version'

    token, error_code, extra = server.auth.arc_login(
        name, password, device_id, request.remote_addr)
    if not error_code:
        r = {"success": True, "token_type": "Bearer"}
        r['access_token'] = token
        return jsonify(r)
    else:
        if extra:
            return error_return(error_code, extra)
        else:
            return error_return(error_code)


@app.route(add_url_prefix('/user'), methods=['POST'])  # 注册接口
def register():
    if 'AppVersion' in request.headers:  # 版本检查
        if Config.ALLOW_APPVERSION:
            if request.headers['AppVersion'] not in Config.ALLOW_APPVERSION:
                return error_return(5)

    name = request.form['name']
    password = request.form['password']
    email = request.form['email']
    if 'device_id' in request.form:
        device_id = request.form['device_id']
    else:
        device_id = 'low_version'

    user_id, token, error_code = server.auth.arc_register(
        name, password, device_id, email, request.remote_addr)
    if user_id is not None:
        r = {"success": True, "value": {
            'user_id': user_id, 'access_token': token}}
        return jsonify(r)
    else:
        return error_return(error_code)


# 集成式请求，没想到什么好办法处理，就先这样写着
@app.route(add_url_prefix('/compose/aggregate'), methods=['GET'])
@server.auth.auth_required(request)
def aggregate(user_id):
    calls = request.args.get('calls')
    if calls == '[{ "endpoint": "/user/me", "id": 0 }]':  # 极其沙雕的判断，我猜get的参数就两种
        r = server.info.arc_aggregate_small(user_id)
    else:
        r = server.info.arc_aggregate_big(user_id)
    return jsonify(r)


@app.route(add_url_prefix('/user/me'), methods=['GET'])  # 用户信息，给baa查分器用的
@server.auth.auth_required(request)
def user_me(user_id):
    r = server.info.arc_aggregate_small(user_id)
    if r['success']:
        r['value'] = r['value'][0]['value']
    return jsonify(r)


@app.route(add_url_prefix('/user/me/character'), methods=['POST'])  # 角色切换
@server.auth.auth_required(request)
def character_change(user_id):
    character_id = request.form['character']
    skill_sealed = request.form['skill_sealed']

    flag = server.setme.change_char(user_id, character_id, skill_sealed)
    if flag:
        return jsonify({
            "success": True,
            "value": {
                "user_id": user_id,
                "character": character_id
            }
        })
    else:
        return error_return(108)


# 角色觉醒切换
@app.route(add_url_prefix('/<path:path>/toggle_uncap', True), methods=['POST'])
@server.auth.auth_required(request)
def character_uncap(user_id, path):
    character_id = int(path[path.find('character')+10:])
    r = server.setme.change_char_uncap(user_id, character_id)
    if r is not None:
        return jsonify({
            "success": True,
            "value": {
                "user_id": user_id,
                "character": [r]
            }
        })
    else:
        return error_return(108)


# 角色觉醒
@app.route(add_url_prefix('/<path:path>/uncap', True), methods=['POST'])
@server.auth.auth_required(request)
def character_first_uncap(user_id, path):
    character_id = int(path[path.find('character')+10:])
    r = server.character.char_uncap(user_id, character_id)
    if r is not None:
        return jsonify({
            "success": True,
            "value": r
        })
    else:
        return error_return(108)


# 角色使用以太之滴
@app.route(add_url_prefix('/<path:path>/exp', True), methods=['POST'])
@server.auth.auth_required(request)
def character_exp(user_id, path):
    character_id = int(path[path.find('character')+10:])
    amount = int(request.form['amount'])
    r = server.character.char_use_core(user_id, character_id, amount)
    if r is not None:
        return jsonify({
            "success": True,
            "value": r
        })
    else:
        return error_return(108)


@app.route(add_url_prefix('/friend/me/add'), methods=['POST'])  # 加好友
@server.auth.auth_required(request)
def add_friend(user_id):
    friend_code = request.form['friend_code']
    friend_id = server.auth.code_get_id(friend_code)
    if friend_id is not None:
        r = server.setme.arc_add_friend(user_id, friend_id)
        if r is not None and r != 602 and r != 604:
            return jsonify({
                "success": True,
                "value": {
                    "user_id": user_id,
                    "updatedAt": "2020-09-07T07:32:12.740Z",
                    "createdAt": "2020-09-06T10:05:18.471Z",
                    "friends": r
                }
            })
        else:
            if r is not None:
                return error_return(r)
            else:
                return error_return(108)
    else:
        return error_return(401)


@app.route(add_url_prefix('/friend/me/delete'), methods=['POST'])  # 删好友
@server.auth.auth_required(request)
def delete_friend(user_id):
    friend_id = int(request.form['friend_id'])
    if friend_id is not None:
        r = server.setme.arc_delete_friend(user_id, friend_id)
        if r is not None:
            return jsonify({
                "success": True,
                "value": {
                    "user_id": user_id,
                    "updatedAt": "2020-09-07T07:32:12.740Z",
                    "createdAt": "2020-09-06T10:05:18.471Z",
                    "friends": r
                }
            })
        else:
            return error_return(108)
    else:
        return error_return(401)


# 好友排名，默认最多50
@app.route(add_url_prefix('/score/song/friend'), methods=['GET'])
@server.auth.auth_required(request)
def song_score_friend(user_id):
    song_id = request.args.get('song_id')
    difficulty = request.args.get('difficulty')
    r = server.arcscore.arc_score_friend(user_id, song_id, difficulty)
    if r is not None:
        return jsonify({
            "success": True,
            "value": r
        })
    else:
        return error_return(108)


@app.route(add_url_prefix('/score/song/me'), methods=['GET'])  # 我的排名，默认最多20
@server.auth.auth_required(request)
def song_score_me(user_id):
    song_id = request.args.get('song_id')
    difficulty = request.args.get('difficulty')
    r = server.arcscore.arc_score_me(user_id, song_id, difficulty)
    if r is not None:
        return jsonify({
            "success": True,
            "value": r
        })
    else:
        return error_return(108)


@app.route(add_url_prefix('/score/song'), methods=['GET'])  # TOP20
@server.auth.auth_required(request)
def song_score_top(user_id):
    song_id = request.args.get('song_id')
    difficulty = request.args.get('difficulty')
    r = server.arcscore.arc_score_top(song_id, difficulty)
    if r is not None:
        return jsonify({
            "success": True,
            "value": r
        })
    else:
        return error_return(108)


@app.route(add_url_prefix('/score/song'), methods=['POST'])  # 成绩上传
@server.auth.auth_required(request)
def song_score_post(user_id):
    song_token = request.form['song_token']
    song_hash = request.form['song_hash']
    song_id = request.form['song_id']
    difficulty = int(request.form['difficulty'])
    score = int(request.form['score'])
    shiny_perfect_count = int(request.form['shiny_perfect_count'])
    perfect_count = int(request.form['perfect_count'])
    near_count = int(request.form['near_count'])
    miss_count = int(request.form['miss_count'])
    health = int(request.form['health'])
    modifier = int(request.form['modifier'])
    beyond_gauge = int(request.form['beyond_gauge'])
    clear_type = int(request.form['clear_type'])
    submission_hash = request.form['submission_hash']

    # 增加成绩校验
    if not server.arcscore.arc_score_check(user_id, song_id, difficulty, score, shiny_perfect_count, perfect_count, near_count, miss_count, health, modifier, beyond_gauge, clear_type, song_token, song_hash, submission_hash):
        return error_return(107)

    r, re = server.arcscore.arc_score_post(user_id, song_id, difficulty, score, shiny_perfect_count,
                                           perfect_count, near_count, miss_count, health, modifier, beyond_gauge, clear_type)
    if re:
        return jsonify({
            "success": True,
            "value": re
        })
    else:
        return error_return(108)


# 成绩上传所需的token，显然我不想验证
@app.route(add_url_prefix('/score/token'), methods=['GET'])
def score_token():
    return jsonify({
        "success": True,
        "value": {
            "token": "1145141919810"
        }
    })


# 世界模式成绩上传所需的token，无验证
@app.route(add_url_prefix('/score/token/world'), methods=['GET'])
@server.auth.auth_required(request)
def score_token_world(user_id):
    args = request.args
    r = server.arcworld.play_world_song(user_id, args)
    if r:
        return jsonify({
            "success": True,
            "value": r
        })
    else:
        return error_return(108)


@app.route(add_url_prefix('/user/me/save'), methods=['GET'])  # 从云端同步
@server.auth.auth_required(request)
def cloud_get(user_id):
    r = server.arcscore.arc_all_get(user_id)
    if r is not None:
        return jsonify({
            "success": True,
            "value": r
        })
    else:
        return error_return(108)


@app.route(add_url_prefix('/user/me/save'), methods=['POST'])  # 向云端同步
@server.auth.auth_required(request)
def cloud_post(user_id):
    scores_data = request.form['scores_data']
    clearlamps_data = request.form['clearlamps_data']
    clearedsongs_data = request.form['clearedsongs_data']
    unlocklist_data = request.form['unlocklist_data']
    installid_data = request.form['installid_data']
    devicemodelname_data = request.form['devicemodelname_data']
    story_data = request.form['story_data']

    server.arcscore.arc_all_post(user_id, scores_data, clearlamps_data, clearedsongs_data,
                                 unlocklist_data, installid_data, devicemodelname_data, story_data)
    return jsonify({
        "success": True,
        "value": {
            "user_id": user_id
        }
    })


@app.route(add_url_prefix('/purchase/me/redeem'), methods=['POST'])  # 兑换码
@server.auth.auth_required(request)
def redeem(user_id):
    code = request.form['code']
    fragment, error_code = server.arcpurchase.claim_user_redeem(
        user_id, code)
    if not error_code:
        if fragment > 0:
            return jsonify({
                "success": True,
                "value": {"coupon": "fragment"+str(fragment)}
            })
        else:
            return jsonify({
                "success": True,
                "value": {"coupon": ""}
            })
    else:
        return error_return(error_code)


# 礼物确认
@app.route(add_url_prefix('/present/me/claim/<present_id>'), methods=['POST'])
@server.auth.auth_required(request)
def claim_present(user_id, present_id):
    flag = server.arcpurchase.claim_user_present(user_id, present_id)
    if flag:
        return jsonify({
            "success": True
        })
    else:
        return error_return(108)


# 购买体力
@app.route(add_url_prefix('/purchase/me/stamina/<buy_stamina_type>'), methods=['POST'])
@server.auth.auth_required(request)
def purchase_stamina(user_id, buy_stamina_type):

    if buy_stamina_type == 'fragment':
        r, error_code = server.arcworld.buy_stamina_by_fragment(user_id)
    else:
        return error_return(108)

    if error_code:
        return error_return(error_code)
    else:
        if r:
            return jsonify({
                "success": True,
                "value": r
            })
        else:
            return error_return(108)


# 购买，world模式boost
@app.route(add_url_prefix('/purchase/me/item'), methods=['POST'])
@server.auth.auth_required(request)
def prog_boost(user_id):
    re = {"success": False}
    if 'item_id' in request.form:
        if request.form['item_id'] == 'prog_boost_300':
            ticket, error_code = server.arcpurchase.get_prog_boost(user_id)
            if error_code:
                return error_return(error_code)

            re = {
                "success": True,
                "value": {'ticket': ticket}
            }

        elif request.form['item_id'] == 'stamina6':
            r, error_code = server.arcworld.buy_stamina_by_ticket(user_id)
            if error_code:
                return error_return(error_code)

            re = {
                "success": True,
                "value": r
            }
    return jsonify(re)


@app.route(add_url_prefix('/purchase/me/pack'), methods=['POST'])  # 曲包和单曲购买
@server.auth.auth_required(request)
def pack(user_id):
    if 'pack_id' in request.form:
        return jsonify(server.arcpurchase.buy_thing(user_id, request.form['pack_id']))
    if 'single_id' in request.form:
        return jsonify(server.arcpurchase.buy_thing(user_id, request.form['single_id']))

    return jsonify({"success": True})


# 单曲购买信息获取
@app.route(add_url_prefix('/purchase/bundle/single'), methods=['GET'])
def single():
    return jsonify({
        "success": True,
        "value": server.arcpurchase.get_single_purchase()
    })


@app.route(add_url_prefix('/world/map/me'), methods=['GET'])  # 获得世界模式信息，所有地图
@server.auth.auth_required(request)
def world_all(user_id):
    return jsonify({
        "success": True,
        "value": {
            "current_map": server.arcworld.get_current_map(user_id),
            "user_id": user_id,
            "maps": server.arcworld.get_world_all(user_id)
        }
    })


@app.route(add_url_prefix('/world/map/me'), methods=['POST'])  # 进入地图
@server.auth.auth_required(request)
def world_in(user_id):
    map_id = request.form['map_id']
    flag = server.arcworld.unlock_user_world(user_id, map_id)
    return jsonify({
        "success": flag,
        "value": server.arcworld.get_user_world(user_id, map_id)
    })


# 获得单个地图完整信息
@app.route(add_url_prefix('/world/map/me/<map_id>'), methods=['GET'])
@server.auth.auth_required(request)
def world_one(user_id, map_id):
    server.arcworld.change_user_current_map(user_id, map_id)
    return jsonify({
        "success": True,
        "value": {
            "user_id": user_id,
            "current_map": map_id,
            "maps": [server.arcworld.get_user_world_info(user_id, map_id)]
        }
    })


@app.route(add_url_prefix('/serve/download/me/song'), methods=['GET'])  # 歌曲下载
@server.auth.auth_required(request)
def download_song(user_id):
    song_ids = request.args.getlist('sid')
    if server.arcdownload.is_able_download(user_id):
        re = {}
        if not song_ids:
            re = server.arcdownload.get_all_songs(user_id)
        else:
            re = server.arcdownload.get_some_songs(user_id, song_ids)

        return jsonify({
            "success": True,
            "value": re
        })
    else:
        return error_return(903)


@app.route('/download/<path:file_path>', methods=['GET'])  # 下载
def download(file_path):
    try:
        t = request.args.get('t')
        message = server.arcdownload.is_token_able_download(t)
        if message == 0:
            path = os.path.join('./database/songs', file_path)
            if os.path.isfile(path) and not('../' in path or '..\\' in path):
                return send_from_directory('./database/songs', file_path, as_attachment=True)
            else:
                return error_return(109)
        else:
            return error_return(message)
    except:
        return error_return(108)


# 创建房间
@app.route(add_url_prefix('/multiplayer/me/room/create'), methods=['POST'])
@server.auth.auth_required(request)
def room_create(user_id):
    return error_return(151)
    # return jsonify({
    #     "success": True,
    #     "value": {
    #         "roomCode": "Fuck616",
    #         "roomId": "16465282253677196096",
    #         "token": "16465282253677196096",
    #         "key": "czZNUmivWm6c3SpMaPIXcA==",
    #         "playerId": "12753",
    #         "userId": user_id,
    #         "endPoint": "192.168.1.200",
    #         "port": 10900,
    #         "orderedAllowedSongs": "9w93DwcH93AA8HcPAAAHAHcAAHBwAABwcAAAAHB3AAAAcAcAAHAAAHAAAAB3BwD3AAAABwAAAAAAAAAAAAAAAAAAAAAAAAAHAHAHBwcAAAAAcHd3cAAAAAAHBwcAAAAAAAAAAAAHdwAHAAAAcAdwBwAAAAAAdwcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
    #     }
    # })


# 加入房间
@app.route(add_url_prefix('/multiplayer/me/room/join/<room_code>'), methods=['POST'])
@server.auth.auth_required(request)
def room_join(user_id, room_code):
    return error_return(151)


@app.route(add_url_prefix('/multiplayer/me/update'), methods=['POST'])  # ？
@server.auth.auth_required(request)
def multiplayer_update(user_id):
    return error_return(151)


@app.route(add_url_prefix('/user/me/request_delete'), methods=['POST'])  # 删除账号
@server.auth.auth_required(request)
def user_delete(user_id):
    return error_return(151)


# 三个设置，写在最后降低优先级
@app.route(add_url_prefix('/<path:path>', True), methods=['POST'])
@server.auth.auth_required(request)
def sys_set(user_id, path):
    set_arg = path[5:]
    value = request.form['value']
    server.setme.arc_sys_set(user_id, value, set_arg)
    r = server.info.arc_aggregate_small(user_id)
    r['value'] = r['value'][0]['value']
    return jsonify(r)


def main():
    if Config.SSL_CERT and Config.SSL_KEY:
        app.run(Config.HOST, Config.PORT, ssl_context=(
            Config.SSL_CERT, Config.SSL_KEY))
    else:
        app.run(Config.HOST, Config.PORT)


if __name__ == '__main__':
    main()


# Made By Lost  2020.9.11
