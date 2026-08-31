from time import time

from flask import Blueprint, request

from core.constant import (
    ARCAEA_DATABASE_VERSION,
    ARCAEA_LOG_DATBASE_VERSION,
    ARCAEA_SERVER_VERSION,
)
from core.constant import Constant as CoreConstant
from core.error import ArcError
from core.operation import BaseOperation

from .api_auth import api_try, role_required
from .api_code import success_return
from .constant import Constant

bp = Blueprint('system', __name__, url_prefix='/system')


operation_dict = {i._name: i for i in BaseOperation.__subclasses__()}


@bp.route('/operations', methods=['GET'])
@role_required(request, ['system'])
@api_try
def operations_get(user):
    return success_return(list(operation_dict.keys()))


@bp.route('/operations/<string:operation_name>', methods=['POST'])
@role_required(request, ['system'])
@api_try
def operations_operation_post(user, operation_name: str):
    if operation_name not in operation_dict:
        raise ArcError(
            f'No such operation: `{operation_name}`', api_error_code=-1, status=404)
    x = operation_dict[operation_name]()
    x.set_params(**request.get_json())
    x.run()
    return success_return()


@bp.route('/constants', methods=['GET'])
@role_required(request, ['public'])
@api_try
def constants_get(user):
    return success_return({
        'server_version': ARCAEA_SERVER_VERSION,
        'database_version': ARCAEA_DATABASE_VERSION,
        'log_database_version': ARCAEA_LOG_DATBASE_VERSION,
        'skill_ids': list(Constant.SKILL_IDS),

        'best30_weight': CoreConstant.BEST30_WEIGHT,
        'recent10_weight': CoreConstant.RECENT10_WEIGHT,
        'best10_weight': CoreConstant.BEST10_WEIGHT,
        'best50_weight': CoreConstant.BEST50_WEIGHT,
        'clear_bonus': CoreConstant.CLEAR_BONUS,
    })


@bp.route('/info', methods=['GET'])
@role_required(request, ['public'])
@api_try
def info_get(user):
    return success_return({
        'server_time': time(),
    })
