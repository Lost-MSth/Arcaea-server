from time import time

from .error import ArcError, NoData
from .item import CollectionItemMixin, ItemFactory


class Present(CollectionItemMixin):
    collection_item_const = {
        'name': 'present',
        'table_name': 'present_item',
        'table_primary_key': 'present_id',
        'id_name': 'present_id',
        'items_name': 'items'
    }

    def __init__(self, c=None) -> None:
        self.c = c
        self.present_id: str = None
        self.expire_ts: int = None
        self.description: str = None

        self.items: list = None

    @property
    def is_expired(self) -> bool:
        return self.expire_ts < int(time() * 1000)

    def to_dict(self, has_items: bool = True) -> dict:
        r = {
            'present_id': self.present_id,
            'expire_ts': self.expire_ts,
            'description': self.description
        }
        if has_items:
            r['items'] = [x.to_dict() for x in self.items]
        return r

    def from_dict(self, d: dict) -> 'Present':
        self.present_id = d['present_id']
        self.expire_ts = int(d['expire_ts'])
        self.description = d.get('description', '')
        self.items = [ItemFactory.from_dict(
            i, c=self.c) for i in d.get('items', [])]
        return self

    def from_list(self, l: list) -> 'Present':
        self.present_id = l[0]
        self.expire_ts = int(l[1]) if l[1] else 0
        self.description = l[2] if l[2] else ''
        return self

    def select_exists(self) -> bool:
        '''
            查询present是否存在
        '''
        self.c.execute(
            '''select exists(select * from present where present_id=?)''', (self.present_id,))
        return bool(self.c.fetchone()[0])

    def select(self, present_id: str = None) -> 'Present':
        '''
            用present_id查询信息
        '''
        if present_id:
            self.present_id = present_id

        self.c.execute(
            '''select * from present where present_id=:a''', {'a': self.present_id})
        x = self.c.fetchone()
        if x is None:
            raise NoData('The present `%s` does not exist.' % self.present_id)

        self.from_list(x)
        return self

    def select_items(self) -> None:
        '''
            查询奖励的物品
        '''
        self.c.execute(
            '''select * from present_item where present_id=:a''', {'a': self.present_id})
        self.items = [ItemFactory.from_dict({
            'item_id': i[1],
            'type': i[2],
            'amount': i[3] if i[3] else 1
        }, self.c) for i in self.c.fetchall()]

    def insert_items(self) -> None:
        for i in self.items:
            self.c.execute('''insert or ignore into item values(?,?,?)''',
                           (i.item_id, i.item_type, i.is_available))

            self.c.execute('''insert or ignore into present_item values(?,?,?,?)''',
                           (self.present_id, i.item_id, i.item_type, i.amount))

    def insert(self) -> None:
        self.c.execute('''insert into present values(?,?,?)''',
                       (self.present_id, self.expire_ts, self.description))

    def insert_all(self) -> None:
        self.insert()
        self.insert_items()

    def delete(self) -> None:
        self.c.execute(
            '''delete from present where present_id=?''', (self.present_id,))

    def delete_present_item(self) -> None:
        self.c.execute(
            '''delete from present_item where present_id=?''', (self.present_id,))

    def delete_all(self) -> None:
        self.delete_present_item()
        self.delete()

    def update(self) -> None:
        self.c.execute('''update present set expire_ts=?, description=? where present_id=?''',
                       (self.expire_ts, self.description, self.present_id))


class UserPresent(Present):
    '''
        用户登录奖励类
        忽视了description的多语言
        properties: `user` - `User`类或子类的实例
    '''

    def __init__(self, c=None, user=None) -> None:
        super().__init__(c)
        self.user = user

    def delete_user_present(self) -> None:
        '''
            删除用户奖励
        '''
        self.c.execute('''delete from user_present where user_id=:a and present_id=:b''',
                       {'a': self.user.user_id, 'b': self.present_id})

    def claim_user_present(self, present_id: str = None, user=None) -> None:
        '''
            确认并删除用户奖励
        '''
        if present_id:
            self.present_id = present_id
        if user:
            self.user = user
        if self.expire_ts is None:
            self.select()
        if self.items is None:
            self.select_items()

        self.c.execute('''select exists(select * from user_present where user_id=:a and present_id=:b)''',
                       {'a': self.user.user_id, 'b': self.present_id})

        if self.c.fetchone() == (0,):
            raise NoData('The present `%s` for the user `%s` does not exist.' % (
                self.present_id, self.user.user_id))

        self.delete_user_present()

        if self.is_expired:
            raise ArcError('The present `%s` has expired.' % self.present_id)

        for i in self.items:
            i.user_claim_item(self.user)


class UserPresentList:
    def __init__(self, c=None, user=None) -> None:
        self.c = c
        self.user = user

        self.presents: list = None

    def to_dict_list(self) -> list:
        return [x.to_dict() for x in self.presents]

    def select_user_presents(self) -> None:
        '''
            查询用户全部奖励
        '''
        self.c.execute(
            '''select * from present where present_id in (select present_id from user_present where user_id=:a)''', {'a': self.user.user_id})
        x = self.c.fetchall()
        self.presents = []
        if not x:
            return None

        for i in x:
            p = UserPresent(self.c, self.user)
            p.present_id = i[0]
            p.expire_ts = i[1]
            p.description = i[2]
            if not p.is_expired:
                p.select_items()
                self.presents.append(p)
