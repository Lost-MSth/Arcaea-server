import os
import time

from core.init import FileChecker
from core.operation import RefreshAllScoreRating, RefreshSongFileCache, SaveUpdateScore, UnlockUserItem
from core.rank import RankList
from core.sql import Connect
from core.user import User
from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

import web.system
import web.webscore
from web.login import login_required

UPLOAD_FOLDER = 'database'
ALLOWED_EXTENSIONS = {'db'}

bp = Blueprint('index', __name__, url_prefix='/web')


def is_number(s):
    try:  # 判断字符串s是浮点数
        float(s)
        return True
    except ValueError:
        pass
    return False


@bp.route('/index')
@bp.route('/')
@login_required
def index():
    # 主页
    return render_template('web/index.html')


@bp.route('/singleplayer', methods=['POST', 'GET'])
@login_required
def single_player_score():
    # 单个玩家分数查询
    if request.method == 'POST':
        name = request.form['name']
        user_code = request.form['user_code']
        error = None
        if name or user_code:
            with Connect() as c:
                if user_code:
                    c.execute('''select user_id from user where user_code=:a''', {
                        'a': user_code})
                else:
                    c.execute(
                        '''select user_id from user where name=:a''', {'a': name})

                user_id = c.fetchone()
                posts = []
                if user_id:
                    user_id = user_id[0]
                    posts = web.webscore.get_user_score(c, user_id)
                    if not posts:
                        error = '无成绩 No score.'
                else:
                    error = '玩家不存在 The player does not exist.'

        else:
            error = '输入为空 Null Input.'

        if error:
            flash(error)
        else:
            return render_template('web/singleplayer.html', posts=posts)

    return render_template('web/singleplayer.html')


@bp.route('/singleplayerptt', methods=['POST', 'GET'])
@login_required
def single_player_ptt():
    # 单个玩家PTT详情查询
    if request.method == 'POST':
        name = request.form['name']
        user_code = request.form['user_code']
        error = None
        if name or user_code:
            with Connect() as c:
                if user_code:
                    c.execute('''select user_id from user where user_code=:a''', {
                        'a': user_code})
                else:
                    c.execute(
                        '''select user_id from user where name=:a''', {'a': name})

                user_id = c.fetchone()
                posts = []
                if user_id:
                    user_id = user_id[0]
                    user = web.webscore.get_user(c, user_id)
                    posts = web.webscore.get_user_score(c, user_id, 30)
                    recent, recentptt = web.webscore.get_user_recent30(
                        c, user_id)
                    if not posts:
                        error = '无成绩 No score.'
                    else:
                        bestptt = 0
                        for i in posts:
                            if i['rating']:
                                bestptt += i['rating']
                        bestptt = bestptt / 30
                else:
                    error = '玩家不存在 The player does not exist.'

        else:
            error = '输入为空 Null Input.'

        if error:
            flash(error)
        else:
            return render_template('web/singleplayerptt.html', posts=posts, user=user, recent=recent, recentptt=recentptt, bestptt=bestptt)

    return render_template('web/singleplayerptt.html')


@bp.route('/allplayer', methods=['GET'])
@login_required
def all_player():
    # 所有玩家数据，按照ptt排序
    error = None
    with Connect() as c:
        c.execute('''select * from user order by rating_ptt DESC''')
        x = c.fetchall()
        if x:
            posts = []
            for i in x:
                join_data = None
                time_played = None
                if i[3]:
                    join_date = time.strftime('%Y-%m-%d %H:%M:%S',
                                              time.localtime(int(i[3])//1000))
                if i[20]:
                    time_played = time.strftime('%Y-%m-%d %H:%M:%S',
                                                time.localtime(int(i[20])//1000))
                if i[2] == '':
                    ban_flag = True
                else:
                    ban_flag = False

                posts.append({'name': i[1],
                              'user_id': i[0],
                              'join_date': join_date,
                              'user_code': i[4],
                              'rating_ptt': i[5],
                              'song_id': i[11],
                              'difficulty': i[12],
                              'score': i[13],
                              'shiny_perfect_count': i[14],
                              'perfect_count': i[15],
                              'near_count': i[16],
                              'miss_count': i[17],
                              'time_played': time_played,
                              'clear_type': i[21],
                              'rating': i[22],
                              'ticket': i[26],
                              'ban_flag': ban_flag
                              })
        else:
            error = '没有玩家数据 No player data.'

    if error:
        flash(error)
        return render_template('web/allplayer.html')
    else:
        return render_template('web/allplayer.html', posts=posts)


@bp.route('/allsong', methods=['GET'])
@login_required
def all_song():
    # 所有歌曲数据
    def defnum(x):
        # 定数转换
        if x >= 0:
            return x / 10
        else:
            return None

    error = None
    with Connect() as c:
        c.execute('''select * from chart''')
        x = c.fetchall()
        if x:
            posts = []
            for i in x:
                posts.append({'song_id': i[0],
                              'name_en': i[1],
                              'rating_pst': defnum(i[2]),
                              'rating_prs': defnum(i[3]),
                              'rating_ftr': defnum(i[4]),
                              'rating_byn': defnum(i[5])
                              })
        else:
            error = '没有谱面数据 No song data.'

    if error:
        flash(error)
        return render_template('web/allsong.html')
    else:
        return render_template('web/allsong.html', posts=posts)


@bp.route('/singlecharttop', methods=['GET', 'POST'])
@login_required
def single_chart_top():
    # 歌曲排行榜
    if request.method == 'POST':
        song_name = request.form['sid']
        difficulty = request.form['difficulty']
        if difficulty.isdigit():
            difficulty = int(difficulty)
        else:
            difficulty = 0
        error = None
        x = None
        with Connect() as c:
            song_name = '%'+song_name+'%'
            c.execute('''select song_id, name from chart where song_id like :a limit 1''',
                      {'a': song_name})
            x = c.fetchone()

            if x:
                y = RankList(c)
                y.song.set_chart(x[0], difficulty)
                y.limit = -1
                y.select_top()
                posts = y.to_dict_list()
                for i in posts:
                    i['time_played'] = time.strftime('%Y-%m-%d %H:%M:%S',
                                                     time.localtime(i['time_played']))
            else:
                error = '查询为空 No song.'

        if not error:
            return render_template('web/singlecharttop.html', posts=posts, song_name_en=x[1], song_id=x[0], difficulty=difficulty)
        else:
            flash(error)

    return render_template('web/singlecharttop.html')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/updatedatabase', methods=['GET', 'POST'])
@login_required
def update_database():
    # 更新数据库
    error = None
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('无文件 No file part.')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('未选择文件 No selected file.')
            return redirect(request.url)

        if file and allowed_file(file.filename) and file.filename in ['arcaea_database.db']:
            filename = 'old_' + secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            flash('上传成功 Success upload.')
            try:
                FileChecker.update_database(
                    os.path.join(UPLOAD_FOLDER, filename))
                flash('数据更新成功 Success update data.')
            except:
                flash('数据更新失败 Cannot update data.')
        else:
            error = '上传失败 Upload error.'

        if error:
            flash(error)

    return render_template('web/updatedatabase.html')


@bp.route('/updatedatabase/refreshsonghash', methods=['POST'])
@login_required
def update_song_hash():
    # 更新数据库内谱面文件hash值
    try:
        RefreshSongFileCache().run()
        flash('数据刷新成功 Success refresh data.')
    except:
        flash('Something error!')
    return render_template('web/updatedatabase.html')


@bp.route('/updatedatabase/refreshsongrating', methods=['POST'])
@login_required
def update_song_rating():
    # 更新所有分数的rating
    RefreshAllScoreRating().run()
    flash('数据刷新成功 Success refresh data.')
    return render_template('web/updatedatabase.html')


@bp.route('/changesong', methods=['GET'])
@login_required
def change_song():
    # 修改歌曲数据
    return render_template('web/changesong.html')


@bp.route('/changesong/addsong', methods=['POST'])
@login_required
def add_song():
    # 添加歌曲数据
    def get_rating(x):
        # 换算定数
        if is_number(x):
            x = float(x)
            if x >= 0:
                return int(x*10)
            else:
                return -1
        else:
            return -1

    error = None
    song_id = request.form['sid']
    name_en = request.form['name_en']
    rating_pst = get_rating(request.form['rating_pst'])
    rating_prs = get_rating(request.form['rating_prs'])
    rating_ftr = get_rating(request.form['rating_ftr'])
    rating_byd = get_rating(request.form['rating_byd'])
    if len(song_id) >= 256:
        song_id = song_id[:200]
    if len(name_en) >= 256:
        name_en = name_en[:200]

    with Connect() as c:
        c.execute(
            '''select exists(select * from chart where song_id=:a)''', {'a': song_id})
        if c.fetchone() == (0,):
            c.execute('''insert into chart values(:a,:b,:c,:d,:e,:f)''', {
                'a': song_id, 'b': name_en, 'c': rating_pst, 'd': rating_prs, 'e': rating_ftr, 'f': rating_byd})
            flash('歌曲添加成功 Successfully add the song.')
        else:
            error = '歌曲已存在 The song exists.'

    if error:
        flash(error)

    return redirect(url_for('index.change_song'))


@bp.route('/changesong/deletesong', methods=['POST'])
@login_required
def delete_song():
    # 删除歌曲数据

    error = None
    song_id = request.form['sid']
    with Connect() as c:
        c.execute(
            '''select exists(select * from chart where song_id=:a)''', {'a': song_id})
        if c.fetchone() == (1,):
            c.execute('''delete from chart where song_id=:a''', {'a': song_id})
            flash('歌曲删除成功 Successfully delete the song.')
        else:
            error = "歌曲不存在 The song doesn't exist."

    if error:
        flash(error)

    return redirect(url_for('index.change_song'))


@bp.route('/allchar', methods=['GET'])
@login_required
def all_character():
    # 所有角色数据
    error = None
    with Connect() as c:
        c.execute('''select * from character''')
        x = c.fetchall()
        if x:
            posts = []
            for i in x:
                posts.append({'character_id': i[0],
                              'name': i[1],
                              'max_level': i[2],
                              'frag1': i[3],
                              'prog1': i[4],
                              'overdrive1': i[5],
                              'frag20': i[6],
                              'prog20': i[7],
                              'overdrive20': i[8],
                              'frag30': i[9],
                              'prog30': i[10],
                              'overdrive30': i[11],
                              'skill_id': i[12],
                              'skill_unlock_level': i[13],
                              'skill_id_uncap': i[15],
                              'char_type': i[16],
                              'is_uncapped': i[17] == 1
                              })
        else:
            error = '没有角色数据 No character data.'

    if error:
        flash(error)
        return render_template('web/allchar.html')
    else:
        return render_template('web/allchar.html', posts=posts)


@bp.route('/changechar', methods=['GET'])
@login_required
def change_character():
    # 修改角色数据
    skill_ids = ['No_skill', 'gauge_easy', 'note_mirror', 'gauge_hard', 'frag_plus_10_pack_stellights', 'gauge_easy|frag_plus_15_pst&prs', 'gauge_hard|fail_frag_minus_100', 'frag_plus_5_side_light', 'visual_hide_hp', 'frag_plus_5_side_conflict', 'challenge_fullcombo_0gauge', 'gauge_overflow', 'gauge_easy|note_mirror', 'note_mirror', 'visual_tomato_pack_tonesphere',
                 'frag_rng_ayu', 'gaugestart_30|gaugegain_70', 'combo_100-frag_1', 'audio_gcemptyhit_pack_groovecoaster', 'gauge_saya', 'gauge_chuni', 'kantandeshou', 'gauge_haruna', 'frags_nono', 'gauge_pandora', 'gauge_regulus', 'omatsuri_daynight', 'sometimes(note_mirror|frag_plus_5)', 'scoreclear_aa|visual_scoregauge', 'gauge_tempest', 'gauge_hard', 'gauge_ilith_summer', 'frags_kou', 'visual_ink', 'shirabe_entry_fee', 'frags_yume', 'note_mirror|visual_hide_far', 'frags_ongeki', 'gauge_areus', 'gauge_seele', 'gauge_isabelle', 'gauge_exhaustion', 'skill_lagrange', 'gauge_safe_10', 'frags_nami', 'skill_elizabeth', 'skill_lily', 'skill_kanae_midsummer', 'eto_uncap', 'luna_uncap', 'frags_preferred_song', 'visual_ghost_skynotes', 'ayu_uncap', 'skill_vita', 'skill_fatalis', 'skill_reunion', 'frags_ongeki_slash', 'frags_ongeki_hard', 'skill_amane', 'skill_kou_winter', 'gauge_hard|note_mirror', 'skill_shama', 'skill_milk', 'skill_shikoku', 'skill_mika', 'ilith_awakened_skill', 'skill_mithra', 'skill_toa', 'skill_nami_twilight', 'skill_ilith_ivy', 'skill_hikari_vanessa', 'skill_maya', 'skill_luin', 'skill_luin_uncap']
    return render_template('web/changechar.html', skill_ids=skill_ids)


@bp.route('/changesong/editchar', methods=['POST'])
@login_required
def edit_char():
    # 修改角色数据

    error = None

    try:
        character_id = int(request.form['id'])
        level = request.form['level']
        skill_id = request.form['skill_id']
        skill_id_uncap = request.form['skill_id_uncap']
        if level:
            level = int(level)
        else:
            level = None
    except:
        error = '数据错误 Wrong data.'
        flash(error)
        return redirect(url_for('index.change_character'))

    with Connect() as c:
        c.execute(
            '''select exists(select * from character where character_id=:a)''', {'a': character_id})
        if c.fetchone() == (1,):
            if level is None and skill_id is None and skill_id_uncap is None:
                error = '无修改 No change.'
            else:
                sql = '''update character set '''
                sql_dict = {'character_id': character_id}
                if level is not None:
                    sql += 'max_level = :level, '
                    sql_dict['level'] = level
                if skill_id is not None:
                    sql += 'skill_id = :skill_id, '
                    if skill_id == 'No_skill':
                        sql_dict['skill_id'] = ''
                    else:
                        sql_dict['skill_id'] = skill_id
                if skill_id_uncap is not None:
                    sql += 'skill_id_uncap = :skill_id_uncap, '
                    if skill_id_uncap == 'No_skill':
                        sql_dict['skill_id_uncap'] = ''
                    else:
                        sql_dict['skill_id_uncap'] = skill_id_uncap

                sql = sql[:-2]
                sql += ' where character_id = :character_id'
                c.execute(sql, sql_dict)
                flash('角色修改成功 Successfully edit the character.')
        else:
            error = '角色不存在 The character does not exist.'

    if error:
        flash(error)

    return redirect(url_for('index.change_character'))


@bp.route('/changesong/updatechar', methods=['POST'])
@login_required
def update_character():
    # 更新角色数据
    with Connect() as c:
        web.system.update_user_char(c)

    flash('数据更新成功 Success update data.')
    return redirect(url_for('index.change_character'))


@bp.route('/changeuser', methods=['GET'])
@login_required
def change_user():
    # 修改用户信息

    return render_template('web/changeuser.html')


@bp.route('/changeuser/edituser', methods=['POST'])
@login_required
def edit_user():
    # 修改用户数据

    error = None
    flag = True
    name = None
    user_code = None
    try:
        ticket = request.form['ticket']
        if ticket:
            ticket = int(ticket)
        else:
            ticket = None
    except:
        error = '数据错误 Wrong data.'
        flash(error)
        return redirect(url_for('index.change_user'))

    with Connect() as c:

       # 全修改
        if 'name' not in request.form and 'user_code' not in request.form:
            flag = False
            if not ticket:
                error = '无修改 No change.'
            else:
                sql = '''update user set ticket = :ticket'''
                sql_dict = {'ticket': ticket}
                c.execute(sql, sql_dict)
                flash("全部用户信息修改成功 Successfully edit all the users' information.")

        else:
            name = request.form['name']
            user_code = request.form['user_code']

        # 指定修改

        if name or user_code:

            if user_code:
                c.execute('''select user_id from user where user_code=:a''', {
                    'a': user_code})
            else:
                c.execute(
                    '''select user_id from user where name=:a''', {'a': name})

            user_id = c.fetchone()
            if user_id:
                user_id = user_id[0]

                if not ticket:
                    error = '无修改 No change.'
                else:
                    sql = '''update user set ticket = :ticket where user_id = :user_id'''
                    sql_dict = {'ticket': ticket, 'user_id': user_id}
                    c.execute(sql, sql_dict)
                    flash('用户信息修改成功 Successfully edit the user information.')

            else:
                error = '玩家不存在 The player does not exist.'

        else:
            if flag:
                error = '输入为空 Null Input.'

    if error:
        flash(error)

    return redirect(url_for('index.change_user'))


@bp.route('/changeuserpurchase', methods=['GET'])
@login_required
def change_user_purchase():
    # 修改用户购买

    return render_template('web/changeuserpurchase.html')


@bp.route('/changeuserpurchase/edituser', methods=['POST'])
@login_required
def edit_user_purchase():
    # 修改用户购买

    error = None
    flag = True
    name = None
    user_code = None
    try:
        method = request.form['method']
    except:
        flash('输入为空 Null Input.')
        return redirect(url_for('index.change_user_purchase'))

    with Connect() as c:

        # 全修改
        if 'name' not in request.form and 'user_code' not in request.form:
            flag = False
            if method == '0':
                UnlockUserItem().run()
            else:
                c.execute(
                    '''delete from user_item where type in ('pack', 'single')''')

            flash("全部用户购买信息修改成功 Successfully edit all the users' purchase information.")

        else:
            name = request.form['name']
            user_code = request.form['user_code']

        # 指定修改
        if name or user_code:

            if user_code:
                c.execute('''select user_id from user where user_code=:a''', {
                    'a': user_code})
            else:
                c.execute(
                    '''select user_id from user where name=:a''', {'a': name})

            user_id = c.fetchone()
            if user_id:
                user_id = user_id[0]

                if method == '0':
                    x = UnlockUserItem()
                    x.set_params(user_id=user_id)
                    x.run()
                else:
                    c.execute('''delete from user_item where type in ('pack', 'single') and user_id = :user_id''', {
                        'user_id': user_id})
                flash('用户购买信息修改成功 Successfully edit the user purchase information.')

            else:
                error = '玩家不存在 The player does not exist.'

        else:
            if flag:
                error = '输入为空 Null Input.'

    if error:
        flash(error)

    return redirect(url_for('index.change_user_purchase'))


@bp.route('/allitem', methods=['GET'])
@login_required
def all_item():
    # 所有物品数据

    error = None
    posts = web.system.get_all_item()
    if not posts:
        error = '没有物品数据 No item data.'

    if error:
        flash(error)
        return render_template('web/allitem.html')
    else:
        return render_template('web/allitem.html', posts=posts)


@bp.route('/changeitem', methods=['GET', 'POST'])
@login_required
def change_item():
    # 添加物品信息

    error = None
    if request.method == 'POST':
        try:
            item_id = request.form['item_id']
            item_type = request.form['type']
            try:
                is_available = request.form['is_available']
                if is_available:
                    is_available = int(is_available)
                else:
                    is_available = 0
            except:
                is_available = 0

        except:
            error = '数据错误 Wrong data.'
            flash(error)
            return redirect(url_for('index.change_item'))

        with Connect() as c:
            c.execute(
                '''select exists(select * from item where item_id=:a and type=:b)''', {'a': item_id, 'b': item_type})
            if c.fetchone() == (0,):
                c.execute('''insert into item values(?,?,?)''',
                          (item_id, item_type, is_available))
                flash('物品添加成功 Successfully add the item.')
            else:
                error = '物品已存在 The item exists.'

        if error:
            flash(error)

    return render_template('web/changeitem.html')


@bp.route('/changeitem/delete', methods=['POST'])
@login_required
def change_item_delete():
    # 删除物品信息

    error = None
    try:
        item_id = request.form['item_id']
        item_type = request.form['type']
    except:
        error = '数据错误 Wrong data.'
        flash(error)
        return redirect(url_for('index.change_item'))

    with Connect() as c:
        c.execute(
            '''select exists(select * from item where item_id=:a and type=:b)''', {'a': item_id, 'b': item_type})
        if c.fetchone() == (1,):
            c.execute('''delete from item where item_id=? and type=?''',
                      (item_id, item_type))
            flash('物品删除成功 Successfully delete the item.')
        else:
            error = '物品不存在 The item does not exist.'

    if error:
        flash(error)

    return render_template('web/changeitem.html')


@bp.route('/allpurchase', methods=['GET'])
@login_required
def all_purchase():
    # 所有购买数据

    error = None
    posts = web.system.get_all_purchase()
    if not posts:
        error = '没有购买数据 No purchase data.'

    if error:
        flash(error)
        return render_template('web/allpurchase.html')
    else:
        return render_template('web/allpurchase.html', posts=posts)


@bp.route('/changepurchase', methods=['GET', 'POST'])
@login_required
def change_purchase():
    # 添加购买信息

    error = None
    if request.method == 'POST':
        try:
            purchase_name = request.form['purchase_name']
            price = request.form['price']
            orig_price = request.form['orig_price']
            discount_from = request.form['discount_from']
            discount_to = request.form['discount_to']
            discount_reason = request.form['discount_reason']

            if price:
                price = int(price)
            else:
                price = None
            if orig_price:
                orig_price = int(orig_price)
            else:
                orig_price = None
            if discount_from:
                discount_from = int(time.mktime(time.strptime(
                    discount_from, "%Y-%m-%dT%H:%M"))) * 1000
            else:
                discount_from = -1
            if discount_to:
                discount_to = int(time.mktime(time.strptime(
                    discount_to, "%Y-%m-%dT%H:%M"))) * 1000
            else:
                discount_to = -1

            if not discount_reason:
                discount_reason = ''

        except:
            error = '数据错误 Wrong data.'
            flash(error)
            return redirect(url_for('index.change_purchase'))

        with Connect() as c:
            c.execute(
                '''select exists(select * from purchase where purchase_name=:a)''', {'a': purchase_name})
            if c.fetchone() == (0,):
                c.execute('''insert into purchase values(?,?,?,?,?,?)''',
                          (purchase_name, price, orig_price, discount_from, discount_to, discount_reason))

                flash('购买项目添加成功 Successfully add the purchase.')
            else:
                error = '购买项目已存在 The purchase exists.'

        if error:
            flash(error)

    return render_template('web/changepurchase.html')


@bp.route('/changepurchase/delete', methods=['POST'])
@login_required
def change_purchase_delete():
    # 删除购买信息

    error = None
    try:
        purchase_name = request.form['purchase_name']
    except:
        error = '数据错误 Wrong data.'
        flash(error)
        return redirect(url_for('index.change_purchase'))

    with Connect() as c:
        c.execute(
            '''select exists(select * from purchase where purchase_name=:a)''', {'a': purchase_name})
        if c.fetchone() == (1,):
            c.execute('''delete from purchase where purchase_name=?''',
                      (purchase_name,))
            c.execute('''delete from purchase_item where purchase_name=?''',
                      (purchase_name,))
            flash('购买信息删除成功 Successfully delete the purchase.')
        else:
            error = '购买信息不存在 The purchase does not exist.'

    if error:
        flash(error)

    return render_template('web/changepurchase.html')


@bp.route('/changepurchaseitem', methods=['GET', 'POST'])
@login_required
def change_purchase_item():
    # 添加购买的物品信息

    error = None
    if request.method == 'POST':
        try:
            purchase_name = request.form['purchase_name']
            item_id = request.form['item_id']
            item_type = request.form['type']
            amount = int(request.form['amount'])
        except:
            error = '数据错误 Wrong data.'
            flash(error)
            return redirect(url_for('index.change_purchase_item'))

        with Connect() as c:
            c.execute(
                '''select exists(select * from purchase_item where purchase_name=? and item_id=? and type=?)''', (purchase_name, item_id, item_type))
            if c.fetchone() == (0,):
                c.execute(
                    '''select exists(select * from purchase where purchase_name=?)''', (purchase_name,))
                if c.fetchone() == (1,):
                    c.execute(
                        '''select exists(select * from item where item_id=? and type=?)''', (item_id, item_type))
                    if c.fetchone() == (1,):
                        c.execute('''insert into purchase_item values(?,?,?,?)''',
                                  (purchase_name, item_id, item_type, amount))
                        flash('''购买项目的物品添加成功 Successfully add the purchase's item.''')
                    else:
                        error = '''物品不存在 The item does not exist.'''
                else:
                    error = '''购买项目不存在 The purchase does not exist.'''
            else:
                error = '''购买项目的物品已存在 The purchase's item exists.'''

        if error:
            flash(error)

    return render_template('web/changepurchaseitem.html')


@bp.route('/changepurchaseitem/delete', methods=['POST'])
@login_required
def change_purchase_item_delete():
    # 删除购买的物品信息

    error = None
    try:
        purchase_name = request.form['purchase_name']
        item_id = request.form['item_id']
        item_type = request.form['type']
    except:
        error = '数据错误 Wrong data.'
        flash(error)
        return redirect(url_for('index.change_purchase_item'))

    with Connect() as c:
        c.execute(
            '''select exists(select * from purchase_item where purchase_name=? and item_id=? and type=?)''', (purchase_name, item_id, item_type))
        if c.fetchone() == (1,):
            c.execute('''delete from purchase_item where purchase_name=? and item_id=? and type=?''',
                      (purchase_name, item_id, item_type))

            flash('''购买项目的物品删除成功 Successfully delete the purchase's item.''')
        else:
            error = '''购买项目的物品不存在 The purchase's item does not exist.'''

    if error:
        flash(error)

    return render_template('web/changepurchaseitem.html')


@bp.route('/updateusersave', methods=['POST', 'GET'])
@login_required
def update_user_save():
    # 将用户存档覆盖到分数表中

    if request.method == 'GET':
        return render_template('web/updateusersave.html')

    error = None
    flag = True
    name = None
    user_code = None

    with Connect() as c:

        # 全修改
        if 'name' not in request.form and 'user_code' not in request.form:
            flag = False
            SaveUpdateScore().run()
            flash("全部用户存档同步成功 Successfully update all users' saves.")

        else:
            name = request.form['name']
            user_code = request.form['user_code']

        # 指定修改
        if name or user_code:

            if user_code:
                c.execute('''select user_id from user where user_code=:a''', {
                    'a': user_code})
            else:
                c.execute(
                    '''select user_id from user where name=:a''', {'a': name})

            user_id = c.fetchone()
            if user_id:
                user_id = user_id[0]
                user = User()
                user.user_id = user_id
                SaveUpdateScore(user).run()
                flash("用户存档同步成功 Successfully update the user's saves.")

            else:
                error = '玩家不存在 The player does not exist.'

        else:
            if flag:
                error = '输入为空 Null Input.'

    if error:
        flash(error)

    return render_template('web/updateusersave.html')


@bp.route('/allpresent', methods=['GET'])
@login_required
def all_present():
    # 所有奖励数据

    error = None
    with Connect() as c:
        c.execute('''select * from present''')
        x = c.fetchall()
        if x:
            posts = []
            for i in x:
                items = []
                c.execute(
                    '''select * from present_item where present_id=?''', (i[0],))
                y = c.fetchall()
                for j in y:
                    if j is not None:
                        items.append(
                            {'item_id': j[1], 'type': j[2], 'amount': j[3]})

                posts.append({'present_id': i[0],
                              'expire_ts': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(i[1])//1000)),
                              'items': items,
                              'description': i[2]
                              })
        else:
            error = '没有奖励数据 No present data.'

    if error:
        flash(error)
        return render_template('web/allpresent.html')
    else:
        return render_template('web/allpresent.html', posts=posts)


@bp.route('/changepresent', methods=['GET'])
@login_required
def change_present():
    # 修改奖励数据
    return render_template('web/changepresent.html')


@bp.route('/changepresent/addpresent', methods=['POST'])
@login_required
def add_present():
    # 添加奖励数据
    present_id = request.form['present_id']
    expire_ts = request.form['expire_ts']
    description = request.form['description']
    item_id = request.form['item_id']
    item_type = request.form['type']
    item_amount = request.form['amount']

    try:
        if item_amount:
            item_amount = int(item_amount)
        else:
            item_amount = 1
        expire_ts = int(time.mktime(time.strptime(
            expire_ts, "%Y-%m-%dT%H:%M"))) * 1000
    except:
        flash('数据错误 Wrong data.')
        return redirect(url_for('index.change_present'))

    if len(present_id) >= 256:
        present_id = present_id[:200]
    if len(description) >= 256:
        description = description[:200]

    message = web.system.add_one_present(
        present_id, expire_ts, description, item_id, item_type, item_amount)

    if message:
        flash(message)

    return redirect(url_for('index.change_present'))


@bp.route('/changepresent/deletepresent', methods=['POST'])
@login_required
def delete_present():
    # 删除奖励数据
    present_id = request.form['present_id']
    message = web.system.delete_one_present(present_id)

    if message:
        flash(message)

    return redirect(url_for('index.change_present'))


@bp.route('/deliverpresent', methods=['GET', 'POST'])
@login_required
def deliver_present():
    # 分发奖励

    if request.method == 'GET':
        return render_template('web/deliverpresent.html')

    error = None
    flag = True
    name = None
    user_code = None
    present_id = request.form['present_id']

    with Connect() as c:
        if not web.system.is_present_available(c, present_id):
            flash("奖励不存在 The present does not exist.")
            return render_template('web/deliverpresent.html')

        # 全修改
        if 'name' not in request.form and 'user_code' not in request.form:
            flag = False
            web.system.deliver_all_user_present(c, present_id)
            flash("全部用户奖励分发成功 Successfully deliver the present to all users.")
        else:
            name = request.form['name']
            user_code = request.form['user_code']

        # 指定修改f
        if name or user_code:
            if user_code:
                c.execute('''select user_id from user where user_code=:a''', {
                    'a': user_code})
            else:
                c.execute(
                    '''select user_id from user where name=:a''', {'a': name})

            user_id = c.fetchone()
            if user_id:
                user_id = user_id[0]
                web.system.deliver_one_user_present(c, present_id, user_id)
                flash("用户奖励分发成功 Successfully deliver the present to the user.")

            else:
                error = '玩家不存在 The player does not exist.'

        else:
            if flag:
                error = '输入为空 Null Input.'

    if error:
        flash(error)

    return render_template('web/deliverpresent.html')


@bp.route('/allredeem', methods=['GET'])
@login_required
def all_redeem():
    # 所有兑换码数据

    error = None
    with Connect() as c:
        c.execute('''select * from redeem''')
        x = c.fetchall()
        if x:
            posts = []
            for i in x:
                items = []
                c.execute(
                    '''select * from redeem_item where code=?''', (i[0],))
                y = c.fetchall()
                for j in y:
                    if j is not None:
                        items.append(
                            {'item_id': j[1], 'type': j[2], 'amount': j[3]})

                posts.append({'code': i[0],
                              'items': items,
                              'type': i[1]
                              })
        else:
            error = '没有兑换码数据 No redeem code data.'

    if error:
        flash(error)
        return render_template('web/allredeem.html')
    else:
        return render_template('web/allredeem.html', posts=posts)


@bp.route('/changeredeem', methods=['GET'])
@login_required
def change_redeem():
    # 修改兑换码数据
    return render_template('web/changeredeem.html')


@bp.route('/changeredeem/addredeem', methods=['POST'])
@login_required
def add_redeem():
    # 添加兑换码数据
    code = request.form['code']
    redeem_amount = request.form['redeem_amount']
    redeem_type = request.form['redeem_type']
    item_id = request.form['item_id']
    item_type = request.form['type']
    item_amount = request.form['amount']

    try:
        if item_amount:
            item_amount = int(item_amount)
        else:
            item_amount = 1
        if redeem_amount:
            redeem_amount = int(redeem_amount)
    except:
        flash('数据错误 Wrong data.')
        return redirect(url_for('index.change_redeem'))

    if code and not redeem_amount:
        if len(code) > 20 or len(code) < 10:
            flash('兑换码长度不合适 Inappropriate length of redeem code.')
            return redirect(url_for('index.change_redeem'))

        message = web.system.add_one_redeem(
            code, redeem_type, item_id, item_type, item_amount)
    elif redeem_amount and not code:
        if redeem_amount <= 0 or redeem_amount > 1000:
            flash('数量错误 Wrong amount.')
            return redirect(url_for('index.change_redeem'))

        message = web.system.add_some_random_redeem(
            redeem_amount, redeem_type, item_id, item_type, item_amount)
    elif redeem_amount and code:
        flash('只能使用一种添加方式 Only one add method can be used.')
        return redirect(url_for('index.change_redeem'))
    else:
        flash('空输入 Null input.')
        return redirect(url_for('index.change_redeem'))

    if message:
        flash(message)

    return redirect(url_for('index.change_redeem'))


@bp.route('/changeredeem/deleteredeem', methods=['POST'])
@login_required
def delete_redeem():
    # 删除兑换码数据
    code = request.form['code']
    message = web.system.delete_one_redeem(code)

    if message:
        flash(message)

    return redirect(url_for('index.change_redeem'))


@bp.route('/redeem/<code>', methods=['GET'])
@login_required
def one_redeem(code):
    # 某个兑换码的用户使用情况数据

    error = None
    with Connect() as c:
        c.execute(
            '''select user_id, name, user_code from user where user_id in (select user_id from user_redeem where code=:a)''', {'a': code})
        x = c.fetchall()
        if x:
            posts = []
            for i in x:
                posts.append({'user_id': i[0],
                              'name': i[1],
                              'user_code': i[2]
                              })
        else:
            error = '没有数据 No data.'

    if error:
        flash(error)
        return render_template('web/redeem.html', code=code)
    else:
        return render_template('web/redeem.html', posts=posts, code=code)


@bp.route('/changeuserpwd', methods=['GET', 'POST'])
@login_required
def edit_userpwd():
    # 修改用户密码
    if request.method == 'GET':
        return render_template('web/changeuserpwd.html')

    error = None

    name = request.form['name']
    user_code = request.form['user_code']
    pwd = request.form['pwd']
    pwd2 = request.form['pwd2']
    if pwd != pwd2:
        flash('两次输入的密码不一致 Entered passwords differ!')
        return render_template('web/changeuserpwd.html')
    else:
        if len(pwd) < 8 or len(pwd) > 20:
            flash('密码太长或太短 Password is too long or too short!')
            return render_template('web/changeuserpwd.html')

    with Connect() as c:
        if name or user_code:

            if user_code:
                c.execute('''select user_id from user where user_code=:a''', {
                    'a': user_code})
            else:
                c.execute(
                    '''select user_id from user where name=:a''', {'a': name})

            user_id = c.fetchone()
            if user_id:
                user_id = user_id[0]
                web.system.change_userpwd(c, user_id, pwd)
                flash('用户密码修改成功 Successfully edit the user information.')

            else:
                error = '玩家不存在 The player does not exist.'

        else:
            error = '输入为空 Null Input.'

    if error:
        flash(error)

    return redirect(url_for('index.edit_userpwd'))


@bp.route('/banuser', methods=['POST', 'GET'])
@login_required
def ban_user():
    # 封禁用户
    if request.method == 'GET':
        return render_template('web/banuser.html')

    error = None

    name = request.form['name']
    user_code = request.form['user_code']

    with Connect() as c:
        if name or user_code:
            if user_code:
                c.execute('''select user_id from user where user_code=:a''', {
                    'a': user_code})
            else:
                c.execute(
                    '''select user_id from user where name=:a''', {'a': name})

            user_id = c.fetchone()
            if user_id:
                user_id = user_id[0]
                web.system.ban_one_user(c, user_id)
                flash('用户封禁成功 Successfully ban the user.')

            else:
                error = '玩家不存在 The player does not exist.'

        else:
            error = '输入为空 Null Input.'

    if error:
        flash(error)

    return redirect(url_for('index.ban_user'))


@bp.route('/banuser/deleteuserscore', methods=['POST'])
@login_required
def delete_user_score():
    # 删除用户所有成绩
    error = None

    name = request.form['name']
    user_code = request.form['user_code']

    with Connect() as c:
        if name or user_code:
            if user_code:
                c.execute('''select user_id from user where user_code=:a''', {
                    'a': user_code})
            else:
                c.execute(
                    '''select user_id from user where name=:a''', {'a': name})

            user_id = c.fetchone()
            if user_id:
                user_id = user_id[0]
                web.system.clear_user_score(c, user_id)
                flash("用户成绩删除成功 Successfully delete the user's scores.")

            else:
                error = '玩家不存在 The player does not exist.'

        else:
            error = '输入为空 Null Input.'

    if error:
        flash(error)

    return redirect(url_for('index.ban_user'))


@bp.route('/changescore', methods=['GET'])
@login_required
def change_score():
    # 修改成绩页面
    return render_template('web/changescore.html')


@bp.route('/changescore/delete', methods=['POST'])
@login_required
def delete_score():
    # 删除成绩

    song_id = request.form['sid']
    difficulty = request.form['difficulty']
    if difficulty.isdigit() or difficulty == '-1':
        difficulty = int(difficulty)

    name = request.form['name']
    user_code = request.form['user_code']

    error = 'Unknown error.'
    flag = [False, False, False]
    if song_id:
        flag[0] = True
    if difficulty != -1:
        flag[1] = True

    with Connect() as c:
        if name or user_code:
            if user_code:
                c.execute('''select user_id from user where user_code=:a''', {
                    'a': user_code})
            else:
                c.execute(
                    '''select user_id from user where name=:a''', {'a': name})

            user_id = c.fetchone()
            if user_id:
                user_id = user_id[0]
                flag[2] = True
            else:
                error = '玩家不存在 The player does not exist.'

        if flag[0] or flag[1] or flag[2]:
            sql = '''delete from best_score where '''
            sql_dict = {}
            if flag[0]:
                sql += 'song_id=:song_id and '
                sql_dict['song_id'] = song_id
            if flag[1]:
                sql += 'difficulty=:difficulty and '
                sql_dict['difficulty'] = difficulty
            if flag[2]:
                sql += 'user_id=:user_id '
                sql_dict['user_id'] = user_id
            if sql[-4:-1] == 'and':
                sql = sql[:-4]

            c.execute(sql, sql_dict)
            flash('成功删除成绩 Successfully delete the scores.')
            error = None
        else:
            error = '输入为空 Null Input.'

    if error:
        flash(error)

    return redirect(url_for('index.change_score'))
