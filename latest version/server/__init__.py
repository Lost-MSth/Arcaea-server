from flask import Blueprint
from setting import Config
from . import user
from . import auth

bp = Blueprint('server', __name__, url_prefix=Config.GAME_API_PREFIX)
bp.register_blueprint(user.bp)
bp.register_blueprint(auth.bp)