from flask import Blueprint

from . import (users, songs, token, system, items,
               purchases, presents, redeems, characters, multiplay)

bp = Blueprint('api', __name__, url_prefix='/api/v1')
l = [users, songs, token, system, items, purchases,
     presents, redeems, characters, multiplay]
for i in l:
    bp.register_blueprint(i.bp)
