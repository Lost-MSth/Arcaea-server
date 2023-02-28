from flask import Blueprint, request

from core.error import DataExist, InputError, NoData
from core.item import ItemFactory
from core.purchase import Purchase
from core.sql import Connect, Query, Sql

from .api_auth import api_try, request_json_handle, role_required
from .api_code import success_return
from .constant import Constant

bp = Blueprint('purchases', __name__, url_prefix='/purchases')


@bp.route('', methods=['GET'])
@role_required(request, ['select'])
@request_json_handle(request, optional_keys=Constant.QUERY_KEYS)
@api_try
def purchases_get(data, user):
    '''查询全购买信息'''
    with Connect() as c:
        query = Query(['purchase_name', 'discount_reason'], ['purchase_name'], [
                      'purchase_name', 'price', 'orig_price', 'discount_from', 'discount_to']).from_dict(data)
        x = Sql(c).select('purchase', query=query)
        r = [Purchase().from_list(i) for i in x]

        if not r:
            raise NoData(api_error_code=-2)

        return success_return([x.to_dict(has_items=False, show_real_price=False) for x in r])


@bp.route('', methods=['POST'])
@role_required(request, ['change'])
@request_json_handle(request, required_keys=['purchase_name', 'orig_price'], optional_keys=['price', 'discount_from', 'discount_to', 'discount_reason', 'items'])
@api_try
def purchases_post(data, user):
    '''新增购买，注意可以有items，不存在的item会自动创建'''
    with Connect() as c:
        purchase = Purchase(c).from_dict(data)
        if purchase.select_exists():
            raise DataExist(
                f'Purchase `{purchase.purchase_name}` already exists')
        purchase.insert_all()
        return success_return(purchase.to_dict(has_items='items' in data, show_real_price=False))


@bp.route('/<string:purchase_name>', methods=['GET'])
@role_required(request, ['select'])
@api_try
def purchases_purchase_get(user, purchase_name: str):
    '''查询单个购买信息'''
    with Connect() as c:
        return success_return(Purchase(c).select(purchase_name).to_dict(show_real_price=False))


@bp.route('/<string:purchase_name>', methods=['DELETE'])
@role_required(request, ['change'])
@api_try
def purchases_purchase_delete(user, purchase_name: str):
    '''删除单个购买信息，会连带删除purchase_item'''
    with Connect() as c:
        Purchase(c).select(purchase_name).delete_all()
        return success_return()


@bp.route('/<string:purchase_name>', methods=['PUT'])
@role_required(request, ['change'])
@request_json_handle(request, optional_keys=['price', 'orig_price', 'discount_from', 'discount_to', 'discount_reason'], must_change=True)
@api_try
def purchases_purchase_put(data, user, purchase_name: str):
    '''修改单个购买信息，注意不能有items'''
    with Connect() as c:
        purchase = Purchase(c).select(purchase_name)
        t = ['price', 'orig_price', 'discount_from', 'discount_to']
        for i in t:
            if i in data:
                setattr(purchase, i, int(data[i]))
        if 'discount_reason' in data:
            purchase.discount_reason = str(data['discount_reason'])

        purchase.update()
        return success_return(purchase.to_dict(has_items=False, show_real_price=False))


@bp.route('/<string:purchase_name>/items', methods=['GET'])
@role_required(request, ['select'])
@api_try
def purchases_purchase_items_get(user, purchase_name: str):
    '''查询单个购买的所有items'''
    with Connect() as c:
        p = Purchase(c)
        p.purchase_name = purchase_name
        p.select_items()
        return success_return([x.to_dict(has_is_available=True) for x in p.items])


# @bp.route('/<string:purchase_name>/items', methods=['POST'])
# @role_required(request, ['change'])
# @request_json_handle(request, required_keys=['item_id', 'type'], optional_keys=['amount'])
# @api_try
# def purchases_purchase_items_post(data, user, purchase_name: str):
#     '''新增单个购买的批量items'''
#     with Connect() as c:
#         p = Purchase(c)
#         p.purchase_name = purchase_name
#         p.select_items()
#         p.add_items([ItemFactory().from_dict(data)])
#         return success_return([x.to_dict(has_is_available=True) for x in p.items])


@bp.route('/<string:purchase_name>/items', methods=['PATCH'])
@role_required(request, ['change'])
@request_json_handle(request, is_batch=True)
@api_try
def purchases_purchase_items_patch(data, user, purchase_name: str):
    '''增删改单个购买的批量items'''
    with Connect() as c:
        p = Purchase(c)
        p.purchase_name = purchase_name
        p.select_items()
        p.remove_items([ItemFactory.from_dict(x, c=c)
                        for x in data.get('remove', [])])
        p.add_items([ItemFactory.from_dict(x, c=c)
                     for x in data.get('create', [])])

        updates = data.get('update', [])
        for x in updates:
            if 'amount' not in x:
                raise InputError('`amount` is required in `update`')
            if not isinstance(x['amount'], int) or x['amount'] <= 0:
                raise InputError(
                    '`amount` must be a positive integer', api_error_code=-101)

        p.update_items([ItemFactory.from_dict(x, c=c) for x in updates])
        return success_return([x.to_dict(has_is_available=True) for x in p.items])


# @bp.route('/<string:purchase_name>/items/<string:item_type>/<string:item_id>', methods=['DELETE'])
# @role_required(request, ['change'])
# @api_try
# def purchases_purchase_items_item_delete(user, purchase_name: str, item_type: str, item_id: str):
#     '''删除单个购买的单个item'''
#     with Connect() as c:
#         p = Purchase(c)
#         p.purchase_name = purchase_name
#         p.select_items()
#         p.delete_items([ItemFactory().from_dict(
#             {'item_type': item_type, 'item_id': item_id})])
#         return success_return()


# @bp.route('/<string:purchase_name>/items/<string:item_type>/<string:item_id>', methods=['PUT'])
# @role_required(request, ['change'])
# @request_json_handle(request, optional_keys=['amount', 'is_available'], must_change=True)
# @api_try
# def purchases_purchase_items_item_put(data, user, purchase_name: str, item_type: str, item_id: str):
#     '''修改单个购买的单个item'''
#     with Connect() as c:
#         p = Purchase(c)
#         p.purchase_name = purchase_name
#         pass
#         return success_return()
