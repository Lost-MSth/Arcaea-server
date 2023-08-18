from .config_manager import Config
from .error import DataExist, InputError, ItemNotEnough, ItemUnavailable, NoData


class Item:
    item_type = None

    def __init__(self, c=None) -> None:
        self.item_id = None
        self.__amount = None
        self.is_available = None
        self.c = c

    def __eq__(self, other: 'Item') -> bool:
        return self.item_id == other.item_id and self.item_type == other.item_type

    @property
    def amount(self):
        return self.__amount

    @amount.setter
    def amount(self, value: int):
        self.__amount = int(value)

    def to_dict(self, has_is_available: bool = False, has_amount: bool = True) -> dict:
        r = {
            'id': self.item_id,
            'type': self.item_type
        }
        if has_amount:
            r['amount'] = self.amount
        if has_is_available:
            r['is_available'] = self.is_available
        return r

    def user_claim_item(self, user):
        # parameter: user - User类或子类的实例
        pass

    def select_exists(self):
        self.c.execute('''select exists(select * from item where item_id=? and type=?)''',
                       (self.item_id, self.item_type))
        return bool(self.c.fetchone()[0])

    def insert(self, ignore: bool = False):
        sql = '''insert into item values(?,?,?)''' if not ignore else '''insert or ignore into item values(?,?,?)'''
        self.c.execute(sql, (self.item_id, self.item_type, self.is_available))

    def delete(self):
        self.c.execute('''delete from item where item_id=? and type=?''',
                       (self.item_id, self.item_type))

    def update(self):
        self.c.execute('''update item set is_available=? where item_id=? and type=?''',
                       (self.is_available, self.item_id, self.item_type))

    def select(self):
        self.c.execute('''select is_available from item where item_id=? and type=?''',
                       (self.item_id, self.item_type))
        x = self.c.fetchone()
        if not x:
            raise NoData(
                f'No such item `{self.item_type}`: `{self.item_id}`', api_error_code=-121)
        self.is_available = x[0]


class UserItem(Item):

    def __init__(self, c=None) -> None:
        super().__init__()
        self.c = c
        self.user = None

    def select_user_item(self, user=None):
        '''
            查询用户item

            parameter: `user` - `User`类或子类的实例
        '''
        if user is not None:
            self.user = user
        self.c.execute('''select amount from user_item where user_id=? and item_id=? and type=?''',
                       (self.user.user_id, self.item_id, self.item_type))
        x = self.c.fetchone()
        if x:
            self.amount = x[0] if x[0] is not None else 1
        else:
            self.amount = 0


class NormalItem(UserItem):
    def __init__(self, c) -> None:
        super().__init__()
        self.c = c

    def user_claim_item(self, user):
        self.user = user
        if not self.is_available:
            self.c.execute(
                '''select is_available from item where item_id=? and type=?''', (self.item_id, self.item_type))
            x = self.c.fetchone()
            if x:
                if x[0] == 0:
                    self.is_available = False
                    raise ItemUnavailable('The item is unavailable.')
                self.is_available = True
            else:
                raise NoData('No item data.')

        self.c.execute('''select exists(select * from user_item where user_id=? and item_id=? and type=?)''',
                       (self.user.user_id, self.item_id, self.item_type))
        if self.c.fetchone() == (0,):
            self.c.execute('''insert into user_item values(:a,:b,:c,1)''',
                           {'a': self.user.user_id, 'b': self.item_id, 'c': self.item_type})


class PositiveItem(UserItem):
    def __init__(self, c) -> None:
        super().__init__()
        self.c = c

    def user_claim_item(self, user):
        '''添加或使用用户item，注意是+amount'''
        self.user = user
        self.c.execute('''select amount from user_item where user_id=? and item_id=? and type=?''',
                       (self.user.user_id, self.item_id, self.item_type))
        x = self.c.fetchone()
        if x:
            if x[0] + self.amount < 0:  # 数量不足
                raise ItemNotEnough(
                    'The user does not have enough `%s`.' % self.item_id)
            self.c.execute('''update user_item set amount=? where user_id=? and item_id=? and type=?''',
                           (x[0]+self.amount, self.user.user_id, self.item_id, self.item_type))
        else:
            if self.amount < 0:  # 添加数量错误
                raise InputError(
                    'The amount of `%s` is wrong.' % self.item_id)
            self.c.execute('''insert into user_item values(?,?,?,?)''',
                           (self.user.user_id, self.item_id, self.item_type, self.amount))


class ItemCore(PositiveItem):
    item_type = 'core'

    def __init__(self, c, core_type: str = '', amount: int = 0) -> None:
        super().__init__(c)
        self.is_available = True
        self.item_id = core_type
        self.amount = amount

    def __str__(self) -> str:
        return self.item_id + '_' + str(self.amount)

    def to_dict(self, has_is_available: bool = False, has_amount: bool = True, character_format: bool = False) -> dict:
        if character_format:
            # 搭档的core是特殊格式的
            return {'core_type': self.item_id, 'amount': self.amount}
        return super().to_dict(has_is_available=has_is_available, has_amount=has_amount)

    def user_claim_item(self, user, reverse: bool = False) -> None:
        # 骚操作，将amount变为负数后使用再变回来
        if reverse:
            self.amount = -self.amount
        super().user_claim_item(user)
        if reverse:
            self.amount = -self.amount


class ItemCharacter(UserItem):
    item_type = 'character'

    def __init__(self, c) -> None:
        super().__init__()
        self.c = c
        self.is_available = True

    def set_id(self, character_id: str) -> None:
        # 将name: str转为character_id: int存到item_id里
        if character_id.isdigit():
            self.item_id = int(character_id)
        else:
            self.c.execute(
                '''select character_id from character where name=?''', (character_id,))
            x = self.c.fetchone()
            if x:
                self.item_id = x[0]
            else:
                raise NoData('No character `%s`.' % character_id)

    def user_claim_item(self, user):
        if not isinstance(self.item_id, int):
            self.set_id(self.item_id)

        self.c.execute(
            '''select exists(select * from user_char where user_id=? and character_id=?)''', (user.user_id, self.item_id))
        if self.c.fetchone() == (0,):
            self.c.execute(
                '''insert into user_char values(?,?,1,0,0,0,0)''', (user.user_id, self.item_id))


class Memory(UserItem):
    item_type = 'memory'

    def __init__(self, c) -> None:
        super().__init__()
        self.c = c
        self.is_available = True

    def user_claim_item(self, user):
        self.c.execute(
            '''select ticket from user where user_id=?''', (user.user_id,))
        x = self.c.fetchone()
        if x is not None:
            self.c.execute('''update user set ticket=? where user_id=?''',
                           (x[0]+self.amount, user.user_id))
        else:
            raise NoData('The ticket of the user is null.')


class Fragment(UserItem):
    item_type = 'fragment'

    def __init__(self, c) -> None:
        super().__init__()
        self.c = c
        self.is_available = True

    def user_claim_item(self, user):
        pass

    def __str__(self) -> str:
        return 'fragment' + str(self.amount)


class Anni5tix(PositiveItem):
    item_type = 'anni5tix'

    def __init__(self, c) -> None:
        super().__init__(c)
        self.is_available = True


class WorldSong(NormalItem):
    item_type = 'world_song'

    def __init__(self, c) -> None:
        super().__init__(c)
        self.is_available = True


class WorldUnlock(NormalItem):
    item_type = 'world_unlock'

    def __init__(self, c) -> None:
        super().__init__(c)
        self.is_available = True


class CourseBanner(NormalItem):
    item_type = 'course_banner'

    def __init__(self, c) -> None:
        super().__init__(c)
        self.is_available = True

    def __str__(self) -> str:
        return str(self.item_id)


class Single(NormalItem):
    item_type = 'single'


class Pack(NormalItem):
    item_type = 'pack'


class ProgBoost(UserItem):
    item_type = 'prog_boost_300'

    def __init__(self, c) -> None:
        super().__init__(c)

    def user_claim_item(self, user):
        '''
            世界模式prog_boost

            parameters: `user` - `UserOnline`类或子类的实例
        '''
        user.update_user_one_column('prog_boost', 300)


class Stamina6(UserItem):
    item_type = 'stamina6'

    def __init__(self, c) -> None:
        super().__init__(c)

    def user_claim_item(self, user):
        '''
            世界模式记忆源点或残片买体力+6
            顺手清一下世界模式过载状态
        '''
        user.select_user_about_stamina()
        user.stamina.stamina += 6
        user.stamina.update()
        user.update_user_one_column('world_mode_locked_end_ts', -1)


class ItemFactory:
    def __init__(self, c=None) -> None:
        self.c = c

    def get_item(self, item_type: str):
        '''
            根据item_type实例化对应的item类
            return: Item类或子类的实例
        '''
        if item_type == 'core':
            return ItemCore(self.c)
        elif item_type == 'character':
            return ItemCharacter(self.c)
        elif item_type == 'memory':
            return Memory(self.c)
        elif item_type == 'anni5tix':
            return Anni5tix(self.c)
        elif item_type == 'world_song':
            return WorldSong(self.c)
        elif item_type == 'world_unlock':
            return WorldUnlock(self.c)
        elif item_type == 'single':
            return Single(self.c)
        elif item_type == 'pack':
            return Pack(self.c)
        elif item_type == 'fragment':
            return Fragment(self.c)
        elif item_type == 'prog_boost_300':
            return ProgBoost(self.c)
        elif item_type == 'stamina6':
            return Stamina6(self.c)
        elif item_type == 'course_banner':
            return CourseBanner(self.c)
        else:
            raise InputError(
                f'The item type `{item_type}` is invalid.', api_error_code=-120)

    @classmethod
    def from_dict(cls, d: dict, c=None):
        '''注意这里没有处理character_id的转化，是为了世界模式的map服务的'''
        if 'item_type' in d:
            item_type = d['item_type']
        elif 'type' in d:
            item_type = d['type']
        else:
            raise InputError('The dict of item is wrong.')
        i = cls().get_item(item_type)
        if c is not None:
            i.c = c
        if 'item_id' in d:
            i.item_id = d['item_id']
        elif 'id' in d:
            i.item_id = d['id']
        else:
            i.item_id = item_type
        i.amount = d.get('amount', 1)
        i.is_available = d.get('is_available', True)
        return i

    @classmethod
    def from_str(cls, s: str, c=None):
        if s.startswith('fragment'):
            item_type = 'fragment'
            item_id = 'fragment'
            amount = int(s[8:])
        elif s.startswith('core'):
            item_type = 'core'
            x = s.split('_')
            item_id = x[0] + '_' + x[1]
            amount = int(x[-1])
        elif s.startswith('course_banner'):
            item_type = 'course_banner'
            item_id = s
            amount = 1
        else:
            raise InputError('The string of item is wrong.')
        i = cls().get_item(item_type)
        if c is not None:
            i.c = c
        i.item_id = item_id
        i.amount = amount
        i.is_available = True
        return i


class UserItemList:
    '''
        用户的item列表
        注意只能查在user_item里面的，character不行
        properties: `user` - `User`类或子类的实例
    '''

    def __init__(self, c=None, user=None):
        self.c = c
        self.user = user

        self.items: list = []

    def select_from_type(self, item_type: str) -> 'UserItemList':
        '''
            根据item_type搜索用户的item
        '''
        if Config.WORLD_SONG_FULL_UNLOCK and item_type == 'world_song' or Config.WORLD_SCENERY_FULL_UNLOCK and item_type == 'world_unlock':
            self.c.execute(
                '''select item_id from item where type=?''', (item_type,))
        else:
            self.c.execute('''select item_id, amount from user_item where type = :a and user_id = :b''', {
                'a': item_type, 'b': self.user.user_id})
        x = self.c.fetchall()
        if not x:
            return self

        self.items: list = []
        for i in x:
            if len(i) > 1:
                amount = i[1] if i[1] is not None else 1
            else:
                amount = 1
            self.items.append(ItemFactory.from_dict(
                {'item_id': i[0], 'amount': amount, 'item_type': item_type}, self.c))
        return self


class CollectionItemMixin:
    '''
       批量修改一些集合中的items
    '''
    collection_item_const = {
        'name': 'collection',
        'table_name': 'collection_item',
        'table_primary_key': 'collection_id',
        'id_name': 'collection_id',
        'items_name': 'items'
    }

    def add_items(self, items: 'list[Item]') -> None:
        collection_id: 'str' = getattr(
            self, self.collection_item_const['id_name'])
        collection_items: 'list[Item]' = getattr(
            self, self.collection_item_const['items_name'])

        for i in items:
            if not i.select_exists():
                raise NoData(
                    f'No such item `{i.item_type}`: `{i.item_id}`', api_error_code=-121)
            if i in collection_items:
                raise DataExist(
                    f'Item `{i.item_type}`: `{i.item_id}` already exists in {self.collection_item_const["name"]} `{collection_id}`', api_error_code=-123)
        self.c.executemany(f'''insert into {self.collection_item_const["table_name"]} values (?, ?, ?, ?)''', [
                           (collection_id, i.item_id, i.item_type, i.amount) for i in items])
        collection_items.extend(items)

    def remove_items(self, items: 'list[Item]') -> None:
        collection_id: 'str' = getattr(
            self, self.collection_item_const['id_name'])
        collection_items: 'list[Item]' = getattr(
            self, self.collection_item_const['items_name'])

        for i in items:
            if i not in collection_items:
                raise NoData(
                    f'No such item `{i.item_type}`: `{i.item_id}` in {self.collection_item_const["name"]} `{collection_id}`', api_error_code=-124)
        self.c.executemany(f'''delete from {self.collection_item_const["table_name"]} where {self.collection_item_const["table_primary_key"]}=? and item_id=? and type=?''', [
                           (collection_id, i.item_id, i.item_type) for i in items])
        for i in items:
            collection_items.remove(i)

    def update_items(self, items: 'list[Item]') -> None:
        collection_id: 'str' = getattr(
            self, self.collection_item_const['id_name'])
        collection_items: 'list[Item]' = getattr(
            self, self.collection_item_const['items_name'])

        for i in items:
            if i not in collection_items:
                raise NoData(
                    f'No such item `{i.item_type}`: `{i.item_id}` in {self.collection_item_const["name"]} `{collection_id}`', api_error_code=-124)
        self.c.executemany(f'''update {self.collection_item_const["table_name"]} set amount=? where {self.collection_item_const["table_primary_key"]}=? and item_id=? and type=?''', [
                           (i.amount, collection_id, i.item_id, i.item_type) for i in items])
        for i in items:
            collection_items[collection_items.index(i)].amount = i.amount
