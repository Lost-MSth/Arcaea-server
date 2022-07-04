from flask import Blueprint
from setting import Config
from . import user
from . import auth
from . import friend
from . import score
from . import world
from . import purchase
from . import present
from . import others
from . import multiplayer

bp = Blueprint('server', __name__, url_prefix=Config.GAME_API_PREFIX)
bp.register_blueprint(user.bp)
bp.register_blueprint(auth.bp)
bp.register_blueprint(friend.bp)
bp.register_blueprint(score.bp)
bp.register_blueprint(world.bp)
bp.register_blueprint(purchase.bp)
bp.register_blueprint(present.bp)
bp.register_blueprint(others.bp)
bp.register_blueprint(multiplayer.bp)
