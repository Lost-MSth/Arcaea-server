from .error import ArcError, InputError, DataExist
from setting import Config
import hashlib
import time


class User:
    name = None
    email = None
    password = None
    user_id = None
    user_code = None

    def __init__(self) -> None:
        pass


class RegisterUser(User):
    def __init__(self, c) -> None:
        super().__init__()
        self.c = c

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
