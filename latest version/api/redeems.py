from flask import Blueprint, request

from core.error import DataExist, InputError, NoData
from core.item import ItemFactory
from core.redeem import Redeem
from core.sql import Connect, Query, Sql

from .api_auth import api_try, request_json_handle, role_required
from .api_code import success_return
from .constant import Constant


bp = Blueprint('redeems', __name__, url_prefix='/redeems')


@bp.route('', methods=['GET'])
@role_required(request, ['select'])
@request_json_handle(request, optional_keys=Constant.QUERY_KEYS)
@api_try
def redeems_get(data, user):
    '''查询全redeem信息'''
    with Connect() as c:
        query = Query(['code', 'type'], ['code'], ['code']).from_dict(data)
        x = Sql(c).select('redeem', query=query)
        r = [Redeem().from_list(i) for i in x]

        if not r:
            raise NoData(api_error_code=-2)

        return success_return([x.to_dict(has_items=False) for x in r])


@bp.route('', methods=['POST'])
@role_required(request, ['insert'])
@request_json_handle(request, required_keys=['code', 'type'], optional_keys=['items'])
@api_try
def redeems_post(data, user):
    '''添加redeem，注意可以有items，不存在的item会自动创建'''
    with Connect() as c:
        r = Redeem(c).from_dict(data)
        if r.select_exists():
            raise DataExist(
                f'redeem `{r.code}` already exists')
        r.insert_all()
        return success_return(r.to_dict(has_items='items' in data))


@bp.route('/<string:code>', methods=['GET'])
@role_required(request, ['select'])
@api_try
def redeems_redeem_get(user, code: str):
    '''查询单个redeem信息'''
    with Connect() as c:
        r = Redeem(c).select(code)
        r.select_items()
        return success_return(r.to_dict())


@bp.route('/<string:code>', methods=['DELETE'])
@role_required(request, ['delete'])
@api_try
def redeems_redeem_delete(user, code: str):
    '''删除redeem，会连带删除redeem_item'''
    with Connect() as c:
        Redeem(c).select(code).delete_all()
        return success_return()


@bp.route('/<string:code>', methods=['PUT'])
@role_required(request, ['change'])
@request_json_handle(request, optional_keys=['type'], must_change=True)
@api_try
def redeems_redeem_put(data, user, code: str):
    '''更新redeem信息，注意不能有items'''
    with Connect() as c:
        r = Redeem(c).select(code)
        if 'type' in data:
            r.redeem_type = int(data['type'])
        r.update()
        return success_return(r.to_dict(has_items=False))


@bp.route('/<string:code>/items', methods=['GET'])
@role_required(request, ['select'])
@api_try
def redeems_redeem_items_get(user, code: str):
    '''查询redeem的items'''
    with Connect() as c:
        r = Redeem(c)
        r.code = code
        r.select_items()
        return success_return([x.to_dict(has_is_available=True) for x in r.items])


@bp.route('/<string:code>/items', methods=['PATCH'])
@role_required(request, ['change'])
@request_json_handle(request, is_batch=True)
@api_try
def redeems_redeem_items_patch(data, user, code: str):
    '''增删改单个redeem的items'''
    with Connect() as c:
        r = Redeem(c)
        r.code = code
        r.select_items()
        r.remove_items([ItemFactory.from_dict(x, c=c)
                        for x in data.get('remove', [])])
        r.add_items([ItemFactory.from_dict(x, c=c)
                     for x in data.get('create', [])])

        updates = data.get('update', [])
        for x in updates:
            if 'amount' not in x:
                raise InputError('`amount` is required in `update`')
            if not isinstance(x['amount'], int) or x['amount'] <= 0:
                raise InputError(
                    '`amount` must be a positive integer', api_error_code=-101)

        r.update_items([ItemFactory.from_dict(x, c=c) for x in updates])
        return success_return([x.to_dict(has_is_available=True) for x in r.items])
