from sympy import Nor
from .error import NoData, ItemUnavailable, ItemNotEnough, InputError


class Item:
    item_type = None

    def __init__(self) -> None:
        self.item_id = None
        self.__amount = None
        self.is_available = None

    @property
    def amount(self):
        return self.__amount

    @amount.setter
    def amount(self, value: int):
        self.__amount = int(value)

    def user_claim_item(self, user):
        # parameter: user - User类或子类的实例
        pass


class NormalItem(Item):
    def __init__(self, c) -> None:
        super().__init__()
        self.c = c

    def user_claim_item(self, user):
        if not self.is_available:
            self.c.execute(
                '''select is_available from item where item_id=? and type=?''', (self.item_id, self.item_type))
            x = self.c.fetchone()
            if x:
                if x[0] == 0:
                    self.is_available = False
                    raise ItemUnavailable('The item is unavailable.')
                else:
                    self.is_available = True
            else:
                raise NoData('No item data.')

        self.c.execute('''select exists(select * from user_item where user_id=? and item_id=? and type=?)''',
                       (user.user_id, self.item_id, self.item_type))
        if self.c.fetchone() == (0,):
            self.c.execute('''insert into user_item values(:a,:b,:c,1)''',
                           {'a': user.user_id, 'b': self.item_id, 'c': self.item_type})


class PositiveItem(Item):
    def __init__(self, c) -> None:
        super().__init__()
        self.c = c

    def user_claim_item(self, user):
        self.c.execute('''select amount from user_item where user_id=? and item_id=? and type=?''',
                       (user.user_id, self.item_id, self.item_type))
        x = self.c.fetchone()
        if x:
            if x[0] + self.amount < 0:  # 数量不足
                raise ItemNotEnough(
                    'The user does not have enough `%s`.' % self.item_id)
            self.c.execute('''update user_item set amount=? where user_id=? and item_id=? and type=?''',
                           (x[0]+self.amount, user.user_id, self.item_id, self.item_type))
        else:
            if self.amount < 0:  # 添加数量错误
                raise InputError(
                    'The amount of `%s` is wrong.' % self.item_id)
            self.c.execute('''insert into user_item values(?,?,?,?)''',
                           (user.user_id, self.item_id, self.item_type, self.amount))


class ItemCore(PositiveItem):
    item_type = 'core'

    def __init__(self, c, core=None, reverse=False) -> None:
        super().__init__(c)
        self.is_available = True
        if core:
            self.item_id = core.item_id
            self.amount = - core.amount if reverse else core.amount


class ItemCharacter(Item):
    item_type = 'character'

    def __init__(self, c) -> None:
        super().__init__()
        self.c = c
        self.is_available = True

    def set_id(self, character_id):
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
        self.c.execute(
            '''select exists(select * from user_char where user_id=? and character_id=?)''', (user.user_id, self.item_id))
        if self.c.fetchone() == (0,):
            self.c.execute(
                '''insert into user_char values(?,?,1,0,0,0)''', (user.user_id, self.item_id))


class Memory(Item):
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


class Anni5tix(PositiveItem):
    item_type = 'anni5tix'

    def __init__(self, c) -> None:
        super().__init__(c)
        self.is_available = True


class WorldSong(NormalItem):
    item_type = 'world_song'

    def __init__(self, c) -> None:
        super().__init__(c)


class WorldUnlock(NormalItem):
    item_type = 'world_unlock'

    def __init__(self, c) -> None:
        super().__init__(c)


class Single(NormalItem):
    item_type = 'single'

    def __init__(self, c) -> None:
        super().__init__(c)


class Pack(NormalItem):
    item_type = 'pack'

    def __init__(self, c) -> None:
        super().__init__(c)


def get_user_cores(c, user) -> list:
    # parameter: user - User类或子类的实例
    # 得到用户的cores，返回字典列表
    r = []
    c.execute(
        '''select item_id, amount from user_item where user_id = ? and type="core"''', (user.user_id,))
    x = c.fetchall()
    if x:
        for i in x:
            if i[1]:
                amount = i[1]
            else:
                amount = 0
            r.append({'core_type': i[0], 'amount': amount})

    return r
