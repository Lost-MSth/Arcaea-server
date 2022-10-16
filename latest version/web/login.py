import functools
import hashlib

from core.config_manager import Config
from flask import (Blueprint, flash, g, redirect, render_template, request,
                   session, url_for)

bp = Blueprint('login', __name__, url_prefix='/web')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    # 登录
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None

        if username != Config.USERNAME or password != Config.PASSWORD:
            error = '错误的用户名或密码 Incorrect username or password.'

        if error is None:
            session.clear()
            hash_session = username + \
                hashlib.sha256(password.encode("utf8")).hexdigest()
            hash_session = hashlib.sha256(
                hash_session.encode("utf8")).hexdigest()
            session['user_id'] = hash_session
            return redirect(url_for('index.index'))

        flash(error)

    return render_template('web/login.html')


@bp.route('/logout')
def logout():
    # 登出
    session.clear()
    flash('成功登出 Successfully log out.')
    return redirect(url_for('index.index'))


def login_required(view):
    # 登录验证，写成了修饰器
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        x = session.get('user_id')

        hash_session = Config.USERNAME + \
            hashlib.sha256(Config.PASSWORD.encode("utf8")).hexdigest()
        hash_session = hashlib.sha256(hash_session.encode("utf8")).hexdigest()

        if x != hash_session:
            return redirect(url_for('login.login'))

        g.user = {'user_id': x, 'username': Config.USERNAME}
        return view(**kwargs)

    return wrapped_view
