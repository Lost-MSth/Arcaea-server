import os
from functools import lru_cache
from json import load
from random import randint
from time import time

from .character import Character
from .constant import Constant
from .error import InputError, MapLocked, NoData
from .item import ItemFactory


@lru_cache(maxsize=128)
def get_world_name(file_dir: str = Constant.WORLD_MAP_FOLDER_PATH) -> list:
    '''获取所有地图名称，返回列表'''
    file_list = []
    for root, dirs, files in os.walk(file_dir):
        for file in files:
            if os.path.splitext(file)[1] == '.json':
                file_list.append(os.path.splitext(file)[0])
    return file_list


@lru_cache(maxsize=128)
def get_world_info(map_id: str) -> dict:
    '''读取json文件内容，返回字典'''
    world_info = {}
    with open(os.path.join(Constant.WORLD_MAP_FOLDER_PATH, f'{map_id}.json'), 'rb') as f:
        world_info = load(f)

    return world_info


def get_world_all(c, user) -> list:
    '''
        读取所有地图信息，返回列表
        parameter: `user` - `User`类或子类的实例
    '''
    worlds = get_world_name()
    return [UserMap(c, map_id, user) for map_id in worlds]


class Step:
    '''台阶类'''

    def __init__(self) -> None:
        self.position: int = None
        self.capture: int = None
        self.items: list = []
        self.restrict_id: str = None
        self.restrict_ids: list = []
        self.restrict_type: str = None
        self.restrict_difficulty: int = None
        self.step_type: list = None
        self.speed_limit_value: int = None
        self.plus_stamina_value: int = None

    def to_dict(self) -> dict:
        r = {
            'position': self.position,
            'capture': self.capture,
        }
        if self.items:
            r['items'] = [i.to_dict() for i in self.items]
        if self.restrict_type:
            r['restrict_type'] = self.restrict_type
            if self.restrict_id:
                r['restrict_id'] = self.restrict_id
            if self.restrict_ids:
                r['restrict_ids'] = self.restrict_ids
            if self.restrict_difficulty is not None:
                r['restrict_difficulty'] = self.restrict_difficulty
        if self.step_type:
            r['step_type'] = self.step_type
        if self.speed_limit_value:
            r['speed_limit_value'] = self.speed_limit_value
        if self.plus_stamina_value:
            r['plus_stamina_value'] = self.plus_stamina_value

        return r

    def from_dict(self, d: dict) -> 'Step':
        self.position = d['position']
        self.capture = d['capture']
        self.restrict_id = d.get('restrict_id')
        self.restrict_ids = d.get('restrict_ids')
        self.restrict_type = d.get('restrict_type')
        self.restrict_difficulty = d.get('restrict_difficulty')
        self.step_type = d.get('step_type', [])
        self.speed_limit_value = d.get('speed_limit_value')
        self.plus_stamina_value = d.get('plus_stamina_value')
        if 'items' in d:
            self.items = [ItemFactory.from_dict(i) for i in d['items']]
        return self


class Map:
    def __init__(self, map_id: str = None) -> None:
        self.map_id: str = map_id
        self.is_legacy: bool = None
        self.is_beyond: bool = None
        self.is_breached: bool = None
        self.beyond_health: int = None
        self.character_affinity: list = []
        self.affinity_multiplier: list = []
        self.chapter: int = None
        self.available_from: int = None
        self.available_to: int = None
        self.is_repeatable: bool = None
        self.require_id: 'str | list[str]' = None
        self.require_type: str = None
        self.require_value: int = None
        self.coordinate: str = None
        self.custom_bg: str = None
        self.stamina_cost: int = None
        self.steps: list = []
        self.__rewards: list = None

        self.require_localunlock_songid: str = None
        self.require_localunlock_challengeid: str = None
        self.chain_info: dict = None

        # self.requires: list[dict] = None

        self.disable_over: bool = None
        self.new_law: str = None

    @property
    def rewards(self) -> list:
        if self.__rewards is None:
            self.get_rewards()
        return self.__rewards

    def get_rewards(self) -> list:
        if self.steps:
            self.__rewards = []
            for step in self.steps:
                if step.items:
                    self.__rewards.append(
                        {'items': [i.to_dict() for i in step.items], 'position': step.position})
        return self.__rewards

    @property
    def step_count(self):
        return len(self.steps)

    def to_dict(self) -> dict:
        if self.chapter is None:
            self.select_map_info()
        r = {
            'map_id': self.map_id,
            'is_legacy': self.is_legacy,
            'is_beyond': self.is_beyond,
            'is_breached': self.is_breached,
            'beyond_health': self.beyond_health,
            'character_affinity': self.character_affinity,
            'affinity_multiplier': self.affinity_multiplier,
            'chapter': self.chapter,
            'available_from': self.available_from,
            'available_to': self.available_to,
            'is_repeatable': self.is_repeatable,
            'require_id': self.require_id,
            'require_type': self.require_type,
            'require_value': self.require_value,
            'coordinate': self.coordinate,
            'custom_bg': self.custom_bg,
            'stamina_cost': self.stamina_cost,
            'step_count': self.step_count,
            'require_localunlock_songid': self.require_localunlock_songid,
            'require_localunlock_challengeid': self.require_localunlock_challengeid,
            'steps': [s.to_dict() for s in self.steps],
        }
        if self.chain_info is not None:
            r['chain_info'] = self.chain_info
        if self.disable_over:
            r['disable_over'] = self.disable_over
        if self.new_law is not None and self.new_law != '':
            r['new_law'] = self.new_law
        return r

    def from_dict(self, raw_dict: dict) -> 'Map':
        self.is_legacy = raw_dict.get('is_legacy', False)
        self.is_beyond = raw_dict.get('is_beyond', False)
        self.is_breached = raw_dict.get('is_breached', False)
        self.beyond_health = raw_dict.get('beyond_health')
        self.character_affinity = raw_dict.get('character_affinity', [])
        self.affinity_multiplier = raw_dict.get('affinity_multiplier', [])
        self.chapter = raw_dict.get('chapter')
        self.available_from = raw_dict.get('available_from', -1)
        self.available_to = raw_dict.get('available_to', 9999999999999)
        self.is_repeatable = raw_dict.get('is_repeatable')
        self.require_id = raw_dict.get('require_id', '')
        self.require_type = raw_dict.get('require_type', '')
        self.require_value = raw_dict.get('require_value', 1)
        self.coordinate = raw_dict.get('coordinate')
        self.custom_bg = raw_dict.get('custom_bg', '')
        self.stamina_cost = raw_dict.get('stamina_cost')
        self.require_localunlock_songid = raw_dict.get(
            'require_localunlock_songid', '')
        self.require_localunlock_challengeid = raw_dict.get(
            'require_localunlock_challengeid', '')
        self.chain_info = raw_dict.get('chain_info')
        self.steps = [Step().from_dict(s) for s in raw_dict.get('steps')]

        self.disable_over = raw_dict.get('disable_over')
        self.new_law = raw_dict.get('new_law')
        return self

    def select_map_info(self):
        '''获取地图信息'''
        self.from_dict(get_world_info(self.map_id))


class UserMap(Map):
    '''
        用户地图类
        parameters: `user` - `User`类或者子类的实例
    '''

    def __init__(self, c=None, map_id: str = None, user=None) -> None:
        super().__init__(map_id)
        self.c = c
        self.curr_position: int = None
        self.curr_capture: int = None
        self.is_locked: bool = None

        self.prev_position: int = None
        self.prev_capture: int = None

        self.user = user

    @property
    def rewards_for_climbing(self) -> list:
        rewards = []
        for i in range(self.prev_position+1, self.curr_position+1):
            step = self.steps[i]
            if step.items:
                rewards.append(
                    {'items': step.items, 'position': step.position})

        return rewards

    def rewards_for_climbing_to_dict(self) -> list:
        rewards = []
        for i in range(self.prev_position+1, self.curr_position+1):
            step = self.steps[i]
            if step.items:
                rewards.append(
                    {'items': [i.to_dict() for i in step.items], 'position': step.position})

        return rewards

    @property
    def steps_for_climbing(self) -> list:
        return self.steps[self.prev_position:self.curr_position+1]

    def to_dict(self, has_map_info: bool = False, has_steps: bool = False, has_rewards: bool = False) -> dict:
        if self.is_locked is None:
            self.select()
        if has_map_info:
            if self.chapter is None:
                self.select_map_info()
            r = super().to_dict()
            r['curr_position'] = self.curr_position
            r['curr_capture'] = self.curr_capture
            r['is_locked'] = self.is_locked
            r['user_id'] = self.user.user_id
            # memory_boost_ticket
            if not has_steps:
                del r['steps']
            if has_rewards:
                r['rewards'] = self.rewards
        else:
            r = {
                'map_id': self.map_id,
                'curr_position': self.curr_position,
                'curr_capture': self.curr_capture,
                'is_locked': self.is_locked,
                'user_id': self.user.user_id,
            }
        return r

    def initialize(self):
        '''初始化数据库信息'''
        self.c.execute('''insert into user_world values(:a,:b,0,0,1)''', {
                       'a': self.user.user_id, 'b': self.map_id})

    def update(self):
        '''向数据库更新信息'''
        self.c.execute('''update user_world set curr_position=:a,curr_capture=:b,is_locked=:c where user_id=:d and map_id=:e''', {
                       'a': self.curr_position, 'b': self.curr_capture, 'c': 1 if self.is_locked else 0, 'd': self.user.user_id, 'e': self.map_id})

    def select(self):
        '''获取用户在此地图的信息'''
        self.c.execute('''select curr_position, curr_capture, is_locked from user_world where map_id = :a and user_id = :b''',
                       {'a': self.map_id, 'b': self.user.user_id})
        x = self.c.fetchone()
        if x:
            self.curr_position = x[0]
            self.curr_capture = x[1]
            self.is_locked = x[2] == 1
        else:
            self.curr_position = 0
            self.curr_capture = 0
            self.is_locked = True
            self.initialize()

    def change_user_current_map(self):
        '''改变用户当前地图为此地图'''
        self.user.current_map = self
        self.c.execute('''update user set current_map = :a where user_id=:b''', {
            'a': self.map_id, 'b': self.user.user_id})

    def unlock(self) -> bool:
        '''解锁用户此地图，返回成功与否bool值'''
        self.select()

        if self.is_locked:
            self.is_locked = False
            self.curr_position = 0
            self.curr_capture = 0
            self.select_map_info()
            if self.require_type is not None and self.require_type != '':
                if self.require_type in ['pack', 'single']:
                    item = ItemFactory(self.c).get_item(self.require_type)
                    item.item_id = self.require_id
                    item.select_user_item(self.user)
                    if not item.amount:
                        self.is_locked = True

            self.update()

        return not self.is_locked

    def climb(self, step_value: float) -> None:
        '''爬梯子，数值非负'''
        if step_value < 0:
            raise InputError('`Step_value` must be non-negative.')
        if self.curr_position is None:
            self.select()
        if self.is_beyond is None:
            self.select_map_info()
        if self.is_locked:
            raise MapLocked('The map is locked.')

        self.prev_capture = self.curr_capture
        self.prev_position = self.curr_position

        if self.is_beyond:  # beyond判断
            dt = self.beyond_health - self.prev_capture
            self.curr_capture = self.prev_capture + \
                step_value if dt >= step_value else self.beyond_health

            i = 0
            t = self.prev_capture + step_value
            while i < self.step_count and t > 0:
                dt = self.steps[i].capture
                if dt > t:
                    t = 0
                else:
                    t -= dt
                    i += 1
            if i >= self.step_count:
                self.curr_position = self.step_count - 1
            else:
                self.curr_position = i

        else:
            i = self.prev_position
            j = self.prev_capture
            t = step_value
            while t > 0 and i < self.step_count:
                dt = self.steps[i].capture - j
                if dt > t:
                    j += t
                    t = 0
                else:
                    t -= dt
                    j = 0
                    i += 1
            if i >= self.step_count:
                self.curr_position = self.step_count - 1
                self.curr_capture = 0
            else:
                self.curr_position = i
                self.curr_capture = j

    def reclimb(self, step_value: float) -> None:
        '''重新爬梯子计算'''
        self.curr_position = self.prev_position
        self.curr_capture = self.prev_capture
        self.climb(step_value)


class Stamina:
    '''
        体力类
    '''

    def __init__(self) -> None:
        self.__stamina: int = None
        self.max_stamina_ts: int = None

    def set_value(self, max_stamina_ts: int, stamina: int):
        self.max_stamina_ts = int(max_stamina_ts) if max_stamina_ts else 0
        self.__stamina = int(stamina) if stamina else Constant.MAX_STAMINA

    @property
    def stamina(self) -> int:
        '''通过计算得到当前的正确体力值'''
        stamina = round(Constant.MAX_STAMINA - (self.max_stamina_ts -
                                                int(time()*1000)) / Constant.STAMINA_RECOVER_TICK)

        if stamina >= Constant.MAX_STAMINA:
            if self.__stamina >= Constant.MAX_STAMINA:
                stamina = self.__stamina
            else:
                stamina = Constant.MAX_STAMINA

        return stamina

    @stamina.setter
    def stamina(self, value: int) -> None:
        '''设置体力值，此处会导致max_stamina_ts变化'''
        self.__stamina = round(value)
        self.max_stamina_ts = int(
            time()*1000) - (self.__stamina-Constant.MAX_STAMINA) * Constant.STAMINA_RECOVER_TICK


class UserStamina(Stamina):
    '''
        用户体力类

        parameter: `user` - `User`类或子类的实例
    '''

    def __init__(self, c=None, user=None) -> None:
        super().__init__()
        self.c = c
        self.user = user

    def select(self):
        '''获取用户体力信息'''
        self.c.execute('''select max_stamina_ts, staminafrom user where user_id = :a''',
                       {'a': self.user.user_id})
        x = self.c.fetchone()
        if not x:
            raise NoData('The user does not exist.')
        self.set_value(x[0], x[1])

    def update(self):
        '''向数据库更新信息'''
        self.c.execute('''update user set max_stamina_ts=:b, stamina=:a where user_id=:c''', {
                       'a': self.stamina, 'b': self.max_stamina_ts, 'c': self.user.user_id})


class WorldSkillMixin:
    def before_calculate(self) -> None:
        factory_dict = {
            'skill_vita': self._skill_vita,
            'skill_mika': self._skill_mika,
            'skill_ilith_ivy': self._skill_ilith_ivy,
            'ilith_awakened_skill': self._ilith_awakened_skill,
            'skill_hikari_vanessa': self._skill_hikari_vanessa,
            'skill_mithra': self._skill_mithra
        }
        if self.user_play.beyond_gauge == 0 and self.character_used.character_id == 35 and self.character_used.skill_id_displayed:
            self._special_tempest()

        if self.character_used.skill_id_displayed in factory_dict:
            factory_dict[self.character_used.skill_id_displayed]()

    def after_climb(self) -> None:
        factory_dict = {
            'eto_uncap': self._eto_uncap,
            'ayu_uncap': self._ayu_uncap,
            'skill_fatalis': self._skill_fatalis,
            'skill_amane': self._skill_amane,
            'skill_maya': self._skill_maya,
            'luna_uncap': self._luna_uncap,
            'skill_kanae_uncap': self._skill_kanae_uncap
        }
        if self.character_used.skill_id_displayed in factory_dict:
            factory_dict[self.character_used.skill_id_displayed]()

    def _special_tempest(self) -> None:
        '''风暴对立技能，prog随全角色等级提升'''
        if self.character_used.database_table_name == 'user_char_full':
            self.prog_tempest = 60
        else:
            self.c.execute(
                '''select sum(level) from user_char where user_id=?''', (self.user.user_id,))
            x = self.c.fetchone()
            self.prog_tempest = int(x[0]) / 10 if x else 0
        if self.prog_tempest > 60:
            self.prog_tempest = 60
        elif self.prog_tempest < 0:
            self.prog_tempest = 0

    def _skill_vita(self) -> None:
        '''
            vita技能，overdrive随回忆率提升，提升量最多为10
            此处采用线性函数
        '''
        self.over_skill_increase = 0
        if 0 < self.user_play.health <= 100:
            self.over_skill_increase = self.user_play.health / 10

    def _eto_uncap(self) -> None:
        '''eto觉醒技能，获得残片奖励时世界模式进度加7'''
        fragment_flag = False

        for i in self.user.current_map.rewards_for_climbing:
            for j in i['items']:
                if j.item_type == 'fragment':
                    fragment_flag = True
                    break
            if fragment_flag:
                break

        if fragment_flag:
            self.character_bonus_progress_normalized = Constant.ETO_UNCAP_BONUS_PROGRESS

        self.user.current_map.reclimb(self.final_progress)

    def _luna_uncap(self) -> None:
        '''luna觉醒技能，限制格开始时世界模式进度加 7，偷懒重爬（因为 map 信息还未获取）'''
        x: 'Step' = self.user.current_map.steps_for_climbing[0]
        if x.restrict_id and x.restrict_type:
            self.self.character_bonus_progress_normalized = Constant.LUNA_UNCAP_BONUS_PROGRESS
            self.user.current_map.reclimb(self.final_progress)

    def _ayu_uncap(self) -> None:
        '''ayu 觉醒技能，世界模式进度随机变动 [-5, -5]，但不会小于 0'''

        self.character_bonus_progress_normalized = randint(
            -Constant.AYU_UNCAP_BONUS_PROGRESS, Constant.AYU_UNCAP_BONUS_PROGRESS)

        if self.progress_normalized + self.character_bonus_progress_normalized < 0:
            self.character_bonus_progress_normalized = -self.progress_normalized

        self.user.current_map.reclimb(self.final_progress)

    def _skill_fatalis(self) -> None:
        '''hikari fatalis技能，世界模式超载，打完休息60分钟'''

        self.user.world_mode_locked_end_ts = int(
            time()*1000) + Constant.SKILL_FATALIS_WORLD_LOCKED_TIME
        self.user.update_user_one_column('world_mode_locked_end_ts')

    def _skill_amane(self) -> None:
        '''
        amane技能，起始格为限速或随机，成绩小于EX时，世界模式进度减半
        '''
        x: 'Step' = self.user.current_map.steps_for_climbing[0]
        if ('randomsong' in x.step_type or 'speedlimit' in x.step_type) and self.user_play.song_grade < 5:
            self.character_bonus_progress_normalized = -self.progress_normalized / 2
            self.user.current_map.reclimb(self.final_progress)

    def _ilith_awakened_skill(self) -> None:
        '''
        ilith 觉醒技能，曲目通关时步数+6，wiki 说是 prog 值+6
        '''
        if self.user_play.health > 0:
            self.prog_skill_increase = 6

    def _skill_mika(self) -> None:
        '''
        mika 技能，通关特定曲目能力值翻倍
        '''
        if self.user_play.song.song_id in Constant.SKILL_MIKA_SONGS and self.user_play.clear_type != 0:
            self.over_skill_increase = self.character_used.overdrive.get_value(
                self.character_used.level)
            self.prog_skill_increase = self.character_used.prog.get_value(
                self.character_used.level)

    def _skill_mithra(self) -> None:
        '''
        mithra 技能，每 150 combo 增加世界模式进度+1
        '''
        if self.user_play.combo_interval_bonus:
            self.character_bonus_progress_normalized = self.user_play.combo_interval_bonus

    def _skill_ilith_ivy(self) -> None:
        '''
        ilith & ivy 技能，根据 skill_cytusii_flag 来增加三个数值，最高生命每过 20 就对应数值 +10
        '''
        if not self.user_play.skill_cytusii_flag:
            return
        x = self.user_play.skill_cytusii_flag[:
                                              self.user_play.highest_health // 20]
        self.over_skill_increase = x.count('2') * 10
        self.prog_skill_increase = x.count('1') * 10

    def _skill_hikari_vanessa(self) -> None:
        '''
        hikari & vanessa 技能，根据 skill_cytusii_flag 来减少三个数值，最高生命每过 20 就对应数值 -10
        '''
        if not self.user_play.skill_cytusii_flag:
            return
        x = self.user_play.skill_cytusii_flag[:5 -
                                              self.user_play.lowest_health // 20]
        self.over_skill_increase = -x.count('2') * 10
        self.prog_skill_increase = -x.count('1') * 10

    def _skill_maya(self) -> None:
        '''
        maya 技能，skill_flag 为 1 时，世界模式进度翻倍
        '''
        if self.character_used.skill_flag:
            self.character_bonus_progress_normalized = self.progress_normalized
            self.user.current_map.reclimb(self.final_progress)
        self.character_used.change_skill_state()

    def _skill_kanae_uncap(self) -> None:
        '''
        kanae 觉醒技能，保存世界模式 progress 并在下次结算
        直接加减在 progress 最后
        技能存储 base_progress * PROG / 50，下一次消耗全部存储值（无视技能和搭档，但需要非技能隐藏状态）
        '''
        self.kanae_stored_progress = self.progress_normalized
        self.user.current_map.reclimb(self.final_progress)


class BaseWorldPlay(WorldSkillMixin):
    '''
        世界模式打歌类，处理特殊角色技能，联动UserMap和UserPlay

        parameter: `user` - `UserOnline`类或子类的实例
        'user_play` - `UserPlay`类的实例
    '''

    def __init__(self, c=None, user=None, user_play=None) -> None:
        self.c = c
        self.user = user
        self.user_play = user_play
        self.character_used = None

        self.character_bonus_progress_normalized: float = None

        # wpaid: str

    def to_dict(self) -> dict:
        arcmap: 'UserMap' = self.user.current_map
        r = {
            "rewards": arcmap.rewards_for_climbing_to_dict(),
            "exp": self.character_used.level.exp,
            "level": self.character_used.level.level,
            "base_progress": self.base_progress,
            "progress": self.final_progress,
            "user_map": {
                "user_id": self.user.user_id,
                "curr_position": arcmap.curr_position,
                "curr_capture": arcmap.curr_capture,
                "is_locked": arcmap.is_locked,
                "map_id": arcmap.map_id,
                "prev_capture": arcmap.prev_capture,
                "prev_position": arcmap.prev_position,
                "beyond_health": arcmap.beyond_health
            },
            "char_stats": {
                "character_id": self.character_used.character_id,
                "frag": self.character_used.frag_value,
                "prog": self.character_used.prog_value,
                "overdrive": self.character_used.overdrive_value
            },
            "current_stamina": self.user.stamina.stamina,
            "max_stamina_ts": self.user.stamina.max_stamina_ts,
            'world_mode_locked_end_ts': self.user.world_mode_locked_end_ts,
            'beyond_boost_gauge': self.user.beyond_boost_gauge,
            # 'wpaid': 'helloworld',  # world play id ???
            # progress_before_sub_boost
            # progress_sub_boost_amount
            # subscription_multiply
        }

        if self.character_used.skill_id_displayed == 'skill_maya':
            r['char_stats']['skill_state'] = self.character_used.skill_state

        if self.user_play.stamina_multiply != 1:
            r['stamina_multiply'] = self.user_play.stamina_multiply
        if self.user_play.fragment_multiply != 100:
            r['fragment_multiply'] = self.user_play.fragment_multiply
        if self.user_play.prog_boost_multiply != 0:  # 源韵强化
            r['prog_boost_multiply'] = self.user_play.prog_boost_multiply

        return r

    @property
    def beyond_boost_gauge_addition(self) -> float:
        # guessed by Lost-MSth
        return 2.45 * self.user_play.rating ** 0.5 + 27

    @property
    def step_times(self) -> float:
        raise NotImplementedError

    @property
    def exp_times(self) -> float:
        return self.user_play.stamina_multiply * (self.user_play.prog_boost_multiply / 100 + 1)

    @property
    def character_bonus_progress(self) -> float:
        return self.character_bonus_progress_normalized * self.step_times

    @property
    def base_progress(self) -> float:
        raise NotImplementedError

    @property
    def progress_normalized(self) -> float:
        raise NotImplementedError

    @property
    def final_progress(self) -> float:
        raise NotImplementedError

    def before_update(self) -> None:
        if self.user_play.prog_boost_multiply != 0:
            self.user.update_user_one_column('prog_boost', 0)

        self.user_play.clear_play_state()
        # self.user.select_user_about_world_play()

        self.character_used = Character()

        self.user.character.select_character_info()
        if not self.user.is_skill_sealed:
            self.character_used = self.user.character
            if self.user_play.beyond_gauge == 0 and self.user.kanae_stored_prog > 0:
                # 实在不想拆开了，在这里判断一下，注意这段不会在 BeyondWorldPlay 中执行
                self.kanae_added_progress = self.user.kanae_stored_prog
        else:
            self.character_used.character_id = self.user.character.character_id
            self.character_used.level.level = self.user.character.level.level
            self.character_used.level.exp = self.user.character.level.exp
            self.character_used.frag.set_parameter(50, 50, 50)
            self.character_used.prog.set_parameter(50, 50, 50)
            self.character_used.overdrive.set_parameter(50, 50, 50)

        # self.user.current_map.select_map_info()

    def after_update(self) -> None:

        for i in self.user.current_map.rewards_for_climbing:  # 物品分发
            for j in i['items']:
                j.c = self.c
                j.user_claim_item(self.user)

        x: 'Step' = self.user.current_map.steps_for_climbing[-1]
        if x.step_type:
            if 'plusstamina' in x.step_type and x.plus_stamina_value:
                # 体力格子
                self.user.stamina.stamina += x.plus_stamina_value
                self.user.stamina.update()

        # 角色升级
        if self.character_used.database_table_name == 'user_char':
            self.character_used.upgrade(
                self.user, self.exp_times*self.user_play.rating*6)

        if self.user.current_map.curr_position == self.user.current_map.step_count-1 and self.user.current_map.is_repeatable:  # 循环图判断
            self.user.current_map.curr_position = 0

        self.user.current_map.update()

    def update(self) -> None:
        '''世界模式更新'''
        self.before_update()
        self.before_calculate()
        self.user.current_map.climb(self.final_progress)
        self.after_climb()
        self.after_update()


class WorldPlay(BaseWorldPlay):
    def __init__(self, c=None, user=None, user_play=None) -> None:
        super().__init__(c, user, user_play)

        self.prog_tempest: float = None
        self.prog_skill_increase: float = None

        self.kanae_added_progress: float = None  # 群愿往外拿
        self.kanae_stored_progress: float = None  # 往群愿里塞
        # self.user.kanae_stored_prog: float 群愿有的

    def to_dict(self) -> dict:
        r = super().to_dict()

        # 基础进度加上搭档倍数 不带 character_bonus_progress 但是带 kanae 技能
        r['progress_partial_after_stat'] = self.progress_normalized

        if self.character_bonus_progress_normalized is not None:
            r['character_bonus_progress'] = self.character_bonus_progress_normalized
            # 不懂为什么两个玩意一样
            r['character_bonus_progress_normalized'] = self.character_bonus_progress_normalized

        if self.prog_skill_increase is not None:
            r['char_stats']['prog_skill_increase'] = self.prog_skill_increase

        if self.prog_tempest is not None:
            r['char_stats']['prog'] += self.prog_tempest  # 没试过要不要这样
            r['char_stats']['prog_tempest'] = self.prog_tempest

        if self.kanae_added_progress is not None:
            r['kanae_added_progress'] = self.kanae_added_progress

        if self.kanae_stored_progress is not None:
            r['kanae_stored_progress'] = self.kanae_stored_progress

        r['partner_adjusted_prog'] = self.partner_adjusted_prog

        r["user_map"]["steps"] = [x.to_dict()
                                  for x in self.user.current_map.steps_for_climbing]
        return r

    @property
    def step_times(self) -> float:
        return self.user_play.stamina_multiply * self.user_play.fragment_multiply / 100 * (self.user_play.prog_boost_multiply / 100 + 1)

    @property
    def character_bonus_progress(self) -> float:
        return self.character_bonus_progress_normalized * self.step_times

    @property
    def base_progress(self) -> float:
        return 2.5 + 2.45 * self.user_play.rating**0.5

    @property
    def final_progress(self) -> float:
        return (self.progress_normalized + (self.character_bonus_progress_normalized or 0)) * self.step_times + (self.kanae_added_progress or 0) - (self.kanae_stored_progress or 0)

    @property
    def partner_adjusted_prog(self) -> float:
        prog = self.character_used.prog.get_value(
            self.character_used.level)
        if self.prog_tempest:
            prog += self.prog_tempest
        if self.prog_skill_increase:
            prog += self.prog_skill_increase
        return prog

    @property
    def progress_normalized(self) -> float:
        return self.base_progress * (self.partner_adjusted_prog / 50)

    def after_update(self) -> None:
        '''世界模式更新'''
        super().after_update()

        # 更新byd大招蓄力条
        self.user.beyond_boost_gauge += self.beyond_boost_gauge_addition
        self.user.beyond_boost_gauge = min(self.user.beyond_boost_gauge, 200)
        self.user.update_user_one_column(
            'beyond_boost_gauge', self.user.beyond_boost_gauge)

        # 更新kanae存储进度
        if self.kanae_stored_progress is not None:
            self.user.kanae_stored_prog = self.kanae_stored_progress
            self.user.update_user_one_column(
                'kanae_stored_prog', self.user.kanae_stored_prog)
            return
        if self.kanae_added_progress is None:
            return
        self.kanae_stored_progress = 0
        self.user.update_user_one_column('kanae_stored_prog', 0)


class BeyondWorldPlay(BaseWorldPlay):

    def __init__(self, c=None, user=None, user_play=None) -> None:
        super().__init__(c, user, user_play)
        self.over_skill_increase: float = None

    @property
    def step_times(self) -> float:
        return self.user_play.stamina_multiply * self.user_play.fragment_multiply / 100 * (1 + self.user_play.prog_boost_multiply / 100 + self.user_play.beyond_boost_gauge_usage / 100)

    @property
    def affinity_multiplier(self) -> float:
        if self.user.current_map.character_affinity is not None and self.character_used.character_id is not None and self.character_used.character_id in self.user.current_map.character_affinity:
            return self.user.current_map.affinity_multiplier[self.user.current_map.character_affinity.index(self.character_used.character_id)]
        return 1

    @property
    def base_progress(self) -> float:
        return self.user_play.rating**0.5 * 0.43 + (25/28 if self.user_play.clear_type == 0 else 75/28)

    @property
    def final_progress(self) -> float:
        return self.progress_normalized * self.step_times

    @property
    def progress_normalized(self) -> float:
        overdrive = self.character_used.overdrive_value
        if self.over_skill_increase:
            overdrive += self.over_skill_increase

        return self.base_progress * (overdrive / 50) * self.affinity_multiplier

    def to_dict(self) -> dict:
        r = super().to_dict()

        # byd 进度 没有加上源韵强化 和 boost 的数值
        r['pre_boost_progress'] = self.progress_normalized * \
            self.user_play.fragment_multiply / 100

        # r['partner_multiply'] = self.affinity_multiplier  # ?

        if self.over_skill_increase is not None:
            r['char_stats']['over_skill_increase'] = self.over_skill_increase

        r["user_map"]["steps"] = len(self.user.current_map.steps_for_climbing)
        r['affinity_multiply'] = self.affinity_multiplier
        if self.user_play.beyond_boost_gauge_usage != 0:
            r['beyond_boost_gauge_usage'] = self.user_play.beyond_boost_gauge_usage

        return r

    def after_update(self) -> None:
        super().after_update()
        if self.user_play.beyond_boost_gauge_usage != 0 and self.user_play.beyond_boost_gauge_usage <= self.user.beyond_boost_gauge:
            self.user.beyond_boost_gauge -= self.user_play.beyond_boost_gauge_usage
            if abs(self.user.beyond_boost_gauge) <= 1e-5:
                self.user.beyond_boost_gauge = 0
            self.user.update_user_one_column(
                'beyond_boost_gauge', self.user.beyond_boost_gauge)


class WorldLawMixin:
    def breached_before_calculate(self) -> None:
        factory_dict = {
            'over100_step50': self._over100_step50,
            'frag50': self._frag50,
            'lowlevel': self._lowlevel,
            'antiheroism': self._antiheroism
        }
        if self.user.current_map.new_law in factory_dict:
            factory_dict[self.user.current_map.new_law]()

    def _over100_step50(self) -> None:
        '''PROG = OVER + STEP / 2'''
        over = self.character_used.overdrive_value + self.over_skill_increase
        prog = self.character_used.prog_value + self.prog_skill_increase
        self.new_law_prog = over + prog / 2

    def _frag50(self) -> None:
        '''PROG x= FRAG'''
        self.new_law_prog = self.character_used.frag_value

    def _lowlevel(self) -> None:
        '''PROG x= max(1.0, 2.0 - 0.1 x LEVEL)'''
        self.new_law_prog = 50 * \
            max(1, 2 - 0.1 * self.character_used.level.level)

    def _antiheroism(self) -> None:
        '''PROG = OVER - ||OVER-FRAG|-|OVER-STEP||'''
        over = self.character_used.overdrive_value + self.over_skill_increase
        prog = self.character_used.prog_value + self.prog_skill_increase
        x = abs(over - self.character_used.frag_value)
        y = abs(over - prog)
        self.new_law_prog = over - abs(x - y)


class BreachedWorldPlay(BeyondWorldPlay, WorldLawMixin):
    def __init__(self, c=None, user=None, user_play=None) -> None:
        super().__init__(c, user, user_play)
        self.new_law_prog: float = None

    @property
    def new_law_multiply(self) -> float:
        if self.new_law_prog is None:
            return 1
        return self.new_law_prog / 50

    @property
    def affinity_multiplier(self) -> float:
        return 1

    @property
    def progress_normalized(self) -> float:
        if self.user.current_map.disable_over:
            return self.base_progress * self.new_law_multiply

        overdrive = self.character_used.overdrive_value
        if self.over_skill_increase:
            overdrive += self.over_skill_increase
        return self.base_progress * (overdrive / 50) * self.new_law_multiply

    def to_dict(self) -> dict:
        r = super().to_dict()
        r['new_law_multiply'] = self.new_law_multiply
        return r

    def update(self) -> None:
        self.before_update()
        self.before_calculate()
        self.breached_before_calculate()
        self.user.current_map.climb(self.final_progress)
        self.after_climb()
        self.after_update()
