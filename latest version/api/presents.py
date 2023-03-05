from flask import Blueprint, request

from core.error import DataExist, InputError, NoData
from core.item import ItemFactory
from core.present import Present
from core.sql import Connect, Query, Sql

from .api_auth import api_try, request_json_handle, role_required
from .api_code import success_return
from .constant import Constant


bp = Blueprint('presents', __name__, url_prefix='/presents')


@bp.route('', methods=['GET'])
@role_required(request, ['select'])
@request_json_handle(request, optional_keys=Constant.QUERY_KEYS)
@api_try
def presents_get(data, user):
    '''查询全present信息'''
    with Connect() as c:
        query = Query(['present_id'], ['present_id', 'description'], [
                      'present_id', 'expire_ts']).from_dict(data)
        x = Sql(c).select('present', query=query)
        r = [Present().from_list(i) for i in x]

        if not r:
            raise NoData(api_error_code=-2)

        return success_return([x.to_dict(has_items=False) for x in r])


@bp.route('', methods=['POST'])
@role_required(request, ['insert'])
@request_json_handle(request, required_keys=['present_id', 'description', 'expire_ts'], optional_keys=['items'])
@api_try
def presents_post(data, user):
    '''添加present，注意可以有items，不存在的item会自动创建'''
    with Connect() as c:
        p = Present(c).from_dict(data)
        if p.select_exists():
            raise DataExist(
                f'Present `{p.present_id}` already exists')
        p.insert_all()
        return success_return(p.to_dict(has_items='items' in data))


@bp.route('/<string:present_id>', methods=['GET'])
@role_required(request, ['select'])
@api_try
def presents_present_get(user, present_id: str):
    '''查询单个present信息'''
    with Connect() as c:
        p = Present(c).select(present_id)
        p.select_items()
        return success_return(p.to_dict())


@bp.route('/<string:present_id>', methods=['DELETE'])
@role_required(request, ['delete'])
@api_try
def presents_present_delete(user, present_id: str):
    '''删除present，会连带删除present_item'''
    with Connect() as c:
        Present(c).select(present_id).delete_all()
        return success_return()


@bp.route('/<string:present_id>', methods=['PUT'])
@role_required(request, ['change'])
@request_json_handle(request, optional_keys=['description', 'expire_ts'], must_change=True)
@api_try
def presents_present_put(data, user, present_id: str):
    '''更新present信息，注意不能有items'''
    with Connect() as c:
        p = Present(c).select(present_id)
        if 'description' in data:
            p.description = str(data['description'])
        if 'expire_ts' in data:
            p.expire_ts = int(data['expire_ts'])
        p.update()
        return success_return(p.to_dict(has_items=False))


@bp.route('/<string:present_id>/items', methods=['GET'])
@role_required(request, ['select'])
@api_try
def presents_present_items_get(user, present_id: str):
    '''查询present的items'''
    with Connect() as c:
        p = Present(c)
        p.present_id = present_id
        p.select_items()
        return success_return([x.to_dict(has_is_available=True) for x in p.items])


@bp.route('/<string:present_id>/items', methods=['PATCH'])
@role_required(request, ['change'])
@request_json_handle(request, is_batch=True)
@api_try
def presents_present_items_patch(data, user, present_id: str):
    '''增删改单个present的items'''
    with Connect() as c:
        p = Present(c)
        p.present_id = present_id
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
