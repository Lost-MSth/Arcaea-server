# encoding: utf-8

import os
from importlib import import_module

from core.config_manager import Config, ConfigManager

if os.path.exists('config.py') or os.path.exists('config'):
    # 导入用户自定义配置
    ConfigManager.load(import_module('config').Config)

if Config.DEPLOY_MODE == 'gevent':
    # 异步
    from gevent import monkey
    monkey.patch_all()


import sys
from logging.config import dictConfig
from multiprocessing import Process, set_start_method
from traceback import format_exc

from flask import Flask, make_response, request, send_from_directory

import api
import server
import web.index
import web.login
# import webapi
from core.constant import Constant
from core.download import UserDownload
from core.error import ArcError, NoAccess, RateLimit
from core.init import FileChecker
from core.sql import Connect
from server.func import error_return

app = Flask(__name__)

if Config.USE_PROXY_FIX:
    # 代理修复
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
if Config.USE_CORS:
    # 服务端跨域
    from flask_cors import CORS
    CORS(app, supports_credentials=True)


os.chdir(sys.path[0])  # 更改工作路径，以便于愉快使用相对路径


app.config.from_mapping(SECRET_KEY=Config.SECRET_KEY)
app.config['SESSION_TYPE'] = 'filesystem'
app.register_blueprint(web.login.bp)
app.register_blueprint(web.index.bp)
app.register_blueprint(api.bp)
app.register_blueprint(server.bp)
# app.register_blueprint(webapi.bp)


@app.route('/')
def hello():
    return "Hello World!"


@app.route('/favicon.ico', methods=['GET'])  # 图标
def favicon():
    # Pixiv ID: 82374369
    # 我觉得这张图虽然并不是那么精细，但很有感觉，色彩的强烈对比下给人带来一种惊艳
    # 然后在压缩之下什么也看不清了:(

    return app.send_static_file('favicon.ico')


@app.route('/download/<path:file_path>', methods=['GET'])  # 下载
def download(file_path):
    with Connect(in_memory=True) as c:
        try:
            x = UserDownload(c)
            x.token = request.args.get('t')
            x.song_id, x.file_name = file_path.split('/', 1)
            x.select_for_check()
            if x.is_limited:
                raise RateLimit('You have reached the download limit.', 903)
            if not x.is_valid:
                raise NoAccess('Expired token.')
            x.download_hit()
            if Config.DOWNLOAD_USE_NGINX_X_ACCEL_REDIRECT:
                # nginx X-Accel-Redirect
                response = make_response()
                response.headers['Content-Type'] = 'application/octet-stream'
                response.headers['X-Accel-Redirect'] = Config.NGINX_X_ACCEL_REDIRECT_PREFIX + file_path
                return response
            return send_from_directory(Constant.SONG_FILE_FOLDER_PATH, file_path, as_attachment=True, conditional=True)
        except ArcError as e:
            if Config.ALLOW_WARNING_LOG:
                app.logger.warning(format_exc())
            return error_return(e)
    return error_return()


if Config.DEPLOY_MODE == 'waitress':
    # 给waitress加个日志
    @app.after_request
    def after_request(response):
        app.logger.info(
            f'{request.remote_addr} - - {request.method} {request.path} {response.status_code}')
        return response

# @app.before_request
# def before_request():
#     print(request.path)
#     print(request.headers)
#     print(request.data)


def tcp_server_run():
    if Config.DEPLOY_MODE == 'gevent':
        # 异步 gevent WSGI server
        host_port = (Config.HOST, Config.PORT)
        app.logger.info('Running gevent WSGI server... (%s:%s)' % host_port)
        from gevent.pywsgi import WSGIServer
        WSGIServer(host_port, app, log=app.logger).serve_forever()
    elif Config.DEPLOY_MODE == 'waitress':
        # waitress WSGI server
        import logging
        from waitress import serve
        logger = logging.getLogger('waitress')
        logger.setLevel(logging.INFO)
        serve(app, host=Config.HOST, port=Config.PORT)
    else:
        if Config.SSL_CERT and Config.SSL_KEY:
            app.run(Config.HOST, Config.PORT, ssl_context=(
                Config.SSL_CERT, Config.SSL_KEY))
        else:
            app.run(Config.HOST, Config.PORT)


def generate_log_file_dict(level: str, filename: str) -> dict:
    return {
        "class": "logging.handlers.RotatingFileHandler",
        "maxBytes": 1024 * 1024,
        "backupCount": 1,
        "encoding": "utf-8",
        "level": level,
        "formatter": "default",
        "filename": filename
    }


def main():
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
            "error_file": generate_log_file_dict('ERROR', './log/error.log')
        },
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
            }
        }
    }
    if Config.ALLOW_INFO_LOG:
        log_dict['root']['handlers'].append('info_file')
        log_dict['handlers']['info_file'] = generate_log_file_dict(
            'INFO', './log/info.log')
    if Config.ALLOW_WARNING_LOG:
        log_dict['root']['handlers'].append('warning_file')
        log_dict['handlers']['warning_file'] = generate_log_file_dict(
            'WARNING', './log/warning.log')

    dictConfig(log_dict)

    Connect.logger = app.logger
    if not FileChecker(app.logger).check_before_run():
        app.logger.error('Some errors occurred. The server will not run.')
        input('Press ENTER key to exit.')
        sys.exit()

    if Config.LINKPLAY_HOST and Config.SET_LINKPLAY_SERVER_AS_SUB_PROCESS:
        from linkplay_server import link_play
        process = [Process(target=link_play, args=(
            Config.LINKPLAY_HOST, int(Config.LINKPLAY_UDP_PORT), int(Config.LINKPLAY_TCP_PORT)))]
        [p.start() for p in process]
        app.logger.info(
            f"Link Play UDP server is running on {Config.LINKPLAY_HOST}:{Config.LINKPLAY_UDP_PORT} ...")
        app.logger.info(
            f"Link Play TCP server is running on {Config.LINKPLAY_HOST}:{Config.LINKPLAY_TCP_PORT} ...")
        tcp_server_run()
        [p.join() for p in process]
    else:
        tcp_server_run()


if __name__ == '__main__':
    set_start_method("spawn")
    main()


# Made By Lost  2020.9.11
