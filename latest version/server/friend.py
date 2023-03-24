from flask import Blueprint, request

from core.sql import Connect
from core.user import UserOnline, code_get_id

from .auth import auth_required
from .func import arc_try, success_return

bp = Blueprint('friend', __name__, url_prefix='/friend')


@bp.route('/me/add', methods=['POST'])  # 加好友
@auth_required(request)
@arc_try
def add_friend(user_id):
    with Connect() as c:
        friend_code = request.form['friend_code']
        friend_id = code_get_id(c, friend_code)
        user = UserOnline(c, user_id)
        user.add_friend(friend_id)

        return success_return({
            "user_id": user.user_id,
            "updatedAt": "2020-09-07T07:32:12.740Z",
            "createdAt": "2020-09-06T10:05:18.471Z",
            "friends": user.friends
        })


@bp.route('/me/delete', methods=['POST'])  # 删好友
@auth_required(request)
@arc_try
def delete_friend(user_id):
    with Connect() as c:
        friend_id = int(request.form['friend_id'])
        user = UserOnline(c, user_id)
        user.delete_friend(friend_id)

        return success_return({
            "user_id": user.user_id,
            "updatedAt": "2020-09-07T07:32:12.740Z",
            "createdAt": "2020-09-06T10:05:18.471Z",
            "friends": user.friends
        })
