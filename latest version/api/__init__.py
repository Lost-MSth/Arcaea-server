from flask import Blueprint

from . import (
    characters,
    items,
    multiplay,
    presents,
    purchases,
    redeems,
    songs,
    system,
    token,
    users,
)

bp = Blueprint('api', __name__, url_prefix='/api/v1')
l = [users, songs, token, system, items, purchases,
     presents, redeems, characters, multiplay]
for i in l:
    bp.register_blueprint(i.bp)
