import json
from .config import Constant
from setting import Config
import time


def int2b(x):
    # int与布尔值转换
    if x is None or x == 0:
        return False
    else:
        return True


def calc_stamina(max_stamina_ts, curr_stamina):
    # 计算体力，返回剩余体力数值

    stamina = int(Constant.MAX_STAMINA - (max_stamina_ts -
                                          int(time.time()*1000)) / Constant.STAMINA_RECOVER_TICK)

    if stamina >= Constant.MAX_STAMINA:
        if curr_stamina >= Constant.MAX_STAMINA:
            stamina = curr_stamina
        else:
            stamina = Constant.MAX_STAMINA
    if stamina < 0:
        stamina = 0

    return stamina


def get_world_info(map_id):
    # 读取json文件内容，返回字典
    world_info = {}
    with open('./database/map/'+map_id+'.json', 'r') as f:
        world_info = json.load(f)

    return world_info


def get_available_maps():
    # 获取当前可用图（用户设定的），返回字典列表
    re = []
    for i in Config.AVAILABLE_MAP:
        info = get_world_info(i)
        del info['steps']
        try:
            del info['is_locked']
            del info['curr_position']
            del info['curr_capture']
        except:
            pass
        re.append(info)

    return re

