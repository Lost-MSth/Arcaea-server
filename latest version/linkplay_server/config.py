class Config:
    '''
        Link Play server configuration
    '''

    '''
        服务器地址、端口号、校验码、传输加密密钥
        Server address, port, verification code, and encryption key
    '''
    HOST = '0.0.0.0'
    UDP_PORT = 10900
    TCP_PORT = 10901
    AUTHENTICATION = 'my_link_play_server'
    TCP_SECRET_KEY = '1145141919810'
    '''
    --------------------------------------------------
    '''

    DEBUG = False

    TCP_MAX_LENGTH = 0x0FFFFFFF

    TIME_LIMIT = 3600000

    COMMAND_INTERVAL = 1000000

    PLAYER_PRE_TIMEOUT = 3000000
    PLAYER_TIMEOUT = 15000000

    LINK_PLAY_UNLOCK_LENGTH = 512

    COUNTDOWN_SONG_READY = 4 * 1000000
    COUNTDOWN_SONG_START = 6 * 1000000

    # 计时模式
    COUNTDOWN_MATCHING = 15 * 1000000
    COUNTDOWN_SELECT_SONG = 45 * 1000000
    COUNTDOWN_SELECT_DIFFICULTY = 45 * 1000000
    COUNTDOWN_RESULT = 60 * 1000000
