from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from web.login import login_required
from werkzeug.utils import secure_filename
import sqlite3
import web.webscore
import web.system
import time
import server.arcscore
import os

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
            conn = sqlite3.connect('./database/arcaea_database.db')
            c = conn.cursor()
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
            conn.commit()
            conn.close()

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
            conn = sqlite3.connect('./database/arcaea_database.db')
            c = conn.cursor()
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
                recent, recentptt = web.webscore.get_user_recent30(c, user_id)
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

            conn.commit()
            conn.close()
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
    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    c.execute('''select * from user order by rating_ptt DESC''')
    x = c.fetchall()
    error = None
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
                          'ticket': i[26]
                          })
    else:
        error = '没有玩家数据 No player data.'

    conn.commit()
    conn.close()
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

    conn = sqlite3.connect('./database/arcsong.db')
    c = conn.cursor()
    c.execute('''select * from songs''')
    x = c.fetchall()
    error = None
    if x:
        posts = []
        for i in x:
            posts.append({'song_id': i[0],
                          'name_en': i[1],
                          'rating_pst': defnum(i[12]),
                          'rating_prs': defnum(i[13]),
                          'rating_ftr': defnum(i[14]),
                          'rating_byn': defnum(i[15])
                          })
    else:
        error = '没有铺面数据 No song data.'

    conn.commit()
    conn.close()
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
        error = None
        conn = sqlite3.connect('./database/arcsong.db')
        c = conn.cursor()
        song_name = '%'+song_name+'%'
        c.execute('''select sid, name_en from songs where sid like :a limit 1''',
                  {'a': song_name})
        x = c.fetchone()
        conn.commit()
        conn.close()
        print(x)
        if x:
            song_id = x[0]
            posts = server.arcscore.arc_score_top(song_id, difficulty, -1)
            for i in posts:
                i['time_played'] = time.strftime('%Y-%m-%d %H:%M:%S',
                                                 time.localtime(i['time_played']))
        else:
            error = '查询为空 No song.'

        if not error:
            return render_template('web/singlecharttop.html', posts=posts, song_name_en=x[1], song_id=song_id, difficulty=difficulty)
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

        if file and allowed_file(file.filename) and file.filename in ['arcsong.db', 'arcaea_database.db']:
            filename = 'old_' + secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            flash('上传成功 Success upload.')
            try:
                web.system.update_database()
                flash('数据更新成功 Success update data.')
            except:
                flash('数据更新失败 Cannot update data.')
        else:
            error = '上传失败 Upload error.'

        if error:
            flash(error)

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
    conn = sqlite3.connect('./database/arcsong.db')
    c = conn.cursor()
    c.execute(
        '''select exists(select * from songs where sid=:a)''', {'a': song_id})
    if c.fetchone() == (0,):
        c.execute('''insert into songs(sid,name_en,rating_pst,rating_prs,rating_ftr,rating_byn) values(:a,:b,:c,:d,:e,:f)''', {
                  'a': song_id, 'b': name_en, 'c': rating_pst, 'd': rating_prs, 'e': rating_ftr, 'f': rating_byd})
        flash('歌曲添加成功 Successfully add the song.')
    else:
        error = '歌曲已存在 The song exists.'

    conn.commit()
    conn.close()

    if error:
        flash(error)

    return redirect(url_for('index.change_song'))


@bp.route('/changesong/deletesong', methods=['POST'])
@login_required
def delete_song():
    # 删除歌曲数据

    error = None
    song_id = request.form['sid']
    conn = sqlite3.connect('./database/arcsong.db')
    c = conn.cursor()
    c.execute(
        '''select exists(select * from songs where sid=:a)''', {'a': song_id})
    if c.fetchone() == (1,):
        c.execute('''delete from songs where sid=:a''', {'a': song_id})
        flash('歌曲删除成功 Successfully delete the song.')
    else:
        error = "歌曲不存在 The song doesn't exist."

    conn.commit()
    conn.close()
    if error:
        flash(error)

    return redirect(url_for('index.change_song'))


@bp.route('/allchar', methods=['GET'])
@login_required
def all_character():
    # 所有角色数据

    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    c.execute('''select * from character''')
    x = c.fetchall()
    error = None
    if x:
        posts = []
        for i in x:
            posts.append({'character_id': i[0],
                          'name': i[1],
                          'level': i[2],
                          'frag': i[5],
                          'prog': i[6],
                          'overdrive': i[7],
                          'skill_id': i[8],
                          'skill_id_uncap': i[11],
                          'char_type': i[12],
                          'is_uncapped': i[14] == 1
                          })
    else:
        error = '没有角色数据 No character data.'

    conn.commit()
    conn.close()
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
                 'frag_rng_ayu', 'gaugestart_30|gaugegain_70', 'combo_100-frag_1', 'audio_gcemptyhit_pack_groovecoaster', 'gauge_saya', 'gauge_chuni', 'kantandeshou', 'gauge_haruna', 'frags_nono', 'gauge_pandora', 'gauge_regulus', 'omatsuri_daynight', 'sometimes(note_mirror|frag_plus_5)', 'scoreclear_aa|visual_scoregauge', 'gauge_tempest', 'gauge_hard', 'gauge_ilith_summer', 'frags_kou', 'visual_ink', 'shirabe_entry_fee', 'frags_yume']
    return render_template('web/changechar.html', skill_ids=skill_ids)


@bp.route('/changesong/editchar', methods=['POST'])
@login_required
def edit_char():
    # 修改角色数据

    error = None

    try:
        character_id = int(request.form['id'])
        level = request.form['level']
        frag = request.form['frag']
        prog = request.form['prog']
        overdrive = request.form['overdrive']
        skill_id = request.form['skill_id']
        skill_id_uncap = request.form['skill_id_uncap']
        if level:
            level = int(level)
        else:
            level = None
        if frag:
            frag = float(frag)
        else:
            frag = None
        if prog:
            prog = float(prog)
        else:
            prog = None
        if overdrive:
            overdrive = float(overdrive)
        else:
            overdrive = None
    except:
        error = '数据错误 Wrong data.'
        flash(error)
        return redirect(url_for('index.change_character'))

    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    c.execute(
        '''select exists(select * from character where character_id=:a)''', {'a': character_id})
    if c.fetchone() == (1,):
        if not level and not frag and not prog and not overdrive and not skill_id and not skill_id_uncap:
            error = '无修改 No change.'
        else:

            sql = '''update character set level_exp=25000'''
            sql_dict = {'character_id': character_id}
            if level:
                sql += ', level = :level'
                sql_dict['level'] = level
            if frag:
                sql += ', frag = :frag'
                sql_dict['frag'] = frag
            if prog:
                sql += ', prog = :prog'
                sql_dict['prog'] = prog
            if overdrive:
                sql += ', overdrive = :overdrive'
                sql_dict['overdrive'] = overdrive
            if skill_id:
                sql += ', skill_id = :skill_id'
                if skill_id == 'No_skill':
                    sql_dict['skill_id'] = ''
                else:
                    sql_dict['skill_id'] = skill_id
            if skill_id_uncap:
                sql += ', skill_id_uncap = :skill_id_uncap'
                if skill_id_uncap == 'No_skill':
                    sql_dict['skill_id_uncap'] = ''
                else:
                    sql_dict['skill_id_uncap'] = skill_id_uncap
            sql += ' where character_id = :character_id'
            c.execute(sql, sql_dict)
            flash('角色修改成功 Successfully edit the character.')
    else:
        error = '角色不存在 The character does not exist.'

    conn.commit()
    conn.close()

    if error:
        flash(error)

    return redirect(url_for('index.change_character'))


@bp.route('/changesong/updatechar', methods=['POST'])
@login_required
def update_character():
    # 更新角色数据
    conn = sqlite3.connect('./database/arcaea_database.db')
    c = conn.cursor()
    web.system.update_user_char(c)
    conn.commit()
    conn.close()

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
    name = request.form['name']
    user_code = request.form['user_code']

    if name or user_code:
        conn = sqlite3.connect('./database/arcaea_database.db')
        c = conn.cursor()
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
        error = '输入为空 Null Input.'

    conn.commit()
    conn.close()

    if error:
        flash(error)

    return redirect(url_for('index.change_user'))
