import logging
from base64 import b64decode, b64encode
from os import urandom
from random import randint
from threading import RLock
from time import time

from .config import Config
from .udp_class import Player, Room, bi
from .udp_sender import CommandSender


class Store:
    # token: {'key': key, 'room': Room, 'player_index': player_index, 'player_id': player_id}
    link_play_data = {}
    room_id_dict: "dict[int, Room]" = {}  # 'room_id': Room
    room_code_dict = {}  # 'room_code': Room
    player_dict = {}  # 'player_id' : Player

    share_token_dict = {}  # 'share_token': Room

    lock = RLock()


def random_room_code():
    re = ''
    for _ in range(4):
        re += chr(randint(65, 90))
    for _ in range(2):
        re += str(randint(0, 9))
    return re


def random_share_token():
    CHARSET = 'abcdefghijklmnopqrstuvwxyz0123456789'
    re = ''
    for _ in range(10):
        re += CHARSET[randint(0, 35)]
    return re


def unique_random(dataset, length=8, random_func=None):
    '''无重复随机，且默认非0，没处理可能的死循环'''
    if random_func is None:
        x = bi(urandom(length))
        while x in dataset or x == 0:
            x = bi(urandom(length))
    else:
        x = random_func()
        while x in dataset:
            x = random_func()
    return x


def clear_player(token):
    # 清除玩家信息和token
    player_id = Store.link_play_data[token]['player_id']
    logging.info(f'Clean player `{Store.player_dict[player_id].name}`')
    with Store.lock:
        if player_id in Store.player_dict:
            del Store.player_dict[player_id]
        if token in Store.link_play_data:
            del Store.link_play_data[token]


def clear_room(room):
    # 清除房间信息
    room_id = room.room_id
    room_code = room.room_code
    share_token = room.share_token
    logging.info(f'Clean room `{room_code}`')
    with Store.lock:
        if room_id in Store.room_id_dict:
            del Store.room_id_dict[room_id]
        if room_code in Store.room_code_dict:
            del Store.room_code_dict[room_code]
        if share_token in Store.share_token_dict:
            del Store.share_token_dict[share_token]
        del room


def memory_clean(now):
    # 内存清理，应对玩家不正常退出
    with Store.lock:
        clean_room_list = []
        clean_player_list = []
        for token, v in Store.link_play_data.items():
            room = v['room']
            if now - room.timestamp >= Config.TIME_LIMIT:
                clean_room_list.append(room.room_id)

            if now - room.players[v['player_index']].last_timestamp // 1000 >= Config.TIME_LIMIT:
                clean_player_list.append(token)

        for room_id, v in Store.room_id_dict.items():
            if now - v.timestamp >= Config.TIME_LIMIT:
                clean_room_list.append(room_id)

        for room_id in clean_room_list:
            if room_id in Store.room_id_dict:
                clear_room(Store.room_id_dict[room_id])

        for token in clean_player_list:
            clear_player(token)


class TCPRouter:
    clean_timer = 0
    router = {
        'debug',
        'create_room',
        'join_room',
        'update_room',
        'get_rooms',
        'select_room',
        'get_match_rooms'
    }

    def __init__(self, raw_data: 'dict | list'):
        self.raw_data = raw_data  # data: dict {endpoint: str, data: dict}
        self.data = raw_data['data']
        self.endpoint = raw_data['endpoint']

    def debug(self) -> dict:
        if Config.DEBUG:
            return {'result': eval(self.data['code'])}
        return {'hello_world': 'ok'}

    @staticmethod
    def clean_check():
        now = round(time() * 1000)
        if now - TCPRouter.clean_timer >= Config.TIME_LIMIT:
            logging.info('Start cleaning memory...')
            TCPRouter.clean_timer = now
            memory_clean(now)

    def handle(self) -> dict:
        self.clean_check()
        if self.endpoint not in self.router:
            return {'code': 999}
        try:
            r = getattr(self, self.endpoint)()
        except Exception as e:
            logging.error(e)
            return {'code': 999}
        if isinstance(r, int):
            return {'code': r}
        return {
            'code': 0,
            'data': r
        }

    @staticmethod
    def generate_player(name: str) -> Player:
        player_id = unique_random(Store.player_dict, 3)
        player = Player()
        player.player_id = player_id
        player.set_player_name(name)

        Store.player_dict[player_id] = player

        return player

    @staticmethod
    def generate_room() -> Room:
        room_id = unique_random(Store.room_id_dict)
        room = Room()
        room.room_id = room_id
        room.timestamp = round(time() * 1000000)
        Store.room_id_dict[room_id] = room

        room_code = unique_random(
            Store.room_code_dict, random_func=random_room_code)
        room.room_code = room_code
        Store.room_code_dict[room_code] = room

        share_token = unique_random(
            Store.share_token_dict, random_func=random_share_token)
        room.share_token = share_token
        Store.share_token_dict[share_token] = room

        return room

    def create_room(self) -> dict:
        # 开房
        # data = ['1', name, song_unlock, ]
        # song_unlock: base64 str
        name = self.data['name']
        song_unlock = b64decode(self.data['song_unlock'])
        rating_ptt = self.data.get('rating_ptt', 0)
        is_hide_rating = self.data.get('is_hide_rating', False)
        match_times = self.data.get('match_times', None)

        key = urandom(16)
        with Store.lock:
            room = self.generate_room()
            player = self.generate_player(name)

            player.song_unlock = song_unlock
            player.rating_ptt = rating_ptt
            player.is_hide_rating = is_hide_rating
            player.player_index = 0
            room.song_unlock = song_unlock
            room.host_id = player.player_id
            room.players[0] = player

            token = room.room_id
            player.token = token

            # 匹配模式追加
            if match_times is not None:
                room.is_public = 1
                room.round_mode = 3
                room.timed_mode = 1

            Store.link_play_data[token] = {
                'key': key,
                'room': room,
                'player_index': 0,
                'player_id': player.player_id
            }

        logging.info(f'TCP-Create room `{room.room_code}` by player `{name}`')
        return {
            'room_code': room.room_code,
            'room_id': room.room_id,
            'token': token,
            'key': b64encode(key).decode('utf-8'),
            'player_id': player.player_id
        }

    def join_room(self) -> 'dict | int':
        # 入房
        # data = ['2', name, song_unlock, room_code]
        # song_unlock: base64 str
        room_code = self.data['room_code'].upper()
        key = urandom(16)
        name = self.data['name']
        song_unlock = b64decode(self.data['song_unlock'])
        rating_ptt = self.data.get('rating_ptt', 0)
        is_hide_rating = self.data.get('is_hide_rating', False)
        match_times = self.data.get('match_times', None)

        with Store.lock:
            if room_code not in Store.room_code_dict:
                # 房间号错误 / 房间不存在
                return 1202
            room: Room = Store.room_code_dict[room_code]

            player_num = room.player_num
            if player_num == 4:
                # 满人
                return 1201
            if player_num == 0:
                # 房间不存在
                return 1202
            if room.state not in (0, 1, 2) or (room.is_public and match_times is None):
                # 无法加入
                return 1205

            token = unique_random(Store.link_play_data)

            player = self.generate_player(name)
            player.token = token
            player.song_unlock = song_unlock
            player.rating_ptt = rating_ptt
            player.is_hide_rating = is_hide_rating
            room.update_song_unlock()
            for i in range(4):
                if room.players[i].player_id == 0:
                    room.players[i] = player
                    player.player_index = i
                    break
            Store.link_play_data[token] = {
                'key': key,
                'room': room,
                'player_index': player.player_index,
                'player_id': player.player_id
            }

        logging.info(f'TCP-Player `{name}` joins room `{room_code}`')
        return {
            'room_code': room_code,
            'room_id': room.room_id,
            'token': token,
            'key': b64encode(key).decode('utf-8'),
            'player_id': player.player_id,
            'song_unlock': b64encode(room.song_unlock).decode('utf-8')
        }

    def update_room(self) -> dict:
        # 房间信息更新
        # data = ['3', token]
        token = int(self.data['token'])
        rating_ptt = self.data.get('rating_ptt', 0)
        is_hide_rating = self.data.get('is_hide_rating', False)

        with Store.lock:
            if token not in Store.link_play_data:
                return 108
            r = Store.link_play_data[token]
            room = r['room']

            # 更新玩家信息
            player_index = r['player_index']
            player = room.players[player_index]
            player.rating_ptt = rating_ptt
            player.is_hide_rating = is_hide_rating
            cs = CommandSender(room)
            room.command_queue.append(cs.command_12(player_index))

            logging.info(f'TCP-Room `{room.room_code}` info update')
            return {
                'room_code': room.room_code,
                'room_id': room.room_id,
                'key': b64encode(r['key']).decode('utf-8'),
                # changed from room.players[r['player_index']].player_id,
                'player_id': r['player_id'],
                'song_unlock': b64encode(room.song_unlock).decode('utf-8')
            }

    def get_rooms(self) -> dict:
        # 获取房间列表与详细信息

        offset = int(self.data.get('offset', 0))
        if offset < 0:
            offset = 0
        limit = min(int(self.data.get('limit', 100)), 100)
        if limit < 0:
            limit = 100

        n = 0
        m = 0
        rooms = []
        f = False
        f2 = False
        for room in Store.room_id_dict.values():
            if room.player_num == 0:
                continue
            if m < offset:
                m += 1
                continue
            if f:
                # 处理刚好有 limit 个房间的情况
                f2 = True
                break
            n += 1
            rooms.append(room.to_dict())
            if n >= limit:
                f = True

        return {
            'amount': n,
            'offset': offset,
            'limit': limit,
            'has_more': f2,
            'rooms': rooms
        }

    def select_room(self) -> dict:
        # 查询房间信息

        room_code = self.data.get('room_code', None)
        share_token = self.data.get('share_token', None)

        if room_code is not None:
            room = Store.room_code_dict.get(room_code, None)
        elif share_token is not None:
            room = Store.share_token_dict.get(share_token, None)
        if room is None:
            return 108

        return {
            'room_id': room.room_id,
            'room_code': room.room_code,
            'share_token': room.share_token,
            'is_enterable': room.is_enterable,
            'is_matchable': room.is_matchable,
            'is_playing': room.is_playing,
            'is_public': room.is_public == 1,
            'timed_mode': room.timed_mode == 1,
        }

    def get_match_rooms(self):
        n = 0
        rooms = []

        for room in Store.room_id_dict.values():
            if not room.is_matchable:
                continue

            rooms.append({
                'room_id': room.room_id,
                'room_code': room.room_code,
                'share_token': room.share_token,
                'is_matchable': room.is_matchable,
                'next_state_timestamp': room.next_state_timestamp,
                'song_unlock': b64encode(room.song_unlock).decode('utf-8'),
                'players': [{
                    'player_id': i.player_id,
                    'name': i.name,
                    'rating_ptt': i.rating_ptt
                } for i in room.players]
            })
            if n >= 100:
                break
        return {
            'amount': n,
            'rooms': rooms
        }
