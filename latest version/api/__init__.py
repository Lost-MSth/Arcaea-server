from flask import Blueprint

from . import users
from . import songs
from . import token

bp = Blueprint('api', __name__, url_prefix='/api/v1')
bp.register_blueprint(users.bp)
bp.register_blueprint(songs.bp)
bp.register_blueprint(token.bp)
