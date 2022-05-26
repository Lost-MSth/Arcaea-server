from .error import ArcError, InputError, DataExist, NoAccess, NoData, UserBan, FriendError
from .constant import Constant
from .character import UserCharacter
from .score import Score
from .world import Map
from .item import get_user_cores
from setting import Config
import hashlib
import base64
import time
from os import urandom


def code_get_id(c, user_code: str) -> int:
    # 用user_code获取user_id

    c.execute('''select user_id from user where user_code = :a''',
              {'a': user_code})
    x = c.fetchone()

    if x is not None:
        user_id = int(x[0])
    else:
        raise NoData('No user.', 401, -3)

    return user_id


class User:
    def __init__(self) -> None:
        self.name = None
        self.email = None
        self.password = None
        self.user_id = None
        self.user_code = None

        self.join_date = None
        self.rating_ptt = None

        self.ticket = None
        self.world_rank_score = None
        self.ban_flag = None


class UserRegister(User):
    def __init__(self, c) -> None:
        super().__init__()
        self.c = c
        self.hash_pwd = None

    def set_name(self, name: str):
        if 3 <= len(name) <= 16:
            self.c.execute(
                '''select exists(select * from user where name = :name)''', {'name': name})
            if self.c.fetchone() == (0,):
                self.name = name
            else:
                raise DataExist('Username exists.', 101, -203)

        else:
            raise InputError('Username is invalid.')

    def set_password(self, password: str):
        if 8 <= len(password) <= 32:
            self.password = password
            self.hash_pwd = hashlib.sha256(password.encode("utf8")).hexdigest()
        else:
            raise InputError('Password is invalid.')

    def set_email(self, email: str):
        # 邮箱格式懒得多判断
        if 4 <= len(email) <= 32 and '@' in email and '.' in email:
            self.c.execute(
                '''select exists(select * from user where email = :email)''', {'email': email})
            if self.c.fetchone() == (0,):
                self.email = email
            else:
                raise DataExist('Email address exists.', 102, -204)
        else:
            raise InputError('Email address is invalid.')

    def _build_user_code(self):
        # 生成9位的user_code，用的自然是随机
        from random import randint
        random_times = 0

        while random_times <= 1000:
            random_times += 1
            user_code = ''.join([str(randint(0, 9)) for _ in range(9)])
            self.c.execute('''select exists(select * from user where user_code = :user_code)''',
                           {'user_code': user_code})
            if self.c.fetchone() == (0,):
                break

        if random_times <= 1000:
            self.user_code = user_code
        else:
            raise ArcError('No available user code.')

    def _build_user_id(self):
        # 生成user_id，往后加1
        self.c.execute('''select max(user_id) from user''')
        x = self.c.fetchone()
        if x[0] is not None:
            self.user_id = x[0] + 1
        else:
            self.user_id = 2000001

    def _insert_user_char(self):
        # 为用户添加初始角色
        self.c.execute('''insert into user_char values(?,?,?,?,?,?)''',
                       (self.user_id, 0, 1, 0, 0, 0))
        self.c.execute('''insert into user_char values(?,?,?,?,?,?)''',
                       (self.user_id, 1, 1, 0, 0, 0))
        self.c.execute(
            '''select character_id, max_level, is_uncapped from character''')
        x = self.c.fetchall()
        if x:
            for i in x:
                exp = 25000 if i[1] == 30 else 10000
                self.c.execute('''insert into user_char_full values(?,?,?,?,?,?)''',
                               (self.user_id, i[0], i[1], exp, i[2], 0))

    def register(self):
        now = int(time.time() * 1000)
        self._build_user_code()
        self._build_user_id()
        self._insert_user_char()

        self.c.execute('''insert into user(user_id, name, password, join_date, user_code, rating_ptt, 
        character_id, is_skill_sealed, is_char_uncapped, is_char_uncapped_override, is_hide_rating, favorite_character, max_stamina_notification_enabled, current_map, ticket, prog_boost, email)
        values(:user_id, :name, :password, :join_date, :user_code, 0, 0, 0, 0, 0, 0, -1, 0, '', :memories, 0, :email)
        ''', {'user_code': self.user_code, 'user_id': self.user_id, 'join_date': now, 'name': self.name, 'password': self.hash_pwd, 'memories': Config.DEFAULT_MEMORIES, 'email': self.email})
        self.c.execute('''insert into recent30(user_id) values(:user_id)''', {
                       'user_id': self.user_id})


class UserLogin(User):
    # 密码和token的加密方式为 SHA-256
    def __init__(self, c) -> None:
        super().__init__()
        self.c = c
        self.device_id = None
        self.ip = None
        self.hash_pwd = None
        self.token = None
        self.now = 0

    def set_name(self, name: str):
        self.name = name

    def set_password(self, password: str):
        self.password = password
        self.hash_pwd = hashlib.sha256(password.encode("utf8")).hexdigest()

    def set_device_id(self, device_id: str):
        self.device_id = device_id

    def set_ip(self, ip: str):
        self.ip = ip

    def _arc_auto_ban(self):
        # 多设备自动封号机制，返回封号时长
        self.c.execute('''delete from login where user_id=?''',
                       (self.user_id, ))
        self.c.execute(
            '''select ban_flag from user where user_id=?''', (self.user_id,))
        x = self.c.fetchone()
        if x and x[0] != '' and x[0] is not None:
            last_ban_time = int(x[0].split(':', 1)[0])
            i = 0
            while i < len(Constant.BAN_TIME) - 1 and Constant.BAN_TIME[i] <= last_ban_time:
                i += 1
            ban_time = Constant.BAN_TIME[i]
        else:
            ban_time = Constant.BAN_TIME[0]

        ban_flag = ':'.join(
            (str(ban_time), str(self.now + ban_time * 86400000)))
        self.c.execute('''update user set ban_flag=? where user_id=?''',
                       (ban_flag, self.user_id))

        return ban_time * 86400000

    def _check_device(self, device_list):
        should_delete_num = len(
            device_list) + 1 - Config.LOGIN_DEVICE_NUMBER_LIMIT

        if not Config.ALLOW_LOGIN_SAME_DEVICE:
            if self.device_id in device_list:  # 对相同设备进行删除
                self.c.execute('''delete from login where login_device=:a and user_id=:b''', {
                    'a': self.device_id, 'b': self.user_id})
                should_delete_num = len(
                    device_list) + 1 - device_list.count(self.device_id) - Config.LOGIN_DEVICE_NUMBER_LIMIT

        if should_delete_num >= 1:  # 删掉多余token
            if not Config.ALLOW_LOGIN_SAME_DEVICE and Config.ALLOW_BAN_MULTIDEVICE_USER_AUTO:  # 自动封号检查
                self.c.execute(
                    '''select count(*) from login where user_id=? and login_time>?''', (self.user_id, self.now-86400000))
                if self.c.fetchone()[0] >= Config.LOGIN_DEVICE_NUMBER_LIMIT:
                    remaining_ts = self._arc_auto_ban()
                    raise UserBan('Too many devices logging in during 24 hours.', 105, extra_data={
                                  'remaining_ts': remaining_ts})

            self.c.execute('''delete from login where rowid in (select rowid from login where user_id=:user_id limit :a);''',
                           {'user_id': self.user_id, 'a': int(should_delete_num)})

    def login(self, name: str = '', password: str = '', device_id: str = '', ip: str = ''):
        if name:
            self.set_name(name)
        if password:
            self.set_password(password)
        if device_id:
            self.set_device_id(device_id)
        if ip:
            self.set_ip(ip)

        self.c.execute('''select user_id, password, ban_flag from user where name = :name''', {
                       'name': self.name})
        x = self.c.fetchone()
        if x is None:
            raise NoData('Username does not exist.', 104)

        self.now = int(time.time() * 1000)
        if x[2] is not None and x[2] != '':
            # 自动封号检查
            ban_timestamp = int(x[2].split(':', 1)[1])
            if ban_timestamp > self.now:
                raise UserBan('Too many devices logging in during 24 hours.', 105, extra_data={
                              'remaining_ts': ban_timestamp-self.now})

        if x[1] == '':
            # 账号封禁
            raise UserBan('The account has been banned.', 106)

        if x[1] != self.hash_pwd:
            raise NoAccess('Wrong password.', 104)

        self.user_id = str(x[0])
        self.token = base64.b64encode(hashlib.sha256(
            (self.user_id + str(self.now)).encode("utf8") + urandom(8)).digest()).decode()

        self.c.execute(
            '''select login_device from login where user_id = :user_id''', {"user_id": self.user_id})
        y = self.c.fetchall()
        if y:
            self._check_device([i[0] if i[0] else '' for i in y])

        self.c.execute('''insert into login values(:access_token, :user_id, :time, :ip, :device_id)''', {
            'user_id': self.user_id, 'access_token': self.token, 'device_id': self.device_id, 'time': self.now, 'ip': self.ip})


class UserAuth(User):
    def __init__(self, c) -> None:
        super().__init__()
        self.c = c
        self.token = None

    def token_get_id(self):
        # 用token获取id，没有考虑不同用户token相同情况，说不定会有bug
        self.c.execute('''select user_id from login where access_token = :token''', {
            'token': self.token})
        x = self.c.fetchone()
        if x is not None:
            self.user_id = x[0]
        else:
            raise NoAccess('Wrong token.', -4)

        return self.user_id


class UserOnline(User):
    def __init__(self, c, user_id=None) -> None:
        super().__init__()
        self.c = c
        self.user_id = user_id
        self.character = None
        self.is_skill_sealed = False
        self.is_hide_rating = False
        self.recent_score = Score()
        self.favorite_character = -1
        self.max_stamina_notification_enabled = False
        self.prog_boost = 0

        self.__cores = None
        self.__friends = None

    @property
    def cores(self) -> list:
        if self.__cores is None:
            self.__cores = get_user_cores(self.c, self)

        return self.__cores

    @property
    def friends(self) -> list:
        # 得到用户的朋友列表
        if self.__friends is None:
            self.c.execute('''select user_id_other from friend where user_id_me = :user_id''', {
                'user_id': self.user_id})
            x = self.c.fetchall()
            s = []
            if x != [] and x[0][0] is not None:
                for i in x:
                    self.c.execute('''select exists(select * from friend where user_id_me = :x and user_id_other = :y)''',
                                   {'x': i[0], 'y': self.user_id})

                    is_mutual = True if self.c.fetchone() == (1,) else False

                    you = UserOnline(self.c, i[0])
                    you.select_user()
                    character = you.character if you.favorite_character is None else you.favorite_character
                    character.select_character_uncap_condition(you)

                    rating = you.rating_ptt if not you.is_hide_rating else -1

                    s.append({
                        "is_mutual": is_mutual,
                        "is_char_uncapped_override": character.is_uncapped_override,
                        "is_char_uncapped": character.is_uncapped,
                        "is_skill_sealed": you.is_skill_sealed,
                        "rating": rating,
                        "join_date": you.join_date,
                        "character": character.character_id,
                        "recent_score": you.recent_score_list,
                        "name": you.name,
                        "user_id": you.user_id
                    })
            s.sort(key=lambda item: item["recent_score"][0]["time_played"] if len(
                item["recent_score"]) > 0 else 0, reverse=True)
            self.__friends = s

        return self.__friends

    @property
    def recent_score_list(self) -> list:
        # 用户最近一次成绩，是列表
        if self.name is None:
            self.select_user()

        if self.recent_score.song.song_id is None:
            return []

        self.c.execute('''select best_clear_type from best_score where user_id=:u and song_id=:s and difficulty=:d''', {
            'u': self.user_id, 's': self.recent_score.song.song_id, 'd': self.recent_score.song.difficulty})
        y = self.c.fetchone()
        best_clear_type = y[0] if y is not None else self.recent_score.clear_type

        r = self.recent_score.to_dict
        r["best_clear_type"] = best_clear_type
        return [r]

    def change_character(self, character_id: int, skill_sealed: bool = False):
        # 用户角色改变，包括技能封印的改变
        self.character = UserCharacter(self.c, character_id)
        self.character.select_character_uncap_condition(self)
        self.is_skill_sealed = skill_sealed

        self.c.execute('''update user set is_skill_sealed = :a, character_id = :b, is_char_uncapped = :c, is_char_uncapped_override = :d where user_id = :e''', {
            'a': 1 if self.is_skill_sealed else 0, 'b': self.character.character_id, 'c': self.character.is_uncapped, 'd': self.character.is_uncapped_override, 'e': self.user_id})

    def select_user(self):
        # 查user表所有信息
        self.c.execute(
            '''select * from user where user_id = :x''', {'x': self.user_id})
        x = self.c.fetchone()
        if not x:
            raise NoData('No user.', 108, -3)

        self.name = x[1]
        self.join_date = int(x[3])
        self.user_code = x[4]
        self.rating_ptt = x[5]
        self.character = UserCharacter(self.c, x[6])
        self.is_skill_sealed = x[7] == 1
        self.character.is_uncapped = x[8] == 1
        self.character.is_uncapped_override = x[9] == 1
        self.is_hide_rating = x[10] == 1

        self.recent_score.song.song_id = x[11]
        self.recent_score.song.difficulty = x[12]
        self.recent_score.set_score(
            x[13], x[14], x[15], x[16], x[17], x[18], x[19], x[20], x[21])
        self.recent_score.rating = x[22]

        self.favorite_character = None if x[23] == - \
            1 else UserCharacter(self.c, x[23])
        self.max_stamina_notification_enabled = x[24] == 1
        self.current_map = Map(x[25])
        self.ticket = x[26]
        self.prog_boost = x[27]
        self.email = x[28]
        self.world_rank_score = x[29]
        self.ban_flag = x[30]

        self.next_fragstam_ts = x[31]
        self.max_stamina_ts = x[32]
        self.stamina = x[33]

    def add_friend(self, friend_id: int):
        # 加好友
        if self.user_id == friend_id:
            raise FriendError('Add yourself as a friend.', 604)

        self.c.execute('''select exists(select * from friend where user_id_me = :x and user_id_other = :y)''',
                       {'x': self.user_id, 'y': friend_id})
        if self.c.fetchone() == (0,):
            self.c.execute('''insert into friend values(:a, :b)''', {
                           'a': self.user_id, 'b': friend_id})
        else:
            raise FriendError('The user has been your friend.', 602)

    def delete_friend(self, friend_id: int):
        # 删好友

        self.c.execute('''select exists(select * from friend where user_id_me = :x and user_id_other = :y)''',
                       {'x': self.user_id, 'y': friend_id})
        if self.c.fetchone() == (1,):
            self.c.execute('''delete from friend where user_id_me = :x and user_id_other = :y''',
                           {'x': self.user_id, 'y': friend_id})
        else:
            raise FriendError('No user or the user is not your friend.', 401)
