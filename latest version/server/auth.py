import hashlib
import time
from server.sql import Connect
import functools
from setting import Config
from flask import jsonify

BAN_TIME = [1, 3, 7, 15, 31]


def arc_login(name: str, password: str, device_id: str, ip: str):  # 登录判断
    # 查询数据库中的user表，验证账号密码，返回并记录token，多返回个error code和extra
    # token采用user_id和时间戳连接后hash生成（真的是瞎想的，没用bear）
    # 密码和token的加密方式为 SHA-256

    error_code = 108
    token = None
    with Connect() as c:
        hash_pwd = hashlib.sha256(password.encode("utf8")).hexdigest()
        c.execute('''select user_id, password, ban_flag from user where name = :name''', {
            'name': name})
        x = c.fetchone()
        if x is not None:
            now = int(time.time() * 1000)
            if x[2] is not None and x[2] != '':
                # 自动封号检查
                ban_timestamp = int(x[2].split(':', 1)[1])
                if ban_timestamp > now:
                    return None, 105, {'remaining_ts': ban_timestamp-now}
            if x[1] == '':
                # 账号封禁
                error_code = 106
            elif x[1] == hash_pwd:
                user_id = str(x[0])
                token = hashlib.sha256(
                    (user_id + str(now)).encode("utf8")).hexdigest()
                c.execute(
                    '''select login_device from login where user_id = :user_id''', {"user_id": user_id})
                y = c.fetchall()
                if y:
                    device_list = []
                    for i in y:
                        if i[0]:
                            device_list.append(i[0])
                        else:
                            device_list.append('')

                    should_delete_num = len(
                        device_list) + 1 - Config.LOGIN_DEVICE_NUMBER_LIMIT

                    if not Config.ALLOW_LOGIN_SAME_DEVICE:
                        if device_id in device_list:  # 对相同设备进行删除
                            c.execute('''delete from login where login_device=:a and user_id=:b''', {
                                'a': device_id, 'b': user_id})
                            should_delete_num = len(
                                device_list) + 1 - device_list.count(device_id) - Config.LOGIN_DEVICE_NUMBER_LIMIT

                    if should_delete_num >= 1:  # 删掉多余token
                        if not Config.ALLOW_LOGIN_SAME_DEVICE and Config.ALLOW_BAN_MULTIDEVICE_USER_AUTO:  # 自动封号检查
                            c.execute(
                                '''select count(*) from login where user_id=? and login_time>?''', (user_id, now-86400000))
                            if c.fetchone()[0] >= Config.LOGIN_DEVICE_NUMBER_LIMIT:
                                remaining_ts = arc_auto_ban(c, user_id, now)
                                return None, 105, {'remaining_ts': remaining_ts}

                        c.execute('''delete from login where rowid in (select rowid from login where user_id=:user_id limit :a);''',
                                  {'user_id': user_id, 'a': int(should_delete_num)})

                c.execute('''insert into login values(:access_token, :user_id, :time, :ip, :device_id)''', {
                    'user_id': user_id, 'access_token': token, 'device_id': device_id, 'time': now, 'ip': ip})
                error_code = None
            else:
                # 密码错误
                error_code = 104
        else:
            # 用户名错误
            error_code = 104

    return token, error_code, None


def arc_register(name: str, password: str, device_id: str, email: str, ip: str):  # 注册
    # 账号注册，记录hash密码、用户名和邮箱，生成user_id和user_code，自动登录返回token
    # token和密码的处理同登录部分

    def build_user_code(c):
        # 生成9位的user_code，用的自然是随机
        import random
        flag = True
        while flag:
            user_code = ''.join([str(random.randint(0, 9)) for i in range(9)])
            c.execute('''select exists(select * from user where user_code = :user_code)''',
                      {'user_code': user_code})
            if c.fetchone() == (0,):
                flag = False
        return user_code

    def build_user_id(c):
        # 生成user_id，往后加1
        c.execute('''select max(user_id) from user''')
        x = c.fetchone()
        if x[0] is not None:
            return x[0] + 1
        else:
            return 2000001

    def insert_user_char(c, user_id):
        # 为用户添加初始角色
        c.execute('''insert into user_char values(?,?,?,?,?,?)''',
                  (user_id, 0, 1, 0, 0, 0))
        c.execute('''insert into user_char values(?,?,?,?,?,?)''',
                  (user_id, 1, 1, 0, 0, 0))
        c.execute('''select character_id, max_level, is_uncapped from character''')
        x = c.fetchall()
        if x:
            for i in x:
                exp = 25000 if i[1] == 30 else 10000
                c.execute('''insert into user_char_full values(?,?,?,?,?,?)''',
                          (user_id, i[0], i[1], exp, i[2], 0))

    user_id = None
    token = None
    error_code = 108
    with Connect() as c:
        hash_pwd = hashlib.sha256(password.encode("utf8")).hexdigest()
        c.execute(
            '''select exists(select * from user where name = :name)''', {'name': name})
        if c.fetchone() == (0,):
            c.execute(
                '''select exists(select * from user where email = :email)''', {'email': email})
            if c.fetchone() == (0,):
                user_code = build_user_code(c)
                user_id = build_user_id(c)
                now = int(time.time() * 1000)
                c.execute('''insert into user(user_id, name, password, join_date, user_code, rating_ptt, 
                character_id, is_skill_sealed, is_char_uncapped, is_char_uncapped_override, is_hide_rating, favorite_character, max_stamina_notification_enabled, current_map, ticket, prog_boost, email)
                values(:user_id, :name, :password, :join_date, :user_code, 0, 0, 0, 0, 0, 0, -1, 0, '', :memories, 0, :email)
                ''', {'user_code': user_code, 'user_id': user_id, 'join_date': now, 'name': name, 'password': hash_pwd, 'memories': Config.DEFAULT_MEMORIES, 'email': email})
                c.execute('''insert into recent30(user_id) values(:user_id)''', {
                    'user_id': user_id})

                token = hashlib.sha256(
                    (str(user_id) + str(now)).encode("utf8")).hexdigest()
                c.execute('''insert into login values(:access_token, :user_id, :time, :ip, :device_id)''', {
                    'user_id': user_id, 'access_token': token, 'device_id': device_id, 'time': now, 'ip': ip})

                insert_user_char(c, user_id)
                error_code = 0
            else:
                error_code = 102
        else:
            error_code = 101

    return user_id, token, error_code


def token_get_id(token: str):
    # 用token获取id，没有考虑不同用户token相同情况，说不定会有bug

    user_id = None
    with Connect() as c:
        c.execute('''select user_id from login where access_token = :token''', {
            'token': token})
        x = c.fetchone()
        if x is not None:
            user_id = x[0]

    return user_id


def code_get_id(user_code):
    # 用user_code获取id

    user_id = None

    with Connect() as c:
        c.execute('''select user_id from user where user_code = :a''',
                  {'a': user_code})
        x = c.fetchone()
        if x is not None:
            user_id = x[0]

    return user_id


def auth_required(request):
    # arcaea登录验证，写成了修饰器
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(*args, **kwargs):

            user_id = None
            headers = request.headers

            if 'AppVersion' in headers:  # 版本检查
                if Config.ALLOW_APPVERSION:
                    if headers['AppVersion'] not in Config.ALLOW_APPVERSION:
                        return jsonify({"success": False, "error_code": 1203})

            if 'Authorization' in headers:
                token = headers['Authorization']
                token = token[7:]
                user_id = token_get_id(token)

            if user_id is not None:
                return view(user_id, *args, **kwargs)
            else:
                return jsonify({"success": False, "error_code": 108})

        return wrapped_view
    return decorator


def arc_auto_ban(c, user_id, now):
    # 多设备自动封号机制，返回封号时长
    c.execute('''delete from login where user_id=?''', (user_id, ))
    c.execute('''select ban_flag from user where user_id=?''', (user_id,))
    x = c.fetchone()
    if x and x[0] != '' and x[0] is not None:
        last_ban_time = int(x[0].split(':', 1)[0])
        i = 0
        while i < len(BAN_TIME) - 1 and BAN_TIME[i] <= last_ban_time:
            i += 1
        ban_time = BAN_TIME[i]
    else:
        ban_time = BAN_TIME[0]

    ban_flag = ':'.join((str(ban_time), str(now + ban_time*24*60*60*1000)))
    c.execute('''update user set ban_flag=? where user_id=?''',
              (ban_flag, user_id))

    return ban_time*24*60*60*1000
