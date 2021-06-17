class Config():
    '''
    This is the setting file. You can change some parameters here.
    '''

    '''
    --------------------
    主机的地址和端口号
    Host and port of your server
    '''
    HOST = '192.168.1.101'
    PORT = '80'
    '''
    --------------------
    '''

    '''
    --------------------
    游戏API地址前缀
    Game API's URL prefix
    '''
    GAME_API_PREFIX = '/blockchain/14'
    '''
    --------------------
    '''

    '''
    --------------------
    允许使用的游戏版本，若为空，则默认全部允许
    Allowed game versions
    If it is blank, all are allowed.
    '''
    ALLOW_APPVERSION = ['3.5.3', '3.5.3c', '3.6.2', '3.6.2c']
    '''
    --------------------
    '''

    '''
    --------------------
    SSL证书路径
    留空则使用HTTP
    SSL certificate path
    If left blank, use HTTP.
    '''
    SSL_CERT = ''  # *.pem
    SSL_KEY = ''  # *.key
    '''
    --------------------
    '''

    '''
    --------------------
    愚人节模式开关
    Switch of April Fool's Day
    '''
    IS_APRILFOOLS = True
    '''
    --------------------
    '''

    '''
    --------------------
    世界排名的最大显示数量
    The largest number of global rank
    '''
    WORLD_RANK_MAX = 200
    '''
    --------------------
    '''

    '''
    --------------------
    Web后台管理页面的用户名和密码
    Username and password of web background management page
    '''
    USERNAME = 'admin'
    PASSWORD = 'admin'
    '''
    --------------------
    '''

    '''
    --------------------
    Web后台管理页面的session秘钥，如果不知道是什么，请不要修改
    Session key of web background management page
    If you don't know what it is, please don't modify it.
    '''
    SECRET_KEY = '1145141919810'
    '''
    --------------------
    '''

    '''
    --------------------
    API接口完全控制权限Token，留空则不使用
    API interface full control permission Token
    If you don't want to use it, leave it blank.
    '''
    API_TOKEN = ''
    '''
    --------------------
    '''

    '''
    --------------------
    歌曲下载地址前缀，留空则自动获取
    Song download address prefix
    If left blank, it will be obtained automatically.
    '''
    DOWNLOAD_LINK_PREFIX = ''  # http://***.com/download/
    '''
    --------------------
    '''

    '''
    --------------------
    玩家歌曲下载的24小时次数限制，每个文件算一次
    Player's song download limit times in 24 hours, once per file
    '''
    DOWNLOAD_TIMES_LIMIT = 3000
    '''
    歌曲下载链接的有效时长，单位：秒
    Effective duration of song download link, unit: seconds
    '''
    DOWNLOAD_TIME_GAP_LIMIT = 1000
    '''
    --------------------
    '''

    '''
    --------------------
    Arcaea登录的最大允许设备数量，最小值为1
    The maximum number of devices allowed to log in Arcaea, minimum: 1
    '''
    LOGIN_DEVICE_NUMBER_LIMIT = 1
    '''
    是否允许同设备多应用共存登录
    If logging in from multiple applications on the same device is allowed
    '''
    ALLOW_LOGIN_SAME_DEVICE = False
    '''
    --------------------
    '''

    '''
    --------------------
    是否记录详细的服务器日志
    If recording detailed server logs is enabled
    '''
    ALLOW_LOG_INFO = False
    '''
    --------------------
    '''

    '''
    --------------------
    用户注册时的默认记忆源点数量
    The default amount of memories at the time of user registration
    '''
    DEFAULT_MEMORIES = 0
    '''
    --------------------
    '''

    '''
    --------------------
    是否全解锁搭档
    If unlocking all partners is enabled
    '''
    CHARACTER_FULL_UNLOCK = True
    '''
    --------------------
    '''

    '''
    --------------------
    是否全解锁世界歌曲
    If unlocking all world songs is enabled
    '''
    WORLD_SONG_FULL_UNLOCK = True
    '''
    --------------------
    '''

    '''
    --------------------
    是否全解锁世界场景
    If unlocking all world scenerys is enabled
    '''
    WORLD_SCENERY_FULL_UNLOCK = True
    '''
    --------------------
    '''

    '''
    --------------------
    是否强制使用全解锁云端存档
    If forcing full unlocked cloud save is enabled
    '''
    SAVE_FULL_UNLOCK = False
    '''
    --------------------
    '''

    '''
    --------------------
    是否使用最好的 10 条记录（而不是最近的 30 条记录中较好的 10 条）来计算 PTT
    Calculate PTT with best 10 instead of recent best 10
    '''
    USE_B10_AS_R10 = False
    '''
    --------------------
    '''
