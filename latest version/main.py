# encoding: utf-8

from flask import Flask, request, jsonify, make_response, send_from_directory
from logging.config import dictConfig
from setting import Config
import base64
import server.auth
import server.info
import server.setme
import server.arcscore
import web.login
import web.index
import server.arcworld
import server.arcdownload
import server.arcpurchase
import os
import sys


app = Flask(__name__)
wsgi_app = app.wsgi_app


def error_return(error_code):  # 错误返回
    # -7 处理交易时发生了错误
    # -5 所有的曲目都已经下载完毕
    # -4 您的账号已在别处登录
    # -3 无法连接至服务器
    # 2 Arcaea服务器正在维护
    # 5 请更新Arcaea到最新版本
    # 100 无法在此ip地址下登录游戏
    # 101 用户名占用
    # 102 电子邮箱已注册
    # 103 已有一个账号由此设备创建
    # 104 用户名密码错误
    # 105 24小时内登入两台设备
    # 106 账户冻结
    # 107 你没有足够的体力
    # 113 活动已结束
    # 114 该活动已结束，您的成绩不会提交
    # 120 封号警告
    # 121 账户冻结
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
    # 9801 下载歌曲时发生问题，请再试一次
    # 9802 保存歌曲时发生问题，请检查设备空间容量
    # 9905 没有在云端发现任何数据
    # 9907 更新数据时发生了问题
    # 9908 服务器只支持最新的版本，请更新Arcaea
    # 其它 发生未知错误
    return jsonify({
        "success": False,
        "error_code": error_code
    })


@app.route('/')
def hello():
    return "Hello World!"


@app.route('/favicon.ico', methods=['GET'])  # 图标
def favicon():
    # Pixiv ID: 82374369
    # 我觉得这张图虽然并不是那么精细，但很有感觉，色彩的强烈对比下给人带来一种惊艳
    # 然后在压缩之下什么也看不清了:(

    return app.send_static_file('favicon.ico')


@app.route('/latte/13/auth/login', methods=['POST'])  # 登录接口
def login():
    headers = request.headers
    id_pwd = headers['Authorization']
    id_pwd = base64.b64decode(id_pwd[6:]).decode()
    name, password = id_pwd.split(':', 1)
    if 'DeviceId' in headers:
        device_id = headers['DeviceId']
    else:
        device_id = 'low_version'

    token, error_code = server.auth.arc_login(name, password, device_id)
    if not error_code:
        r = {"success": True, "token_type": "Bearer"}
        r['access_token'] = token
        return jsonify(r)
    else:
        return error_return(error_code)


@app.route('/latte/13/user/', methods=['POST'])  # 注册接口
def register():
    name = request.form['name']
    password = request.form['password']
    if 'device_id' in request.form:
        device_id = request.form['device_id']
    else:
        device_id = 'low_version'

    user_id, token, error_code = server.auth.arc_register(
        name, password, device_id)
    if user_id is not None:
        r = {"success": True, "value": {
            'user_id': user_id, 'access_token': token}}
        return jsonify(r)
    else:
        return error_return(error_code)  # 应该是101，用户名被占用，毕竟电子邮箱没记录


# 集成式请求，没想到什么好办法处理，就先这样写着
@app.route('/latte/13/compose/aggregate', methods=['GET'])
@server.auth.auth_required(request)
def aggregate(user_id):
    calls = request.args.get('calls')
    if calls == '[{ "endpoint": "/user/me", "id": 0 }]':  # 极其沙雕的判断，我猜get的参数就两种
        r = server.info.arc_aggregate_small(user_id)
    else:
        r = server.info.arc_aggregate_big(user_id)
    return jsonify(r)


@app.route('/latte/13/user/me/character', methods=['POST'])  # 角色切换
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


@app.route('/latte/<path:path>/toggle_uncap', methods=['POST'])  # 角色觉醒切换
@server.auth.auth_required(request)
def character_uncap(user_id, path):
    while '//' in path:
        path = path.replace('//', '/')
    character_id = int(path[21:])
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


@app.route('/latte/13/friend/me/add', methods=['POST'])  # 加好友
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


@app.route('/latte/13/friend/me/delete', methods=['POST'])  # 删好友
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


@app.route('/latte/13/score/song/friend', methods=['GET'])  # 好友排名，默认最多50
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


@app.route('/latte/13/score/song/me', methods=['GET'])  # 我的排名，默认最多20
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


@app.route('/latte/13/score/song', methods=['GET'])  # TOP20
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


@app.route('/latte/13/score/song', methods=['POST'])  # 成绩上传
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
    if r is not None:
        if re:
            return jsonify({
                "success": True,
                "value": re
            })
        else:
            return jsonify({
                "success": True,
                "value": {"user_rating": r}
            })
    else:
        return error_return(108)


@app.route('/latte/13/score/token', methods=['GET'])  # 成绩上传所需的token，显然我不想验证
def score_token():
    return jsonify({
        "success": True,
        "value": {
            "token": "1145141919810"
        }
    })


# 世界模式成绩上传所需的token，无验证
@app.route('/latte/13/score/token/world', methods=['GET'])
@server.auth.auth_required(request)
def score_token_world(user_id):
    args = request.args
    server.arcworld.play_world_song(user_id, args)
    return jsonify({
        "success": True,
        "value": {
            "stamina": 12,
            "max_stamina_ts": 1599547603825,
            "token": "13145201919810"
        }
    })


@app.route('/latte/13/user/me/save', methods=['GET'])  # 从云端同步
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


@app.route('/latte/13/user/me/save', methods=['POST'])  # 向云端同步
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


@app.route('/latte/13/purchase/me/redeem', methods=['POST'])  # 兑换码
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
@app.route('/latte/13/present/me/claim/<present_id>', methods=['POST'])
@server.auth.auth_required(request)
def claim_present(user_id, present_id):
    flag = server.arcpurchase.claim_user_present(user_id, present_id)
    if flag:
        return jsonify({
            "success": True
        })
    else:
        return error_return(108)


@app.route('/latte/13/purchase/me/item', methods=['POST'])  # 购买，world模式boost
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
    return jsonify(re)


@app.route('/latte/13/purchase/me/pack', methods=['POST'])  # 曲包和单曲购买
@server.auth.auth_required(request)
def pack(user_id):
    if 'pack_id' in request.form:
        return jsonify(server.arcpurchase.buy_pack(user_id, request.form['pack_id']))
    if 'single_id' in request.form:
        return jsonify(server.arcpurchase.buy_single(user_id, request.form['single_id']))

    return jsonify({
        "success": True
    })


@app.route('/latte/13/purchase/bundle/single', methods=['GET'])  # 单曲购买信息获取
def single():
    return jsonify({
        "success": True,
        "value": server.arcpurchase.get_single_purchase()
    })


@app.route('/latte/13/world/map/me', methods=['GET'])  # 获得世界模式信息，所有地图
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


@app.route('/latte/13/world/map/me/', methods=['POST'])  # 进入地图
@server.auth.auth_required(request)
def world_in(user_id):
    map_id = request.form['map_id']
    return jsonify({
        "success": True,
        "value": server.arcworld.get_user_world(user_id, map_id)
    })


@app.route('/latte/13/world/map/me/<map_id>', methods=['GET'])  # 获得单个地图完整信息
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


@app.route('/latte/13/serve/download/me/song', methods=['GET'])  # 歌曲下载
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


@app.route('/latte/<path:path>', methods=['POST'])  # 三个设置，写在最后降低优先级
@server.auth.auth_required(request)
def sys_set(user_id, path):
    set_arg = path[10:]
    value = request.form['value']
    server.setme.arc_sys_set(user_id, value, set_arg)
    r = server.info.arc_aggregate_small(user_id)
    r['value'] = r['value'][0]['value']
    return jsonify(r)


def main():
    os.chdir(sys.path[0])  # 更改工作路径，以便于愉快使用相对路径
    app.config.from_mapping(SECRET_KEY=Config.SECRET_KEY)
    app.config['SESSION_TYPE'] = 'filesystem'
    app.register_blueprint(web.login.bp)
    app.register_blueprint(web.index.bp)

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

    app.logger.info("Start to initialize data in 'songfile' table...")
    try:
        error = server.arcdownload.initialize_songfile()
    except:
        error = 'Something wrong.'
    if error:
        app.logger.warning(error)
    else:
        app.logger.info('Complete!')

    if Config.SSL_CERT and Config.SSL_KEY:
        app.run(Config.HOST, Config.PORT, ssl_context=(
            Config.SSL_CERT, Config.SSL_KEY))
    else:
        app.run(Config.HOST, Config.PORT)


if __name__ == '__main__':
    main()


# Made By Lost  2020.9.11
