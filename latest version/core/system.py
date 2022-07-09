from time import time

from .constant import Constant


class GameInfo:
    def __init__(self):
        pass

    def to_dict(self) -> dict:
        return {
            "max_stamina": Constant.MAX_STAMINA,
            "stamina_recover_tick": Constant.STAMINA_RECOVER_TICK,
            "core_exp": Constant.CORE_EXP,
            "curr_ts": int(time()*1000),
            "level_steps": [{'level': i, 'level_exp': Constant.LEVEL_STEPS[i]} for i in Constant.LEVEL_STEPS],
            "world_ranking_enabled": True,
            "is_byd_chapter_unlocked": True
        }
