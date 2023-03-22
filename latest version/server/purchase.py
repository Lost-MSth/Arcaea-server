from time import time

from flask import Blueprint, request

from core.error import InputError, ItemUnavailable, PostError
from core.item import ItemFactory, Stamina6
from core.purchase import Purchase, PurchaseList
from core.redeem import UserRedeem
from core.sql import Connect
from core.user import UserOnline

from .auth import auth_required
from .func import arc_try, success_return

bp = Blueprint('purchase', __name__, url_prefix='/purchase')


@bp.route('/bundle/pack', methods=['GET'])  # 曲包信息
@auth_required(request)
@arc_try
def bundle_pack(user_id):
    with Connect() as c:
        x = PurchaseList(c, UserOnline(c, user_id)
                         ).select_from_type('pack')
        return success_return(x.to_dict_list())


@bp.route('/bundle/single', methods=['GET'])  # 单曲购买信息获取
@auth_required(request)
@arc_try
def get_single(user_id):
    with Connect() as c:
        x = PurchaseList(c, UserOnline(c, user_id)
                         ).select_from_type('single')
        return success_return(x.to_dict_list())


@bp.route('/bundle/bundle', methods=['GET'])  # 捆绑包
def bundle_bundle():
    return success_return([])
    # 感觉上是定死的，没意义啊
    # return success_return([{
    #     "name": "chronicles",
    #     "items": [{
    #         "type": "bundle",
    #         "id": "core"
    #     }, {
    #         "type": "bundle",
    #         "id": "prelude"
    #     }, {
    #         "type": "bundle",
    #         "id": "rei"
    #     }, {
    #         "type": "bundle",
    #         "id": "yugamu"
    #     }, {
    #         "type": "bundle",
    #         "id": "vs"
    #     }],
    #     "orig_price": 2000,
    #     "price": 2000,
    #     "discount_from": 1657152000000,
    #     "discount_to": 1758447999000,
    #     "discount_reason": "chronicle"
    # }])


@bp.route('/me/pack', methods=['POST'])  # 曲包和单曲购买
@auth_required(request)
@arc_try
def buy_pack_or_single(user_id):
    with Connect() as c:
        if 'pack_id' in request.form:
            purchase_name = request.form['pack_id']
        elif 'single_id' in request.form:
            purchase_name = request.form['single_id']
        else:
            return success_return()

        x = Purchase(c, UserOnline(c, user_id)).select(purchase_name)
        x.buy()

        return success_return({
            'user_id': x.user.user_id,
            'ticket': x.user.ticket,
            'packs': x.user.packs,
            'singles': x.user.singles,
            'characters': x.user.characters_list
        })


@bp.route('/me/item', methods=['POST'])  # 特殊购买，world模式boost和stamina
@auth_required(request)
@arc_try
def buy_special(user_id):
    with Connect() as c:
        if 'item_id' not in request.form:
            raise PostError('`item_id` is required')
        item_id = request.form['item_id']

        x = Purchase(c, UserOnline(c, user_id))
        x.purchase_name = item_id
        x.price = 50
        x.orig_price = 50
        x.discount_from = -1
        x.discount_to = -1
        x.items = [ItemFactory(c).get_item(item_id)]
        x.buy()

        r = {'user_id': x.user.user_id, 'ticket': x.user.ticket}
        if item_id == 'stamina6':
            r['stamina'] = x.user.stamina.stamina
            r['max_stamina_ts'] = x.user.stamina.max_stamina_ts
            r['world_mode_locked_end_ts'] = -1
        return success_return(r)


@bp.route('/me/stamina/<buy_stamina_type>', methods=['POST'])  # 购买体力
@auth_required(request)
@arc_try
def purchase_stamina(user_id, buy_stamina_type):
    with Connect() as c:
        if buy_stamina_type != 'fragment':
            raise InputError('Invalid type of buying stamina')

        user = UserOnline(c, user_id)
        user.select_user_one_column('next_fragstam_ts', -1)
        now = int(time()*1000)
        if user.next_fragstam_ts > now:
            return ItemUnavailable('Buying stamina by fragment is not available yet.', 905)

        user.update_user_one_column(
            'next_fragstam_ts', now + 24 * 3600 * 1000)
        s = Stamina6(c)
        s.user_claim_item(user)
        return success_return({
            "user_id": user.user_id,
            "stamina": user.stamina.stamina,
            "max_stamina_ts": user.stamina.max_stamina_ts,
            "next_fragstam_ts": user.next_fragstam_ts,
            'world_mode_locked_end_ts': -1
        })


@bp.route('/me/redeem', methods=['POST'])  # 兑换码
@auth_required(request)
@arc_try
def redeem(user_id):
    with Connect() as c:
        x = UserRedeem(c, UserOnline(c, user_id))
        x.claim_user_redeem(request.form['code'])

        return success_return({"coupon": "fragment" + str(x.fragment) if x.fragment > 0 else ""})
