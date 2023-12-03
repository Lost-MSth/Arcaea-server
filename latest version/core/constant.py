from .config_manager import Config

ARCAEA_SERVER_VERSION = 'v2.11.2.7'
ARCAEA_LOG_DATBASE_VERSION = 'v1.1'


class Constant:

    BAN_TIME = [1, 3, 7, 15, 31]

    MAX_STAMINA = 12

    STAMINA_RECOVER_TICK = 1800000

    COURSE_STAMINA_COST = 4

    CORE_EXP = 250

    LEVEL_STEPS = {1: 0, 2: 50, 3: 100, 4: 150, 5: 200, 6: 300, 7: 450, 8: 650, 9: 900, 10: 1200, 11: 1600, 12: 2100, 13: 2700, 14: 3400, 15: 4200, 16: 5100,
                   17: 6100, 18: 7200, 19: 8500, 20: 10000, 21: 11500, 22: 13000, 23: 14500, 24: 16000, 25: 17500, 26: 19000, 27: 20500, 28: 22000, 29: 23500, 30: 25000}

    WORLD_VALUE_NAME_ENUM = ['frag', 'prog', 'over']

    FREE_PACK_NAME = 'base'
    SINGLE_PACK_NAME = 'single'

    ETO_UNCAP_BONUS_PROGRESS = 7
    LUNA_UNCAP_BONUS_PROGRESS = 7
    AYU_UNCAP_BONUS_PROGRESS = 5
    SKILL_FATALIS_WORLD_LOCKED_TIME = 3600000
    SKILL_MIKA_SONGS = ['aprilshowers', 'seventhsense', 'oshamascramble',
                        'amazingmightyyyy', 'cycles', 'maxrage', 'infinity', 'temptation']

    MAX_FRIEND_COUNT = Config.MAX_FRIEND_COUNT

    MY_RANK_MAX_LOCAL_POSITION = 5
    MY_RANK_MAX_GLOBAL_POSITION = 9999

    BEST30_WEIGHT = Config.BEST30_WEIGHT
    RECENT10_WEIGHT = Config.RECENT10_WEIGHT

    WORLD_MAP_FOLDER_PATH = Config.WORLD_MAP_FOLDER_PATH
    SONG_FILE_FOLDER_PATH = Config.SONG_FILE_FOLDER_PATH
    SONGLIST_FILE_PATH = Config.SONGLIST_FILE_PATH
    SQLITE_DATABASE_PATH = Config.SQLITE_DATABASE_PATH
    SQLITE_LOG_DATABASE_PATH = Config.SQLITE_LOG_DATABASE_PATH

    DOWNLOAD_TIMES_LIMIT = Config.DOWNLOAD_TIMES_LIMIT
    DOWNLOAD_TIME_GAP_LIMIT = Config.DOWNLOAD_TIME_GAP_LIMIT
    DOWNLOAD_LINK_PREFIX = Config.DOWNLOAD_LINK_PREFIX

    LINKPLAY_UNLOCK_LENGTH = 512  # Units: bytes
    LINKPLAY_TIMEOUT = 5  # Units: seconds

    LINKPLAY_HOST = '127.0.0.1' if Config.SET_LINKPLAY_SERVER_AS_SUB_PROCESS else Config.LINKPLAY_HOST
    LINKPLAY_TCP_PORT = Config.LINKPLAY_TCP_PORT
    LINKPLAY_UDP_PORT = Config.LINKPLAY_UDP_PORT
    LINKPLAY_AUTHENTICATION = Config.LINKPLAY_AUTHENTICATION
    LINKPLAY_TCP_SECRET_KEY = Config.LINKPLAY_TCP_SECRET_KEY
    LINKPLAY_TCP_MAX_LENGTH = 0x0FFFFFFF

    # Well, I can't say a word when I see this.
    FINALE_SWITCH = [
        (0x0015F0, 0x00B032), (0x014C9A, 0x014408), (0x062585, 0x02783B),
        (0x02429E, 0x0449A4), (0x099C9C,
                               0x07CFB4), (0x0785BF, 0x019B2C),
        (0x0EFF43, 0x0841BF), (0x07C88B,
                               0x0DE9FC), (0x000778, 0x064815),
        (0x0E62E3, 0x079F02), (0x0188FE,
                               0x0923EB), (0x0E06CD, 0x0E1A26),
        (0x00669E, 0x0C8BE1), (0x0BEB7A, 0x05D635), (0x040E6F,
                                                     0x0B465B), (0x0568EC, 0x07ED2B),
        (0x189614, 0x00A3D2), (0x62D98D,
                               0x45E5CA), (0x6D8769, 0x473F0E),
        (0x922E4F, 0x667D6C), (0x021F5C,
                               0x298839), (0x2A1201, 0x49FB7E),
        (0x158B81, 0x8D905D), (0x2253A5,
                               0x7E7067), (0x3BEF79, 0x9368E9),
        (0x00669E, 0x0C8BE1), (0x0BEB7A,
                               0x05D635), (0x040E6F, 0x0B465B),
        (0x756276, 0x55CD57), (0x130055, 0x7010E7), (0x55E28D,
                                                     0x4477FB), (0x5E99CB, 0x81060E),
        (0x7F43A4, 0x8FEC56), (0x69412F,
                               0x32735C), (0x8FF846, 0x14B5A1),
        (0x8716BE, 0x5C78BE), (0x62ED0E,
                               0x348E4B), (0x4B20C8, 0x56E0C3),
        (0x0AF6BC, 0x872441), (0x8825BC,
                               0x94B315), (0x792784, 0x5B2C8E),
        (0x1AE3A7, 0x688E97), (0x0D630F,
                               0x06BE78), (0x792784, 0x5B2C8E),
        (0x314869, 0x41CCC1), (0x311934, 0x24DD94), (0x190EDB,
                                                     0x33993D), (0x25F5C5, 0x15FAE6),
        (0x18CA10, 0x1B761A), (0x51BE82,
                               0x120089), (0x51D3B6, 0x2C29A2),
        (0x402075, 0x4A89B2), (0x00697B,
                               0x0E6497), (0x6D872D, 0x618AE7),
        (0x3DC0BE, 0x4E2AC8), (0x8C6ACF,
                               0x9776CF), (0x84673B, 0x5CA060),
        (0x4B05EC, 0x97FDFE), (0x207258,
                               0x02BB9B), (0x20A9EE, 0x1BA4BB),
        (0x503D21, 0x6A41D0), (0x1C256C,
                               0x6DD3BC), (0x6E4E0C, 0x89FDAA), (0x3C5F95, 0x3BA786),
        (0XFEA5, 0x2e4ca), (0X7BF653, 0x4befd11), (0X46BEA7B,
                                                   0x11d3684), (0X8BFB04, 0xa83d6c1),
        (0X5D6FC5, 0xab97ef), (0X237206D, 0xdfef2), (0XA3DEE,
                                                     0x6CB300), (0XA35687B, 0xE456CDEA)
    ]

    DATABASE_MIGRATE_TABLES = ['user', 'friend', 'best_score', 'recent30', 'user_world', 'item', 'user_item', 'purchase', 'purchase_item', 'user_save',
                               'login', 'present', 'user_present', 'present_item', 'redeem', 'user_redeem', 'redeem_item', 'api_login', 'chart', 'user_course', 'user_char', 'user_role']

    LOG_DATABASE_MIGRATE_TABLES = ['cache', 'user_score', 'user_rating']

    UPDATE_WITH_NEW_CHARACTER_DATA = Config.UPDATE_WITH_NEW_CHARACTER_DATA
