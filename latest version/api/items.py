from flask import Blueprint, request

from core.error import DataExist, InputError, NoData
from core.item import Item, ItemFactory
from core.sql import Connect, Query, Sql

from .api_auth import api_try, request_json_handle, role_required
from .api_code import success_return
from .constant import Constant

bp = Blueprint('items', __name__, url_prefix='/items')


@bp.route('', methods=['GET'])
@role_required(request, ['select'])
@request_json_handle(request, optional_keys=Constant.QUERY_KEYS)
@api_try
def items_get(data, user):
    '''查询全物品信息'''
    with Connect() as c:
        query = Query(['item_id', 'type'], ['item_id'],
                      ['item_id']).from_dict(data)
        x = Sql(c).select('item', query=query)
        r: 'list[Item]' = []
        for i in x:
            r.append(ItemFactory.from_dict({
                'item_id': i[0],
                'type': i[1],
                'is_available': i[2] == 1
            }))

        if not r:
            raise NoData(api_error_code=-2)

        return success_return([x.to_dict(has_is_available=True, has_amount=False) for x in r])


ALLOW_ITEM_TYPE = ['pack', 'single', 'world_song', 'character']


@bp.route('', methods=['POST'])
@role_required(request, ['change'])
@request_json_handle(request, required_keys=['item_id', 'type'], optional_keys=['is_available'])
@api_try
def items_post(data, user):
    '''新增物品'''
    if data['type'] not in ALLOW_ITEM_TYPE:
        raise InputError(
            f'Invalid item type: `{data["type"]}`', api_error_code=-120)
    with Connect() as c:
        item = ItemFactory.from_dict(data, c=c)
        if item.select_exists():
            raise DataExist(
                f'Item `{item.item_type}`: `{item.item_id}` already exists', api_error_code=-122)
        item.insert()
        return success_return(item.to_dict(has_is_available=True, has_amount=False))


@bp.route('/<string:item_type>/<string:item_id>', methods=['DELETE'])
@role_required(request, ['change'])
@api_try
def items_item_delete(user, item_type, item_id):
    '''删除物品'''
    if item_type not in ALLOW_ITEM_TYPE:
        raise InputError(
            f'Invalid item type: `{item_type}`', api_error_code=-120)
    with Connect() as c:
        item = ItemFactory.from_dict({
            'item_id': item_id,
            'type': item_type
        }, c=c)
        if not item.select_exists():
            raise NoData(
                f'No such item `{item_type}`: `{item_id}`', api_error_code=-121)
        item.delete()
        return success_return()


@bp.route('/<string:item_type>/<string:item_id>', methods=['PUT'])
@role_required(request, ['change'])
@request_json_handle(request, optional_keys=['is_available'], must_change=True)
@api_try
def items_item_put(data, user, item_type, item_id):
    '''修改物品'''
    if item_type not in ALLOW_ITEM_TYPE:
        raise InputError(
            f'Invalid item type: `{item_type}`', api_error_code=-120)
    if not isinstance(data['is_available'], bool):
        raise InputError('`is_available` must be a boolean',
                         api_error_code=-101)
    with Connect() as c:
        item = ItemFactory.from_dict({
            'item_id': item_id,
            'type': item_type,
            'is_available': data['is_available']
        }, c=c)
        if not item.select_exists():
            raise NoData(
                f'No such item `{item_type}`: `{item_id}`', api_error_code=-121)
        item.update()
        return success_return(item.to_dict(has_is_available=True, has_amount=False))


@bp.route('/<string:item_type>/<string:item_id>', methods=['GET'])
@role_required(request, ['select'])
@api_try
def items_item_get(user, item_type, item_id):
    '''查询单个物品信息'''
    with Connect() as c:
        item = ItemFactory.from_dict({
            'item_id': item_id,
            'type': item_type
        }, c=c)
        item.select()
        return success_return(item.to_dict(has_is_available=True, has_amount=False))
