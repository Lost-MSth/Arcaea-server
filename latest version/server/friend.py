from flask import Blueprint, request
from core.sql import Connect
from core.error import ArcError
from core.user import UserOnline, code_get_id
from .func import error_return, success_return
from .auth import auth_required

bp = Blueprint('friend', __name__, url_prefix='/friend')


@bp.route('/me/add', methods=['POST'])  # 加好友
@auth_required(request)
def add_friend(user_id):
    with Connect() as c:
        try:
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
        except ArcError as e:
            return error_return(e)
    return error_return()


@bp.route('/me/delete', methods=['POST'])  # 删好友
@auth_required(request)
def delete_friend(user_id):
    with Connect() as c:
        try:
            friend_id = int(request.form['friend_id'])
            user = UserOnline(c, user_id)
            user.delete_friend(friend_id)

            return success_return({
                "user_id": user.user_id,
                "updatedAt": "2020-09-07T07:32:12.740Z",
                "createdAt": "2020-09-06T10:05:18.471Z",
                "friends": user.friends
            })
        except ArcError as e:
            return error_return(e)
    return error_return()
