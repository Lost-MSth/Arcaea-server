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
    是否强制使用全解锁云端存档
    If forcing full unlocked cloud save is enabled
    '''
    SAVE_FULL_UNLOCK = True
    '''
    --------------------
    '''
