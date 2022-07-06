# encoding: utf-8

import os
import sys
from logging.config import dictConfig
from multiprocessing import Process, set_start_method

from flask import Flask, request, send_from_directory

import api
import server
import server.init
import web.index
import web.login
from core.constant import Constant
from core.download import UserDownload, initialize_songfile
from core.error import ArcError
from core.sql import Connect
from server.func import error_return
from setting import Config

app = Flask(__name__)
wsgi_app = app.wsgi_app

os.chdir(sys.path[0])  # 更改工作路径，以便于愉快使用相对路径

app.config.from_mapping(SECRET_KEY=Config.SECRET_KEY)
app.config['SESSION_TYPE'] = 'filesystem'
app.register_blueprint(web.login.bp)
app.register_blueprint(web.index.bp)
app.register_blueprint(api.bp)
app.register_blueprint(server.bp)


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
    with Connect() as c:
        try:
            x = UserDownload(c)
            x.file_path = file_path
            x.select_from_token(request.args.get('t'))
            if x.is_limited:
                raise ArcError('You have reached the download limit.', 903)
            if x.is_valid:
                x.insert_user_download()
                return send_from_directory(Constant.SONG_FILE_FOLDER_PATH, file_path, as_attachment=True)
        except ArcError as e:
            return error_return(e)
    return error_return()


def tcp_server_run():
    if Config.SSL_CERT and Config.SSL_KEY:
        app.run(Config.HOST, Config.PORT, ssl_context=(
            Config.SSL_CERT, Config.SSL_KEY))
    else:
        app.run(Config.HOST, Config.PORT)


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

    app.logger.info("Start to initialize song data...")
    try:
        initialize_songfile()
        app.logger.info('Complete!')
    except:
        app.logger.warning('Initialization error!')

    if Config.UDP_PORT and Config.UDP_PORT != '':
        from server.multiplayer import conn2
        from udpserver.udp_main import link_play
        process = [Process(target=link_play, args=(
            conn2, Config.HOST, int(Config.UDP_PORT)))]
        [p.start() for p in process]
        app.logger.info("UDP server is running...")
        tcp_server_run()
        [p.join() for p in process]
    else:
        tcp_server_run()


if __name__ == '__main__':
    set_start_method("spawn")
    main()


# Made By Lost  2020.9.11
