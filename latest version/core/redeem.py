from .error import NoData, RedeemUnavailable
from .item import CollectionItemMixin, ItemFactory


class Redeem(CollectionItemMixin):
    collection_item_const = {
        'name': 'redeem',
        'table_name': 'redeem_item',
        'table_primary_key': 'code',
        'id_name': 'code',
        'items_name': 'items'
    }

    def __init__(self, c=None) -> None:
        self.c = c
        self.code: str = None
        self.redeem_type: int = None

        self.items: list = []
        self.fragment: int = None

    def to_dict(self, has_items: bool = True) -> dict:
        r = {
            'code': self.code,
            'type': self.redeem_type
        }
        if has_items:
            r['items'] = [x.to_dict() for x in self.items]
        return r

    def from_dict(self, d: dict) -> 'Redeem':
        self.code = str(d['code'])
        self.redeem_type = int(d.get('type') or d.get('redeem_type', 0))
        self.items = [ItemFactory.from_dict(
            i, c=self.c) for i in d.get('items', [])]
        return self

    def from_list(self, l: list) -> 'Redeem':
        self.code = l[0]
        self.redeem_type = l[1]
        return self

    def select_exists(self) -> bool:
        self.c.execute(
            '''select exists(select * from redeem where code=?)''', (self.code,))
        return bool(self.c.fetchone()[0])

    def select(self, code: str = None) -> 'Redeem':
        if code:
            self.code = code
        self.c.execute('''select * from redeem where code=:a''',
                       {'a': self.code})
        x = self.c.fetchone()
        if x is None:
            raise NoData(f'The redeem `{self.code}` does not exist.', 504)

        self.redeem_type = x[1]
        return self

    def select_items(self) -> None:
        self.c.execute('''select * from redeem_item where code=:a''',
                       {'a': self.code})
        self.items = [ItemFactory.from_dict({
            'item_id': i[1],
            'type': i[2],
            'amount': i[3] if i[3] else 1
        }, self.c) for i in self.c.fetchall()]

    def insert(self) -> None:
        self.c.execute('''insert into redeem values(?,?)''',
                       (self.code, self.redeem_type))

    def insert_items(self) -> None:
        for i in self.items:
            i.insert(ignore=True)
            self.c.execute('''insert into redeem_item values(?,?,?,?)''', (
                self.code, i.item_id, i.item_type, i.amount))

    def insert_all(self) -> None:
        self.insert()
        self.insert_items()

    def delete(self) -> None:
        self.c.execute('''delete from redeem where code=?''', (self.code,))

    def delete_redeem_item(self) -> None:
        self.c.execute(
            '''delete from redeem_item where code=?''', (self.code,))

    def delete_all(self) -> None:
        self.delete_redeem_item()
        self.delete()

    def update(self) -> None:
        self.c.execute('''update redeem set type=? where code=?''',
                       (self.redeem_type, self.code))


class UserRedeem(Redeem):
    '''
        用户兑换码类

        properties: `user` - `User`类或子类的实例
    '''

    def __init__(self, c=None, user=None) -> None:
        super().__init__(c)
        self.user = user

    @property
    def is_available(self) -> bool:
        if self.redeem_type is None:
            self.select()

        if self.redeem_type == 0:
            # 一次性
            self.c.execute(
                '''select exists(select * from user_redeem where code=:a)''', {'a': self.code})
            if self.c.fetchone() == (1,):
                return False
        elif self.redeem_type == 1:
            # 每个玩家一次
            self.c.execute('''select exists(select * from user_redeem where code=:a and user_id=:b)''',
                           {'a': self.code, 'b': self.user.user_id})
            if self.c.fetchone() == (1,):
                return False

        return True

    def insert_user_redeem(self) -> None:
        self.c.execute('''insert into user_redeem values(:b,:a)''',
                       {'a': self.code, 'b': self.user.user_id})

    def claim_user_redeem(self, code: str = None) -> None:
        if code:
            self.code = code
        if not self.is_available:
            if self.redeem_type == 0:
                raise RedeemUnavailable(
                    'The redeem `%s` is unavailable.' % self.code)
            if self.redeem_type == 1:
                raise RedeemUnavailable(
                    'The redeem `%s` is unavailable.' % self.code, 506)

        if not self.items:
            self.select_items()

        self.insert_user_redeem()

        self.fragment = 0
        for i in self.items:
            if i.item_type == 'fragment':
                self.fragment += i.amount
            else:
                i.user_claim_item(self.user)
