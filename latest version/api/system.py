from flask import Blueprint, request

from core.error import ArcError
from core.operation import BaseOperation

from .api_auth import api_try, role_required
from .api_code import success_return

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
