from flask import Blueprint

from core.config_manager import Config

from . import (auth, course, friend, multiplayer, others, present, purchase,
               score, user, world)

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
bp.register_blueprint(course.bp)
