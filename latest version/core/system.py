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
            "level_steps": [{'level': k, 'level_exp': v} for k, v in Constant.LEVEL_STEPS.items()],
            "world_ranking_enabled": True,
            "is_byd_chapter_unlocked": True
        }
