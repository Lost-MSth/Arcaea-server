class Config:
    '''
    Default config
    '''

    HOST = '0.0.0.0'
    PORT = 80

    DEPLOY_MODE = 'flask_multithread'
    USE_PROXY_FIX = False
    USE_CORS = False

    SONG_FILE_HASH_PRE_CALCULATE = True

    GAME_API_PREFIX = '/evolution/23'

    ALLOW_APPVERSION = []  # list[str]

    SET_LINKPLAY_SERVER_AS_SUB_PROCESS = True

    LINKPLAY_HOST = '0.0.0.0'
    LINKPLAY_UDP_PORT = 10900
    LINKPLAY_TCP_PORT = 10901
    LINKPLAY_AUTHENTICATION = 'my_link_play_server'
    LINKPLAY_DISPLAY_HOST = ''
    LINKPLAY_TCP_SECRET_KEY = '1145141919810'

    SSL_CERT = ''
    SSL_KEY = ''

    IS_APRILFOOLS = True

    WORLD_RANK_MAX = 200

    AVAILABLE_MAP = []  # list[str]

    USERNAME = 'admin'
    PASSWORD = 'admin'

    SECRET_KEY = '1145141919810'

    API_TOKEN = ''

    DOWNLOAD_LINK_PREFIX = ''

    DOWNLOAD_USE_NGINX_X_ACCEL_REDIRECT = False
    NGINX_X_ACCEL_REDIRECT_PREFIX = '/nginx_download/'

    DOWNLOAD_TIMES_LIMIT = 3000
    DOWNLOAD_TIME_GAP_LIMIT = 1000

    DOWNLOAD_FORBID_WHEN_NO_ITEM = False

    LOGIN_DEVICE_NUMBER_LIMIT = 1
    ALLOW_LOGIN_SAME_DEVICE = False
    ALLOW_BAN_MULTIDEVICE_USER_AUTO = True

    ALLOW_SCORE_WITH_NO_SONG = True

    ALLOW_INFO_LOG = False
    ALLOW_WARNING_LOG = False

    DEFAULT_MEMORIES = 0

    UPDATE_WITH_NEW_CHARACTER_DATA = True

    CHARACTER_FULL_UNLOCK = True
    WORLD_SONG_FULL_UNLOCK = True
    WORLD_SCENERY_FULL_UNLOCK = True

    SAVE_FULL_UNLOCK = False

    # ------------------------------------------

    # You can change this to make another PTT mechanism.
    BEST30_WEIGHT = 1 / 40
    RECENT10_WEIGHT = 1 / 40

    MAX_FRIEND_COUNT = 50

    WORLD_MAP_FOLDER_PATH = './database/map/'
    SONG_FILE_FOLDER_PATH = './database/songs/'
    SONGLIST_FILE_PATH = './database/songs/songlist'
    SQLITE_DATABASE_PATH = './database/arcaea_database.db'
    SQLITE_DATABASE_BACKUP_FOLDER_PATH = './database/backup/'
    DATABASE_INIT_PATH = './database/init/'
    SQLITE_LOG_DATABASE_PATH = './database/arcaea_log.db'

    GAME_LOGIN_RATE_LIMIT = '30/5 minutes'
    API_LOGIN_RATE_LIMIT = '10/5 minutes'


class ConfigManager:

    @staticmethod
    def load(config) -> None:
        for k, v in config.__dict__.items():
            if k.startswith('__') or k.endswith('__'):
                continue
            if hasattr(Config, k):
                setattr(Config, k, v)
