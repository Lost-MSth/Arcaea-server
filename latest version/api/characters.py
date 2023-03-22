from flask import Blueprint, request

from core.error import InputError, NoData
from core.item import ItemFactory
from core.character import Character
from core.sql import Connect, Query, Sql

from .api_auth import api_try, request_json_handle, role_required
from .api_code import success_return
from .constant import Constant


bp = Blueprint('characters', __name__, url_prefix='/characters')


@bp.route('', methods=['GET'])
@role_required(request, ['select'])
@request_json_handle(request, optional_keys=Constant.QUERY_KEYS)
@api_try
def characters_get(data, user):
    '''查询全角色信息'''
    A = ['character_id', 'name', 'skill_id',
         'skill_id_uncap', 'char_type', 'is_uncapped']
    B = ['name', 'skill_id', 'skill_id_uncap']
    C = ['name', 'frag1', 'prog1', 'overdrive1', 'frag20',
         'prog20', 'overdrive20', 'frag30', 'prog30', 'overdrive30']
    with Connect() as c:
        query = Query(A, B, C).from_dict(data)
        x = Sql(c).select('character', query=query)
        r = [Character().from_list(i) for i in x]

        if not r:
            raise NoData(api_error_code=-2)

        return success_return([x.to_dict() for x in r])


@bp.route('/<int:character_id>', methods=['GET'])
@role_required(request, ['select'])
@api_try
def characters_character_get(user, character_id: int):
    # 包含core
    with Connect() as c:
        c = Character(c).select(character_id)
        c.select_character_core()
        return success_return(c.to_dict(has_cores=True))


@bp.route('/<int:character_id>', methods=['PUT'])
@role_required(request, ['change'])
@request_json_handle(request, optional_keys=['max_level', 'skill_id', 'skill_id_uncap', 'skill_unlock_level', 'skill_requires_uncap', 'char_type', 'is_uncapped', 'frag1', 'prog1', 'overdrive1', 'frag20', 'prog20', 'overdrive20', 'frag30', 'prog30', 'overdrive30'], must_change=True)
@api_try
def characters_character_put(data, user, character_id: int):
    '''修改角色信息'''
    if ('skill_id' in data and data['skill_id'] != '' and data['skill_id'] not in Constant.SKILL_IDS) or ('skill_id_uncap' in data and data['skill_id_uncap'] != '' and data['skill_id_uncap'] not in Constant.SKILL_IDS):
        raise InputError('Invalid skill_id', api_error_code=-131)
    with Connect() as c:
        c = Character(c).select(character_id)
        try:
            if 'max_level' in data:
                c.max_level = int(data['max_level'])
            if 'skill_id' in data:
                c.skill_id = data['skill_id']
            if 'skill_id_uncap' in data:
                c.skill_id_uncap = data['skill_id_uncap']
            if 'skill_unlock_level' in data:
                c.skill_unlock_level = int(data['skill_unlock_level'])
            if 'skill_requires_uncap' in data:
                c.skill_requires_uncap = data['skill_requires_uncap'] == 1
            if 'char_type' in data:
                c.char_type = int(data['char_type'])
            if 'is_uncapped' in data:
                c.is_uncapped = data['is_uncapped'] == 1
            t = ['frag1', 'prog1', 'overdrive1', 'frag20', 'prog20',
                 'overdrive20', 'frag30', 'prog30', 'overdrive30']
            for i in t:
                if i not in data:
                    continue
                if i.endswith('1'):
                    x = getattr(c, i[:-1])
                    x.start = float(data[i])
                elif i.endswith('20'):
                    x = getattr(c, i[:-2])
                    x.mid = float(data[i])
                else:
                    x = getattr(c, i[:-2])
                    x.end = float(data[i])
        except ValueError as e:
            raise InputError('Invalid input', api_error_code=-101) from e
        c.update()
        return success_return(c.to_dict())


@bp.route('/<int:character_id>/cores', methods=['GET'])
@role_required(request, ['select'])
@api_try
def characters_character_cores_get(user, character_id: int):
    with Connect() as c:
        c = Character(c)
        c.character_id = character_id
        c.select_character_core()
        return success_return(c.uncap_cores_to_dict())


@bp.route('/<int:character_id>/cores', methods=['PATCH'])
@role_required(request, ['change'])
@request_json_handle(request, is_batch=True)
@api_try
def characters_character_cores_patch(data, user, character_id: int):
    '''修改角色觉醒cores'''
    def force_type_core(x: dict) -> dict:
        x['item_type'] = 'core'
        x['type'] = 'core'
        return x

    with Connect() as c:
        ch = Character(c)
        ch.character_id = character_id
        ch.select_character_core()
        ch.remove_items([ItemFactory.from_dict(x, c=c)
                         for x in map(force_type_core, data.get('remove', []))])
        ch.add_items([ItemFactory.from_dict(x, c=c)
                      for x in map(force_type_core, data.get('create', []))])
        updates = list(map(force_type_core, data.get('update', [])))
        for x in updates:
            if 'amount' not in x:
                raise InputError('`amount` is required in `update`')
            if not isinstance(x['amount'], int) or x['amount'] <= 0:
                raise InputError(
                    '`amount` must be a positive integer', api_error_code=-101)

        ch.update_items(
            [ItemFactory.from_dict(x, c=c) for x in updates])
        return success_return(ch.uncap_cores_to_dict())
