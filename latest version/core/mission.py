from .item import Fragment, ItemCore, ItemStamina, PickTicket, WorldSong


class Mission:
    mission_id: str = None
    items: list = []

    def __init__(self, c=None):
        self.c = c
        self.user = None
        self._status: int = None

        if self.c is not None:
            for i in self.items:
                i.c = self.c

    def to_dict(self, has_items=False) -> dict:
        r = {
            'mission_id': self.mission_id,
            'status': self.status,
        }
        if has_items:
            r['items'] = [x.to_dict() for x in self.items]
        return r

    @property
    def status(self) -> str:
        if self._status == 1:
            return 'inprogress'
        elif self._status == 2:
            return 'cleared'
        elif self._status == 3:
            return 'prevclaimedfragmission'
        elif self._status == 4:
            return 'claimed'

        return 'locked'

    def user_claim_mission(self, user):
        # param: user - User 类或子类的实例
        if user is not None:
            self.user = user

        self.c.execute('''insert or replace into user_mission (user_id, mission_id, status) values (?, ?, 4)''',
                       (self.user.user_id, self.mission_id))
        for i in self.items:
            i.user_claim_item(self.user)
        self._status = 4

    def user_clear_mission(self, user):
        # param: user - User 类或子类的实例
        if user is not None:
            self.user = user

        self.c.execute('''insert or replace into user_mission (user_id, mission_id, status) values (?, ?, 2)''',
                       (self.user.user_id, self.mission_id))
        self._status = 2

    def select_user_mission(self, user):
        # param: user - User 类或子类的实例
        if user is not None:
            self.user = user

        self._status = 0
        self.c.execute('''select status from user_mission where user_id=? and mission_id=?''',
                       (self.user.user_id, self.mission_id))
        x = self.c.fetchone()

        if x and x[0]:
            self._status = x[0]


class M11(Mission):
    mission_id = 'mission_1_1_tutorial'
    items = [Fragment(amount=10)]


class M12(Mission):
    mission_id = 'mission_1_2_clearsong'
    items = [Fragment(amount=10)]


class M13(Mission):
    mission_id = 'mission_1_3_settings'
    items = [Fragment(amount=10)]


class M14(Mission):
    mission_id = 'mission_1_4_allsongsview'
    items = [Fragment(amount=10)]


class M15(Mission):
    mission_id = 'mission_1_5_fragunlock'
    items = [ItemCore(core_type='core_generic', amount=1)]


class M1E(Mission):
    mission_id = 'mission_1_end'
    items = [Fragment(amount=100)]


class M21(Mission):
    mission_id = 'mission_2_1_account'
    items = [Fragment(amount=20)]


class M22(Mission):
    mission_id = 'mission_2_2_profile'
    items = [Fragment(amount=20)]


class M23(Mission):
    mission_id = 'mission_2_3_partner'
    items = [Fragment(amount=20)]


class M24(Mission):
    mission_id = 'mission_2_4_usestamina'
    items = [ItemCore(core_type='core_generic', amount=1)]


class M25(Mission):
    mission_id = 'mission_2_5_prologuestart'
    items = [ItemCore(core_type='core_generic', amount=1)]


class M2E(Mission):
    mission_id = 'mission_2_end'
    items = [ItemCore(core_type='core_generic', amount=3)]


class M31(Mission):
    mission_id = 'mission_3_1_prsclear'
    items = [Fragment(amount=50)]


class M32(Mission):
    mission_id = 'mission_3_2_etherdrop'
    items = [ItemStamina(amount=2)]


class M33(Mission):
    mission_id = 'mission_3_3_step50'
    items = [Fragment(amount=50)]


class M34(Mission):
    mission_id = 'mission_3_4_frag60'
    items = [ItemStamina(amount=2)]


class M3E(Mission):
    mission_id = 'mission_3_end'
    items = [ItemStamina(amount=6)]


class M41(Mission):
    mission_id = 'mission_4_1_exgrade'
    items = [Fragment(amount=100)]


class M42(Mission):
    mission_id = 'mission_4_2_potential350'
    items = [ItemStamina(amount=2)]


class M43(Mission):
    mission_id = 'mission_4_3_twomaps'
    items = [Fragment(amount=100)]


class M44(Mission):
    mission_id = 'mission_4_4_worldsongunlock'
    items = [ItemCore(core_type='core_generic', amount=3)]


class M45(Mission):
    mission_id = 'mission_4_5_prologuefinish'
    items = [ItemStamina(amount=2)]


_innocence = WorldSong()
_innocence.amount = 1
_innocence.item_id = 'innocence'


class M4E(Mission):
    mission_id = 'mission_4_end'
    items = [_innocence]


class M51(Mission):
    mission_id = 'mission_5_1_songgrouping'
    items = [Fragment(amount=50)]


class M52(Mission):
    mission_id = 'mission_5_2_partnerlv12'
    items = [Fragment(amount=250)]


class M53(Mission):
    mission_id = 'mission_5_3_cores'
    items = [ItemCore(core_type='core_generic', amount=3)]


class M54(Mission):
    mission_id = 'mission_5_4_courseclear'
    items = [ItemCore(core_type='core_generic', amount=3)]


class M5E(Mission):
    mission_id = 'mission_5_end'
    items = [PickTicket()]


MISSION_DICT = {i.mission_id: i for i in Mission.__subclasses__()}


class UserMissionList:
    def __init__(self, c=None, user=None):
        self.c = c
        self.user = user

        self.missions: list = []

    def select_all(self):
        self.missions = []
        self.c.execute('''select mission_id, status from user_mission where user_id=?''',
                       (self.user.user_id,))
        for i in self.c.fetchall():
            x = MISSION_DICT[i[0]]()
            x._status = i[1]
            self.missions.append(x)

        return self

    def to_dict_list(self) -> list:
        return [i.to_dict() for i in self.missions]
