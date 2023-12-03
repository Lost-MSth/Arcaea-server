from .config_manager import Config
from .constant import Constant
from .error import ArcError, InputError, ItemNotEnough, NoData
from .item import CollectionItemMixin, ItemCore


class Level:
    mid_level = 20
    min_level = 1

    def __init__(self) -> None:
        self.max_level: int = None
        self.level: int = None
        self.exp: float = None

    @property
    def level_exp(self):
        return Constant.LEVEL_STEPS[self.level]

    def add_exp(self, exp_addition: float):
        # 添加经验计算

        exp = self.exp + exp_addition

        if exp >= Constant.LEVEL_STEPS[self.max_level]:
            self.exp = Constant.LEVEL_STEPS[self.max_level]
            self.level = self.max_level
            return None

        a = []
        b = []
        for k, v in Constant.LEVEL_STEPS.items():
            a.append(k)
            b.append(v)

        if exp < b[0]:  # 向下溢出，是异常状态，不该被try捕获，不然数据库无法回滚
            raise ValueError('EXP value error.')

        i = len(a) - 1
        while exp < b[i]:
            i -= 1

        self.exp = exp
        self.level = a[i]


class Skill:
    def __init__(self) -> None:
        self.skill_id: str = None
        self.skill_id_uncap: str = None
        self.skill_unlock_level: int = None
        self.skill_requires_uncap: bool = None


class CharacterValue:
    def __init__(self, start: float = 0, mid: float = 0, end: float = 0) -> None:
        self.set_parameter(start, mid, end)

    @staticmethod
    def _calc_char_value_20_math(level: int, value_1: float, value_20: float) -> float:
        # by Lost-MSth
        # 4/6859 = 0.00058317539
        if level <= 10:
            return 0.00058317539 * (level - 1) ** 3 * (value_20 - value_1) + value_1
        return - 0.00058317539 * (20 - level) ** 3 * (value_20 - value_1) + value_20

    # @staticmethod
    # def _calc_char_value_20(level: int, stata, statb, lva=1, lvb=20) -> float:
    #     # 计算1~20级搭档数值的核心函数，返回浮点数，来自https://redive.estertion.win/arcaea/calc/
    #     n = [0, 0, 0.0005831753900000081, 0.004665403120000065, 0.015745735529959858, 0.03732322495992008, 0.07289692374980007, 0.12596588423968, 0.2000291587694801, 0.29858579967923987, 0.42513485930893946,
    #          0.5748651406910605, 0.7014142003207574, 0.7999708412305152, 0.8740341157603029, 0.9271030762501818, 0.962676775040091, 0.9842542644700301, 0.9953345968799998, 0.9994168246100001, 1]
    #     e = n[lva] - n[lvb]
    #     a = stata - statb
    #     r = a / e
    #     d = stata - n[lva] * r
    #     return d + r * n[level]

    @staticmethod
    def _calc_char_value_30(level, stata, statb, lva=20, lvb=30):
        # 计算21~30级搭档数值，返回浮点数
        return (level - lva) * (statb - stata) / (lvb - lva) + stata

    def set_parameter(self, start: float = 0, mid: float = 0, end: float = 0):
        self.start: float = start
        self.mid: float = mid
        self.end: float = end

    def get_value(self, level: Level):
        if level.min_level <= level.level <= level.mid_level:
            return self._calc_char_value_20_math(level.level, self.start, self.mid)
        if level.mid_level < level.level <= level.max_level:
            return self._calc_char_value_30(level.level, self.mid, self.end)
        return 0


class Character(CollectionItemMixin):
    database_table_name = None

    collection_item_const = {
        'name': 'character',
        'table_name': 'char_item',
        'table_primary_key': 'character_id',
        'id_name': 'character_id',
        'items_name': 'uncap_cores'
    }

    def __init__(self, c=None) -> None:
        self.c = c

        self.character_id: int = None
        self.name: str = None
        self.char_type: int = None
        self.is_uncapped: bool = None
        self.is_uncapped_override: bool = None
        self.skill = Skill()
        self.level = Level()
        self.frag = CharacterValue()
        self.prog = CharacterValue()
        self.overdrive = CharacterValue()
        self.uncap_cores: list = []
        self.voice: list = None

    @property
    def skill_id_displayed(self) -> str:
        return None

    def uncap_cores_to_dict(self):
        return [x.to_dict(character_format=True) for x in self.uncap_cores]

    @property
    def is_uncapped_displayed(self) -> bool:
        '''对外显示的uncap状态'''
        return False if self.is_uncapped_override else self.is_uncapped

    @property
    def is_base_character(self) -> bool:
        # 应该是只有对立这样
        return self.character_id == 1

    def to_dict(self, has_cores=False) -> dict:
        # 用于API里，游戏内的数据不太一样，故不能super
        r = {
            'character_id': self.character_id,
            'name': self.name,
            'char_type': self.char_type,
            'is_uncapped': self.is_uncapped,
            'max_level': self.level.max_level,
            'skill_id': self.skill.skill_id,
            'skill_unlock_level': self.skill.skill_unlock_level,
            'skill_requires_uncap': self.skill.skill_requires_uncap,
            'skill_id_uncap': self.skill.skill_id_uncap,
            'frag1': self.frag.start,
            'frag20': self.frag.mid,
            'frag30': self.frag.end,
            'prog1': self.prog.start,
            'prog20': self.prog.mid,
            'prog30': self.prog.end,
            'overdrive1': self.overdrive.start,
            'overdrive20': self.overdrive.mid,
            'overdrive30': self.overdrive.end,
        }
        if has_cores:
            r['uncap_cores'] = self.uncap_cores_to_dict()
        return r

    def from_list(self, l: tuple) -> 'Character':
        self.character_id = l[0]
        self.name = l[1]
        self.level.max_level = l[2]
        self.frag.set_parameter(l[3], l[6], l[9])
        self.prog.set_parameter(l[4], l[7], l[10])
        self.overdrive.set_parameter(l[5], l[8], l[11])
        self.skill.skill_id = l[12]
        self.skill.skill_unlock_level = l[13]
        self.skill.skill_requires_uncap = l[14] == 1
        self.skill.skill_id_uncap = l[15]
        self.char_type = l[16]
        self.is_uncapped = l[17] == 1
        return self

    def select(self, character_id: int = None) -> 'Character':
        if character_id is not None:
            self.character_id = character_id
        self.c.execute(
            'select * from character where character_id = ?', (self.character_id,))
        x = self.c.fetchone()
        if not x:
            raise NoData(
                f'No such character: {self.character_id}', api_error_code=-130)
        return self.from_list(x)

    def update(self) -> None:
        self.c.execute('''update character set name = ?, max_level = ?, frag1 = ?, frag20 = ?, frag30 = ?, prog1 = ?, prog20 = ?, prog30 = ?, overdrive1 = ?, overdrive20 = ?, overdrive30 = ?, skill_id = ?, skill_unlock_level = ?, skill_requires_uncap = ?, skill_id_uncap = ?, char_type = ?, is_uncapped = ? where character_id = ?''', (
            self.name, self.level.max_level, self.frag.start, self.frag.mid, self.frag.end, self.prog.start, self.prog.mid, self.prog.end, self.overdrive.start, self.overdrive.mid, self.overdrive.end, self.skill.skill_id, self.skill.skill_unlock_level, self.skill.skill_requires_uncap, self.skill.skill_id_uncap, self.char_type, self.is_uncapped, self.character_id))

    def select_character_core(self):
        # 获取此角色所需核心
        self.c.execute(
            '''select item_id, amount from char_item where character_id = ? and type="core"''', (self.character_id,))
        x = self.c.fetchall()
        if x:
            self.uncap_cores = []
            for i in x:
                self.uncap_cores.append(ItemCore(self.c, i[0], i[1]))


class UserCharacter(Character):
    '''
        用户角色类
        property: `user` - `User`类或子类的实例
    '''
    database_table_name = 'user_char_full' if Config.CHARACTER_FULL_UNLOCK else 'user_char'

    def __init__(self, c, character_id=None, user=None) -> None:
        super().__init__()
        self.c = c
        self.character_id = character_id
        self.user = user

        self.skill_flag: bool = None

    @property
    def skill_id_displayed(self) -> str:
        '''对外显示的技能id'''
        if self.is_uncapped_displayed and self.skill.skill_id_uncap:
            return self.skill.skill_id_uncap
        if self.skill.skill_id and self.level.level >= self.skill.skill_unlock_level:
            return self.skill.skill_id
        return None

    @property
    def skill_state(self) -> str:
        if self.skill_id_displayed == 'skill_maya':
            return 'add_random' if self.skill_flag else 'remove_random'
        return None

    def select_character_uncap_condition(self, user=None):
        # parameter: user - User类或子类的实例
        # 获取此角色的觉醒信息
        if user:
            self.user = user
        self.c.execute(f'''select is_uncapped, is_uncapped_override from {self.database_table_name} where user_id = :a and character_id = :b''',
                       {'a': self.user.user_id, 'b': self.character_id})

        x = self.c.fetchone()
        if not x:
            self.is_uncapped = False
            self.is_uncapped_override = False
            # raise NoData('The character of the user does not exist.')
        else:
            self.is_uncapped = x[0] == 1
            self.is_uncapped_override = x[1] == 1

    def select_character_info(self, user=None):
        # parameter: user - User类或子类的实例
        # 获取所给用户此角色信息
        if user:
            self.user = user
        self.c.execute(f'''select * from {self.database_table_name} a,character b where a.user_id=? and a.character_id=b.character_id and a.character_id=?''',
                       (self.user.user_id, self.character_id))

        y = self.c.fetchone()
        if y is None:
            raise NoData('The character of the user does not exist.')

        self.name = y[8]
        self.char_type = y[23]
        self.is_uncapped = y[4] == 1
        self.is_uncapped_override = y[5] == 1
        self.level.level = y[2]
        self.level.exp = y[3]
        self.level.max_level = y[9]
        self.frag.set_parameter(y[10], y[13], y[16])
        self.prog.set_parameter(y[11], y[14], y[17])
        self.overdrive.set_parameter(y[12], y[15], y[18])
        self.skill.skill_id = y[19]
        self.skill.skill_id_uncap = y[22]
        self.skill.skill_unlock_level = y[20]
        self.skill.skill_requires_uncap = y[21] == 1

        self.skill_flag = y[6] == 1

        if self.character_id in (21, 46):
            self.voice = [0, 1, 2, 3, 100, 1000, 1001]

        self.select_character_core()

    def to_dict(self) -> dict:
        if self.char_type is None:
            self.select_character_info(self.user)
        r = {'base_character': self.is_base_character,
             "is_uncapped_override": self.is_uncapped_override,
             "is_uncapped": self.is_uncapped,
             "uncap_cores": self.uncap_cores_to_dict(),
             "char_type": self.char_type,
             "skill_id_uncap": self.skill.skill_id_uncap,
             "skill_requires_uncap": self.skill.skill_requires_uncap,
             "skill_unlock_level": self.skill.skill_unlock_level,
             "skill_id": self.skill.skill_id,
             "overdrive": self.overdrive.get_value(self.level),
             "prog": self.prog.get_value(self.level),
             "frag": self.frag.get_value(self.level),
             "level_exp": self.level.level_exp,
             "exp": self.level.exp,
             "level": self.level.level,
             "name": self.name,
             "character_id": self.character_id
             }
        if self.voice:
            r['voice'] = self.voice
        if self.character_id == 55:
            r['fatalis_is_limited'] = False  # emmmmmmm
        if self.character_id in [1, 6, 7, 17, 18, 24, 32, 35, 52]:
            r['base_character_id'] = 1

        x = self.skill_state
        if x:
            r['skill_state'] = x

        return r

    def change_uncap_override(self, user=None):
        # parameter: user - User类或子类的实例
        # 切换觉醒状态
        if user:
            self.user = user
        self.c.execute(f'''select is_uncapped, is_uncapped_override from {self.database_table_name} where user_id = :a and character_id = :b''',
                       {'a': self.user.user_id, 'b': self.character_id})

        x = self.c.fetchone()
        if x is None or x[0] == 0:
            raise ArcError('Unknown Error')

        self.c.execute('''update user set is_char_uncapped_override = :a where user_id = :b''', {
            'a': 1 if x[1] == 0 else 0, 'b': self.user.user_id})

        self.c.execute(f'''update {self.database_table_name} set is_uncapped_override = :a where user_id = :b and character_id = :c''', {
            'a': 1 if x[1] == 0 else 0, 'b': self.user.user_id, 'c': self.character_id})

        self.is_uncapped_override = x[1] == 0

    def character_uncap(self, user=None):
        # parameter: user - User类或子类的实例
        # 觉醒角色
        if user:
            self.user = user
        if Config.CHARACTER_FULL_UNLOCK:
            # 全解锁了你觉醒个鬼啊
            raise ArcError('All characters are available.')

        if not self.uncap_cores:
            self.select_character_core()

        if self.is_uncapped is None:
            self.c.execute(
                '''select is_uncapped from user_char where user_id=? and character_id=?''', (self.user.user_id, self.character_id))
            x = self.c.fetchone()
            if x and x[0] == 1:
                raise ArcError('The character has been uncapped.')
        elif self.is_uncapped:
            raise ArcError('The character has been uncapped.')

        for i in self.uncap_cores:
            self.c.execute(
                '''select amount from user_item where user_id=? and item_id=? and type="core"''', (self.user.user_id, i.item_id))
            y = self.c.fetchone()
            if i.amount > 0 and (not y or i.amount > y[0]):
                raise ItemNotEnough('The cores are not enough.')

        for i in self.uncap_cores:
            i.user_claim_item(self.user, reverse=True)

        self.c.execute('''update user_char set is_uncapped=1, is_uncapped_override=0 where user_id=? and character_id=?''',
                       (self.user.user_id, self.character_id))

        self.is_uncapped = True
        self.is_uncapped_override = False

    def upgrade(self, user=None, exp_addition: float = 0) -> None:
        # parameter: user - User类或子类的实例
        # 升级角色
        if user:
            self.user = user
        if exp_addition == 0:
            return None
        if Config.CHARACTER_FULL_UNLOCK:
            # 全解锁了你升级个鬼啊
            raise ArcError('All characters are available.')

        if self.level.exp is None:
            self.select_character_info(self.user)

        if self.is_uncapped is None:
            self.c.execute(
                '''select is_uncapped from user_char where user_id=? and character_id=?''', (self.user.user_id, self.character_id))
            x = self.c.fetchone()
            if x:
                self.is_uncapped = x[0] == 1

        self.level.max_level = 30 if self.is_uncapped else 20
        self.level.add_exp(exp_addition)

        self.c.execute('''update user_char set level=?, exp=? where user_id=? and character_id=?''',
                       (self.level.level, self.level.exp, self.user.user_id, self.character_id))

    def upgrade_by_core(self, user=None, core=None):
        '''
            以太之滴升级，注意这里core.amount应该是负数

            parameter: `user` - `User`类或子类的实例
                `core` - `ItemCore`类或子类的实例
        '''
        if user:
            self.user = user
        if not core:
            raise InputError('No `core_generic`.')
        if core.item_id != 'core_generic':
            raise ArcError('Core type error.')

        if core.amount >= 0:
            raise InputError(
                'The amount of `core_generic` should be negative.')

        core.user_claim_item(self.user)
        self.upgrade(self.user, - core.amount * Constant.CORE_EXP)

    def change_skill_state(self) -> None:
        '''翻转技能状态，目前为 skill_miya 专用'''
        self.skill_flag = not self.skill_flag
        self.c.execute(f'''update {self.database_table_name} set skill_flag = ? where user_id = ? and character_id = ?''', (
            1 if self.skill_flag else 0, self.user.user_id, self.character_id))


class UserCharacterList:
    '''
        用户拥有角色列表类
        properties: `user` - `User`类或子类的实例
    '''
    database_table_name = 'user_char_full' if Config.CHARACTER_FULL_UNLOCK else 'user_char'

    def __init__(self, c=None, user=None):
        self.c = c
        self.user = user
        self.characters: list = []

    def select_user_characters(self):
        self.c.execute(
            f'''select character_id from {self.database_table_name} where user_id=?''', (self.user.user_id,))
        x = self.c.fetchall()
        self.characters: list = []
        if x:
            for i in x:
                self.characters.append(UserCharacter(self.c, i[0], self.user))

    def select_characters_info(self):
        for i in self.characters:
            i.select_character_info(self.user)
