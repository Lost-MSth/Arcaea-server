from hashlib import sha256
from os import urandom
from time import time

from .config_manager import Config
from .error import NoAccess, NoData, RateLimit, UserBan
from .limiter import ArcLimiter
from .user import UserOnline


class Power:
    def __init__(self, c=None):
        self.c = c
        self.power_id: str = None
        self.caption: str = None

    @classmethod
    def from_dict(cls, d: dict, c=None) -> 'Power':
        p = cls(c)
        p.power_id = d['power_id']
        p.caption = d['caption']
        return p


class Role:
    def __init__(self, c=None):
        self.c = c
        self.role_id: str = None
        self.caption: str = None

        self.powers: list = None

    def has_power(self, power_id: str) -> bool:
        '''判断role是否有power'''
        return any(power_id == i.power_id for i in self.powers)

    def select_from_id(self, role_id: int = None) -> 'Role':
        '''用role_id查询role'''
        if role_id is not None:
            self.role_id = role_id
        self.c.execute('''select caption from role where role_id = :a''',
                       {'a': self.role_id})
        x = self.c.fetchone()
        if x is None:
            raise NoData('The role `%s` does not exist.' %
                         self.role_id, api_error_code=-200)
        self.caption = x[0]
        return self

    def select_powers(self) -> None:
        '''查询role的全部powers'''
        self.powers = []
        self.c.execute('''select * from power where power_id in (select power_id from role_power where role_id=:a)''', {
            'a': self.role_id})
        x = self.c.fetchall()
        for i in x:
            self.powers.append(Power.from_dict(
                {'power_id': i[0], 'caption': i[1]}, self.c))


class APIUser(UserOnline):
    limiter = ArcLimiter(Config.API_LOGIN_RATE_LIMIT, 'api_login')

    def __init__(self, c=None, user_id=None) -> None:
        super().__init__(c, user_id)
        self.api_token: str = None
        self.role: 'Role' = None

        self.ip: str = None

    def set_role_system(self) -> None:
        '''设置为最高权限用户，API接口'''
        self.user_id = 0
        self.role = Role(self.c)
        self.role.role_id = 'system'
        self.role.select_powers()

    def select_role(self) -> None:
        '''查询user的role'''
        self.c.execute('''select role_id from user_role where user_id = :a''',
                       {'a': self.user_id})
        x = self.c.fetchone()
        self.role = Role(self.c)
        if x is None:
            # 默认role为user
            self.role.role_id = 'user'
        else:
            self.role.role_id = x[0]

    def select_role_and_powers(self) -> None:
        '''查询user的role，以及role的powers'''
        self.select_role()
        self.role.select_powers()

    def select_user_id_from_api_token(self, api_token: str = None) -> None:
        if api_token is not None:
            self.api_token = api_token
        self.c.execute('''select user_id from api_login where token = :token''', {
            'token': self.api_token})
        x = self.c.fetchone()
        if x is None:
            raise NoAccess('No token', api_error_code=-1)
        self.user_id = x[0]

    def logout(self) -> None:
        self.c.execute(
            '''delete from api_login where user_id=?''', (self.user_id,))

    def login(self, name: str = None, password: str = None, ip: str = None) -> None:
        if name is not None:
            self.name = name
        if password is not None:
            self.password = password
        if ip is not None:
            self.ip = ip
        if not self.limiter.hit(name):
            raise RateLimit('Too many login attempts', api_error_code=-205)

        self.c.execute('''select user_id, password from user where name = :a''', {
                       'a': self.name})
        x = self.c.fetchone()
        if x is None:
            raise NoData('The user `%s` does not exist.' %
                         self.name, api_error_code=-201)
        if x[1] == '':
            raise UserBan('The user `%s` is banned.' % self.name)
        if self.hash_pwd != x[1]:
            raise NoAccess('The password is incorrect.', api_error_code=-201)

        self.user_id = x[0]
        now = int(time() * 1000)
        self.token = sha256(
            (str(self.user_id) + str(now)).encode("utf8") + urandom(8)).hexdigest()

        self.logout()
        self.c.execute('''insert into api_login values(?,?,?,?)''',
                       (self.user_id, self.token, now, self.ip))
