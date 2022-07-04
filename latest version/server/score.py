from time import time

from core.error import ArcError, InputError
from core.rank import RankList
from core.score import UserPlay
from core.sql import Connect
from core.user import UserOnline
from flask import Blueprint, request

from .auth import auth_required
from .func import error_return, success_return

bp = Blueprint('score', __name__, url_prefix='/score')


@bp.route('/token', methods=['GET'])  # 成绩上传所需的token，显然我不想验证
def score_token():
    return success_return({'token': '1145141919810'})


@bp.route('/token/world', methods=['GET'])  # 世界模式成绩上传所需的token，无验证
@auth_required(request)
def score_token_world(user_id):

    stamina_multiply = int(
        request.args['stamina_multiply']) if 'stamina_multiply' in request.args else 1
    fragment_multiply = int(
        request.args['fragment_multiply']) if 'fragment_multiply' in request.args else 100
    prog_boost_multiply = int(
        request.args['prog_boost_multiply']) if 'prog_boost_multiply' in request.args else 0
    with Connect() as c:
        try:
            x = UserPlay(c, UserOnline(c, user_id))
            x.song.set_chart(request.args['song_id'], int(
                request.args['difficulty']))
            x.set_play_state(stamina_multiply,
                             fragment_multiply, prog_boost_multiply)
            return success_return({
                "stamina": x.user.stamina.stamina,
                "max_stamina_ts": x.user.stamina.max_stamina_ts,
                "token": "13145201919810"
            }
            )
        except ArcError as e:
            return error_return(e)
    return error_return()


@bp.route('/song', methods=['POST'])  # 成绩上传
@auth_required(request)
def song_score_post(user_id):
    with Connect() as c:
        try:
            x = UserPlay(c, UserOnline(c, user_id))
            x.song_token = request.form['song_token']
            x.song_hash = request.form['song_hash']
            x.song.set_chart(
                request.form['song_id'], request.form['difficulty'])
            x.set_score(request.form['score'], request.form['shiny_perfect_count'], request.form['perfect_count'], request.form['near_count'],
                        request.form['miss_count'], request.form['health'], request.form['modifier'], int(time() * 1000), request.form['clear_type'])
            x.beyond_gauge = int(request.form['beyond_gauge'])
            x.submission_hash = request.form['submission_hash']
            if not x.is_valid:
                raise InputError('Invalid score.', 107)
            x.upload_score()
            return success_return(x.to_dict)
        except ArcError as e:
            return error_return(e)
    return error_return()


@bp.route('/song', methods=['GET'])  # TOP20
@auth_required(request)
def song_score_top(user_id):
    with Connect() as c:
        try:
            rank_list = RankList(c)
            rank_list.song.set_chart(request.args.get(
                'song_id'), request.args.get('difficulty'))
            rank_list.select_top()
            return success_return(rank_list.to_dict_list)
        except ArcError as e:
            return error_return(e)
    return error_return()


@bp.route('/song/me', methods=['GET'])  # 我的排名，默认最多20
@auth_required(request)
def song_score_me(user_id):
    with Connect() as c:
        try:
            rank_list = RankList(c)
            rank_list.song.set_chart(request.args.get(
                'song_id'), request.args.get('difficulty'))
            rank_list.select_me(UserOnline(c, user_id))
            return success_return(rank_list.to_dict_list)
        except ArcError as e:
            return error_return(e)
    return error_return()


@bp.route('/song/friend', methods=['GET'])  # 好友排名，默认最多50
@auth_required(request)
def song_score_friend(user_id):
    with Connect() as c:
        try:
            rank_list = RankList(c)
            rank_list.song.set_chart(request.args.get(
                'song_id'), request.args.get('difficulty'))
            rank_list.select_friend(UserOnline(c, user_id))
            return success_return(rank_list.to_dict_list)
        except ArcError as e:
            return error_return(e)
    return error_return()
