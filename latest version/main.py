# encoding: utf-8

import os
import sys
from importlib import import_module
from importlib import util as importlib_util
from logging.config import dictConfig
from multiprocessing import Process, active_children, current_process, set_start_method
from traceback import format_exc

from core.config_manager import Config, ConfigManager


def _is_path(value: str) -> bool:
    if value.endswith('.py'):
        return True
    if os.path.isabs(value):
        return True
    if os.path.sep in value:
        return True
    if os.path.altsep and os.path.altsep in value:
        return True
    return False


def _load_config_from_path(config_path: str):
    config_path = os.path.abspath(config_path)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f'Config path not found: {config_path}')
    spec = importlib_util.spec_from_file_location('user_config', config_path)
    if spec is None or spec.loader is None:
        raise ImportError(f'Cannot import config from path: {config_path}')
    module = importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, 'Config'):
        raise AttributeError(f'Config class not found in: {config_path}')
    return module.Config


def _load_user_config():
    config_target = os.getenv('ARCAEA_SERVER_CONFIG')
    if config_target:
        if _is_path(config_target):
            return _load_config_from_path(config_target)
        return import_module(config_target).Config
    if os.path.exists('config.py') or os.path.exists('config'):
        return import_module('config').Config
    return None


config_class = _load_user_config()
if config_class:
    # 导入用户自定义配置
    ConfigManager.load(config_class)
    # TODO: More config file formats

if Config.DEPLOY_MODE == 'gevent':
    # 异步
    from gevent import monkey  # type: ignore
    monkey.patch_all()


def _import_after_config():
    global Flask, request
    global api, server, web
    global BundleDownload, UserDownload, ArcError, NoAccess, RateLimit
    global FileChecker, Connect, error_return, DownloadManager

    from flask import Flask, request

    import api
    import server
    import web
    import web.index
    import web.login
    from core.bundle import BundleDownload
    from core.download import DownloadManager, UserDownload
    from core.error import ArcError, NoAccess, RateLimit
    from core.init import FileChecker
    from core.sql import Connect
    from server.func import error_return

    # import webapi


_import_after_config()


app = Flask(__name__)

if Config.USE_PROXY_FIX:
    # 代理修复
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
if Config.USE_CORS:
    # 服务端跨域
    from flask_cors import CORS  # type: ignore
    CORS(app, supports_credentials=True)


os.chdir(sys.path[0])  # 更改工作路径，以便于愉快使用相对路径


app.config.from_mapping(SECRET_KEY=Config.SECRET_KEY)
app.config['SESSION_TYPE'] = 'filesystem'
app.register_blueprint(web.login.bp)
app.register_blueprint(web.index.bp)
app.register_blueprint(api.bp)
list(map(app.register_blueprint, server.get_bps()))
# app.register_blueprint(webapi.bp)


def print_message_and_exit(message: str = ''):
    if message:
        print(message)
    children = active_children()
    if children:
        for child in children:
            try:
                child.terminate()
            except Exception:
                pass
        for child in children:
            try:
                child.join(timeout=2)
            except Exception:
                pass
    input('Press ENTER key to exit.')
    sys.exit(1)


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
                raise RateLimit(
                    f'User `{x.user.user_id}` has reached the download limit.', 903)
            if not x.is_valid:
                raise NoAccess('Expired token.')
            x.download_hit()
            return DownloadManager(file_path).get_response()
        except ArcError as e:
            if Config.ALLOW_WARNING_LOG:
                app.logger.warning(format_exc())
            return error_return(e)
    return error_return()


@app.route('/bundle_download/<string:token>', methods=['GET'])  # 热更新下载
def bundle_download(token: str):
    with Connect(in_memory=True) as c_m:
        try:
            file_path = BundleDownload(c_m).get_path_by_token(
                token, request.remote_addr)
            return DownloadManager(file_path, is_bundle=True).get_response()
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
        from gevent.pywsgi import WSGIServer  # type: ignore
        WSGIServer(host_port, app, log=app.logger).serve_forever()
    elif Config.DEPLOY_MODE == 'waitress':
        # waitress WSGI server
        import logging

        from waitress import serve  # type: ignore
        logger = logging.getLogger('waitress')
        logger.setLevel(logging.INFO)
        serve(app, host=Config.HOST, port=Config.PORT,
              clear_untrusted_proxy_headers=not Config.USE_PROXY_FIX)
    elif Config.DEPLOY_MODE == 'gunicorn':
        # Gunicorn 只能在类 Unix 系统上使用
        if os.name == 'nt':
            app.logger.error(
                'Gunicorn is not supported on Windows. Use waitress instead.')
            print_message_and_exit()
        try:
            from gunicorn.app.base import BaseApplication  # type: ignore
        except Exception:
            app.logger.error(
                'Gunicorn is not installed. Install it with `pip install gunicorn`.')
            print_message_and_exit()

        class GunicornApplication(BaseApplication):
            def __init__(self, application, options=None):
                self.options = options or {}
                self.application = application
                super().__init__()

            def load_config(self):
                for key, value in self.options.items():
                    if value is None:
                        continue
                    self.cfg.set(key, value)

            def load(self):
                return self.application

        GunicornApplication(app, Config.DEPLOY_OPTIONS['gunicorn']).run()
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


def pre_main():
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
            "error_file": generate_log_file_dict('ERROR', f'{Config.LOG_FOLDER_PATH}/error.log')
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
            'INFO', f'{Config.LOG_FOLDER_PATH}/info.log')
    if Config.ALLOW_WARNING_LOG:
        log_dict['root']['handlers'].append('warning_file')
        log_dict['handlers']['warning_file'] = generate_log_file_dict(
            'WARNING', f'{Config.LOG_FOLDER_PATH}/warning.log')

    dictConfig(log_dict)

    Connect.logger = app.logger
    if not FileChecker(app.logger).check_before_run():
        app.logger.error('Some errors occurred. The server will not run.')
        print_message_and_exit()


def main():
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


# must run for init
# this ensures avoiding duplicate init logs for some reason
if current_process().name == 'MainProcess':
    pre_main()

if __name__ == '__main__':
    set_start_method("spawn")
    main()


# Made By Lost  2020.9.11
