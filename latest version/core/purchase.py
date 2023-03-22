from time import time

from .error import InputError, NoData, TicketNotEnough
from .item import CollectionItemMixin, ItemFactory


class Purchase(CollectionItemMixin):
    '''
        购买类
        properties: `user` - `User`类或子类的实例
    '''
    collection_item_const = {
        'name': 'purchase',
        'table_name': 'purchase_item',
        'table_primary_key': 'purchase_name',
        'id_name': 'purchase_name',
        'items_name': 'items'
    }

    def __init__(self, c=None, user=None):
        self.c = c
        self.user = user
        self.purchase_name: str = None
        self.price: int = None
        self.orig_price: int = None
        self.discount_from: int = None
        self.discount_to: int = None
        self.discount_reason: str = None

        self.items: list = []

        # TODO: "discount_reason": "extend"

    @property
    def price_displayed(self) -> int:
        '''
            返回显示的价格
        '''
        if self.discount_from > 0 and self.discount_to > 0:
            if self.discount_from <= int(time() * 1000) <= self.discount_to:
                if self.discount_reason == 'anni5tix':
                    x = ItemFactory(self.c).get_item('anni5tix')
                    x.item_id = 'anni5tix'
                    x.select_user_item(self.user)
                    if x.amount >= 1:
                        return 0
                return self.price
        return self.orig_price

    def to_dict(self, has_items: bool = True, show_real_price: bool = True) -> dict:
        if show_real_price:
            price = self.price_displayed
        r = {
            'name': self.purchase_name,
            'price': price if show_real_price else self.price,
            'orig_price': self.orig_price,
        }
        if has_items:
            r['items'] = [x.to_dict(has_is_available=True) for x in self.items]
        if self.discount_from > 0 and self.discount_to > 0:
            r['discount_from'] = self.discount_from
            r['discount_to'] = self.discount_to
            if not show_real_price or (self.discount_reason == 'anni5tix' and price == 0):
                r['discount_reason'] = self.discount_reason
        return r

    def from_dict(self, d: dict) -> 'Purchase':
        self.purchase_name = d.get('name') or d.get('purchase_name')
        if not self.purchase_name:
            raise InputError('purchase_name is required')
        self.orig_price = int(d['orig_price'])
        self.price = d.get('price', self.orig_price)
        self.discount_from = d.get('discount_from', -1)
        self.discount_to = d.get('discount_to', -1)
        self.discount_reason = d.get('discount_reason', '')
        for i in d.get('items', []):
            self.items.append(ItemFactory.from_dict(i))

        return self

    def from_list(self, l: list) -> 'Purchase':
        self.purchase_name = l[0]
        self.price = l[1]
        self.orig_price = l[2]
        self.discount_from = l[3] if l[3] else -1
        self.discount_to = l[4] if l[4] else -1
        self.discount_reason = l[5] if l[5] else ''
        return self

    def insert_all(self) -> None:
        '''向数据库插入，包括item表和purchase_item表'''
        self.insert()
        self.insert_items()

    def insert(self) -> None:
        '''向数据库插入，不包括item表和purchase_item表'''
        self.c.execute('''insert into purchase values(?,?,?,?,?,?)''',
                       (self.purchase_name, self.price, self.orig_price, self.discount_from, self.discount_to, self.discount_reason))

    # def insert_only_purchase_item(self) -> None:
    #     '''向数据库插入purchase_item表'''
    #     for i in self.items:
    #         self.c.execute('''insert into purchase_item values(?,?,?,?)''',
    #                        (self.purchase_name, i.item_id, i.item_type, i.amount))

    def insert_items(self) -> None:
        '''向数据库插入物品，注意已存在的物品不会变更'''
        for i in self.items:
            self.c.execute('''insert or ignore into item values(?,?,?)''',
                           (i.item_id, i.item_type, i.is_available))

            self.c.execute('''insert or ignore into purchase_item values(?,?,?,?)''',
                           (self.purchase_name, i.item_id, i.item_type, i.amount))

    def select_exists(self, purchase_name: str = None) -> bool:
        '''
            用purchase_name查询存在性
        '''
        if purchase_name:
            self.purchase_name = purchase_name
        self.c.execute(
            '''select exists(select * from purchase where purchase_name=?)''', (self.purchase_name,))
        return self.c.fetchone() == (1,)

    def select(self, purchase_name: str = None) -> 'Purchase':
        '''
            用purchase_name查询信息
        '''
        if purchase_name:
            self.purchase_name = purchase_name

        self.c.execute(
            '''select * from purchase where purchase_name=:name''', {'name': self.purchase_name})
        x = self.c.fetchone()
        if not x:
            raise NoData(
                f'Purchase `{self.purchase_name}` does not exist.', 501)

        self.price = x[1]
        self.orig_price = x[2]
        self.discount_from = x[3] if x[3] else -1
        self.discount_to = x[4] if x[4] else -1
        self.discount_reason = x[5] if x[5] else ''
        self.select_items()
        return self

    def select_items(self) -> None:
        '''从数据库拉取purchase_item数据'''
        self.c.execute(
            '''select item_id, type, amount from purchase_item where purchase_name=:a''', {'a': self.purchase_name})
        x = self.c.fetchall()
        # if not x:
        #     raise NoData(
        #         f'The items of the purchase `{self.purchase_name}` does not exist.', 501)

        self.items = []
        t = None

        for i in x:
            if i[0] == self.purchase_name:
                # 物品排序，否则客户端报错
                t = ItemFactory.from_dict({
                    'item_id': i[0],
                    'type': i[1],
                    'amount': i[2] if i[2] else 1
                }, self.c)
            else:
                self.items.append(ItemFactory.from_dict({
                    'item_id': i[0],
                    'type': i[1],
                    'amount': i[2] if i[2] else 1
                }, self.c))
        if t is not None:
            self.items = [t] + self.items

    def buy(self) -> None:
        '''进行购买'''
        if self.price is None or self.orig_price is None:
            self.select()
        if not self.items:
            self.select_items()
        self.user.select_user_one_column('ticket', 0)
        price_used = self.price_displayed

        if self.user.ticket < price_used:
            raise TicketNotEnough(
                'The user does not have enough memories.', -6)

        if not(self.orig_price == 0 or self.price == 0 and self.discount_from <= int(time() * 1000) <= self.discount_to):
            if price_used == 0:
                x = ItemFactory(self.c).get_item('anni5tix')
                x.item_id = 'anni5tix'
                x.amount = -1
                x.user_claim_item(self.user)
            else:
                self.user.ticket -= price_used
                self.user.update_user_one_column('ticket')

        for i in self.items:
            i.user_claim_item(self.user)

    def delete_purchase_item(self) -> None:
        '''删除purchase_item表'''
        self.c.execute(
            '''delete from purchase_item where purchase_name=?''', (self.purchase_name, ))

    def delete(self) -> None:
        '''删除purchase表'''
        self.c.execute(
            '''delete from purchase where purchase_name=?''', (self.purchase_name, ))

    def delete_all(self) -> None:
        '''删除purchase表和purchase_item表'''
        self.delete_purchase_item()
        self.delete()

    def update(self) -> None:
        '''更新purchase表'''
        self.c.execute('''update purchase set price=:a, orig_price=:b, discount_from=:c, discount_to=:d, discount_reason=:e where purchase_name=:f''', {
                       'a': self.price, 'b': self.orig_price, 'c': self.discount_from, 'd': self.discount_to, 'e': self.discount_reason, 'f': self.purchase_name})


class PurchaseList:
    '''
        购买列表类

        property: `user` - `User`类或子类的实例
    '''

    def __init__(self, c=None, user=None):
        self.c = c
        self.user = user
        self.purchases: list = []

    def to_dict_list(self) -> list:
        return [x.to_dict() for x in self.purchases]

    def select_from_type(self, item_type: str) -> 'PurchaseList':
        self.c.execute('''select purchase_name from purchase_item where type = :a''', {
                       'a': item_type})
        x = self.c.fetchall()
        if not x:
            return self

        self.purchases: list = []
        for i in x:
            self.purchases.append(Purchase(self.c, self.user).select(i[0]))
        return self
