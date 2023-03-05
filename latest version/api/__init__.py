from flask import Blueprint

from . import (users, songs, token, system, items,
               purchases, presents, redeems)

bp = Blueprint('api', __name__, url_prefix='/api/v1')
bp.register_blueprint(users.bp)
bp.register_blueprint(songs.bp)
bp.register_blueprint(token.bp)
bp.register_blueprint(system.bp)
bp.register_blueprint(items.bp)
bp.register_blueprint(purchases.bp)
bp.register_blueprint(presents.bp)
bp.register_blueprint(redeems.bp)
