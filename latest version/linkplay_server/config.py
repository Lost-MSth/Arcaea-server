class Config:
    '''
        Link Play server configuration
    '''

    '''
        服务器地址、端口号、校验码
        Server address, port and verification code
    '''
    HOST = '0.0.0.0'
    UDP_PORT = 10900
    TCP_PORT = 10901
    AUTHENTICATION = 'my_link_play_server'
    '''
    --------------------------------------------------
    '''

    TIME_LIMIT = 3600000

    COMMAND_INTERVAL = 1000000

    COUNTDOWM_TIME = 3999

    PLAYER_PRE_TIMEOUT = 3000000
    PLAYER_TIMEOUT = 20000000

    LINK_PLAY_UNLOCK_LENGTH = 512
