from setting import Config
from .error import ArcError, NoData
from .constant import Constant
from .item import Item


class Level:
    max_level = None
    mid_level = 20
    min_level = 1
    level = None
    exp = None

    def __init__(self) -> None:
        pass

    @property
    def level_exp(self):
        return Constant.LEVEL_STEPS[self.level]


class Skill:
    skill_id = None
    skill_id_uncap = None
    skill_unlock_level = None
    skill_requires_uncap = None

    def __init__(self) -> None:
        pass


class Core(Item):
    item_type = 'core'
    amount = None

    def __init__(self, core_type: str = '', amount: int = 0) -> None:
        super().__init__()
        self.item_id = core_type
        self.amount = amount

    def to_dict(self):
        return {'core_type': self.item_id, 'amount': self.amount}


class CharacterValue:
    start = None
    mid = None
    end = None

    def __init__(self) -> None:
        pass

    @staticmethod
    def _calc_char_value_20(level, stata, statb, lva=1, lvb=20):
        # 计算1~20级搭档数值的核心函数，返回浮点数，来自https://redive.estertion.win/arcaea/calc/
        n = [0, 0, 0.0005831753900000081, 0.004665403120000065, 0.015745735529959858, 0.03732322495992008, 0.07289692374980007, 0.12596588423968, 0.2000291587694801, 0.29858579967923987, 0.42513485930893946,
             0.5748651406910605, 0.7014142003207574, 0.7999708412305152, 0.8740341157603029, 0.9271030762501818, 0.962676775040091, 0.9842542644700301, 0.9953345968799998, 0.9994168246100001, 1]
        e = n[lva] - n[lvb]
        a = stata - statb
        r = a / e
        d = stata - n[lva] * r

        return d + r * n[level]

    @staticmethod
    def _calc_char_value_30(level, stata, statb, lva=20, lvb=30):
        # 计算21~30级搭档数值，返回浮点数
        return (level - lva) * (statb - stata) / (lvb - lva) + stata

    def set_parameter(self, start: float = 0, mid: float = 0, end: float = 0):
        self.start = start
        self.mid = mid
        self.end = end

    def get_value(self, level: Level):
        if level.min_level <= level.level <= level.mid_level:
            return self._calc_char_value_20(level.level, self.start, self.mid)
        elif level.mid_level < level.level <= level.max_level:
            return self._calc_char_value_30(level.level, self.mid, self.end)
        else:
            return 0


class Character:
    character_id = None
    name = None
    char_type = None
    is_uncapped = None
    is_uncapped_override = None
    skill = Skill()
    level = Level()
    frag = CharacterValue()
    prog = CharacterValue()
    overdrive = CharacterValue()
    uncap_cores = None

    def __init__(self) -> None:
        pass

    @property
    def uncap_cores_to_dict(self):
        return [x.to_dict() for x in self.uncap_cores]


class UserCharacter(Character):

    def __init__(self, c, character_id=None) -> None:
        super().__init__()
        self.c = c
        self.character_id = character_id

    def select_character_core(self):
        # 获取此角色所需核心
        self.c.execute(
            '''select item_id, amount from char_item where character_id = ? and type="core"''', (self.character_id,))
        x = self.c.fetchall()
        if x:
            self.uncap_cores = []
            for i in x:
                self.uncap_cores.append(Core(i[0], i[1]))

    def select_character_uncap_condition(self, user):
        # parameter: user - User类或子类的实例
        # 获取此角色的觉醒信息
        if Config.CHARACTER_FULL_UNLOCK:
            self.c.execute('''select is_uncapped, is_uncapped_override from user_char_full where user_id = :a and character_id = :b''',
                           {'a': user.user_id, 'b': self.character_id})
        else:
            self.c.execute('''select is_uncapped, is_uncapped_override from user_char where user_id = :a and character_id = :b''',
                           {'a': user.user_id, 'b': self.character_id})
        x = self.c.fetchone()
        if not x:
            raise NoData('The character of the user does not exist.')

        self.is_uncapped = x[0] == 1
        self.is_uncapped_override = x[1] == 1

    def select_character_info(self, user):
        # parameter: user - User类或子类的实例
        # 获取所给用户此角色信息
        if not Config.CHARACTER_FULL_UNLOCK:
            self.c.execute('''select * from user_char a,character b where a.user_id=? and a.character_id=b.character_id and a.character_id=?''',
                           (user.user_id, self.character_id))
        else:
            self.c.execute('''select * from user_char_full a,character b where a.user_id=? and a.character_id=b.character_id and a.character_id=?''',
                           (user.user_id, self.character_id))
        y = self.c.fetchone()
        if y is None:
            raise NoData('The character of the user does not exist.')

        self.name = y[7]
        self.char_type = y[22]
        self.is_uncapped = y[4] == 1
        self.is_uncapped_override = y[5] == 1
        self.level.level = y[2]
        self.level.exp = y[3]
        self.level.max_level = y[8]
        self.frag.set_parameter(y[9], y[12], y[15])
        self.prog.set_parameter(y[10], y[13], y[16])
        self.overdrive.set_parameter(y[11], y[14], y[17])
        self.skill.skill_id = y[18]
        self.skill.skill_id_uncap = y[21]
        self.skill.skill_unlock_level = y[19]
        self.skill.skill_requires_uncap = y[20] == 1
        self.select_character_core()

    @property
    def to_dict(self):
        return {"is_uncapped_override": self.is_uncapped_override,
                "is_uncapped": self.is_uncapped,
                "uncap_cores": self.uncap_cores_to_dict,
                "char_type": self.char_type,
                "skill_id_uncap": self.skill.skill_id_uncap,
                "skill_requires_uncap": self.skill.skill_requires_uncap,
                "skill_unlock_level": self.skill.skill_unlock_level,
                "skill_id": self.skill.skill_id,
                "overdrive": self.overdrive.get_value(self.level),
                "prog": self.overdrive.get_value(self.level),
                "frag": self.overdrive.get_value(self.level),
                "level_exp": self.level.level_exp,
                "exp": self.level.exp,
                "level": self.level.level,
                "name": self.name,
                "character_id": self.character_id
                }

    def change_uncap_override(self, user):
        # parameter: user - User类或子类的实例
        # 切换觉醒状态
        if not Config.CHARACTER_FULL_UNLOCK:
            self.c.execute('''select is_uncapped, is_uncapped_override from user_char where user_id = :a and character_id = :b''',
                           {'a': user.user_id, 'b': self.character_id})
        else:
            self.c.execute('''select is_uncapped, is_uncapped_override from user_char_full where user_id = :a and character_id = :b''',
                           {'a': user.user_id, 'b': self.character_id})

        x = self.c.fetchone()
        if x is None or x[0] == 0:
            raise ArcError('Unknown Error')

        self.c.execute('''update user set is_char_uncapped_override = :a where user_id = :b''', {
            'a': 1 if x[1] == 0 else 0, 'b': user.user_id})

        if not Config.CHARACTER_FULL_UNLOCK:
            self.c.execute('''update user_char set is_uncapped_override = :a where user_id = :b and character_id = :c''', {
                'a': 1 if x[1] == 0 else 0, 'b': user.user_id, 'c': self.character_id})
        else:
            self.c.execute('''update user_char_full set is_uncapped_override = :a where user_id = :b and character_id = :c''', {
                'a': 1 if x[1] == 0 else 0, 'b': user.user_id, 'c': self.character_id})

    def character_uncap(self):
        # 觉醒角色
        pass
