from flask import Blueprint, request

from core.linkplay import RemoteMultiPlayer

from .api_auth import api_try, request_json_handle, role_required
from .api_code import success_return


bp = Blueprint('multiplay', __name__, url_prefix='/multiplay')


@bp.route('/rooms', methods=['GET'])
@role_required(request, ['select'])
@request_json_handle(request, optional_keys=['offset', 'limit'])
@api_try
def rooms_get(data, user):
    '''获取房间列表'''

    r = RemoteMultiPlayer().get_rooms(offset=data.get(
        'offset', 0), limit=data.get('limit', 100))
    return success_return(r)
