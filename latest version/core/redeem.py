from .error import NoData, RedeemUnavailable
from .item import ItemFactory


class Redeem:
    def __init__(self, c=None) -> None:
        self.c = c
        self.code: str = None
        self.redeem_type: int = None

        self.items: list = []
        self.fragment: int = None

    def select(self, code: str = None) -> None:
        if code:
            self.code = code
        self.c.execute('''select * from redeem where code=:a''',
                       {'a': self.code})
        x = self.c.fetchone()
        if x is None:
            raise NoData('The redeem `%s` does not exist.' % self.code, 504)

        self.redeem_type = x[1]

    def select_items(self) -> None:
        self.c.execute('''select * from redeem_item where code=:a''',
                       {'a': self.code})
        x = self.c.fetchall()
        if not x:
            raise NoData(
                'The redeem `%s` does not have any items.' % self.code)
        self.items = [ItemFactory.from_dict({
            'item_id': i[1],
            'type': i[2],
            'amount': i[3] if i[3] else 1
        }, self.c) for i in x]


class UserRedeem(Redeem):
    '''
        用户兑换码类\ 
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
            elif self.redeem_type == 1:
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
