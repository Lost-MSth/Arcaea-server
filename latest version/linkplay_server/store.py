import logging
from base64 import b64decode, b64encode
from os import urandom
from random import randint
from threading import RLock
from time import time

from .config import Config
from .udp_class import Player, Room, bi


class Store:
    # token: {'key': key, 'room': Room, 'player_index': player_index, 'player_id': player_id}
    link_play_data = {}
    room_id_dict = {}  # 'room_id': Room
    room_code_dict = {}  # 'room_code': Room
    player_dict = {}  # 'player_id' : Player

    lock = RLock()


def random_room_code():
    re = ''
    for _ in range(4):
        re += chr(randint(65, 90))
    for _ in range(2):
        re += str(randint(0, 9))
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
    del Store.player_dict[Store.link_play_data[token]['player_id']]
    del Store.link_play_data[token]


def clear_room(room):
    # 清除房间信息
    room_id = room.room_id
    room_code = room.room_code
    del Store.room_id_dict[room_id]
    del Store.room_code_dict[room_code]
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
        '0': 'debug',
        '1': 'create_room',
        '2': 'join_room',
        '3': 'update_room',
    }

    def __init__(self, data: list):
        self.data = data  # data: list[str] = [command, ...]

    def debug(self):
        if Config.DEBUG:
            return eval(self.data[1])
        return 'ok'

    @staticmethod
    def clean_check():
        now = round(time() * 1000)
        if now - TCPRouter.clean_timer >= Config.TIME_LIMIT:
            logging.info('Start cleaning memory...')
            TCPRouter.clean_timer = now
            memory_clean(now)

    def handle(self) -> str:
        self.clean_check()
        if self.data[0] not in self.router:
            return None
        r = getattr(self, self.router[self.data[0]])()
        if isinstance(r, tuple):
            return '|'.join(map(str, r))
        return str(r)

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
        room.timestamp = round(time() * 1000)
        Store.room_id_dict[room_id] = room

        room_code = unique_random(
            Store.room_code_dict, random_func=random_room_code)
        room.room_code = room_code
        Store.room_code_dict[room_code] = room

        return room

    def create_room(self) -> tuple:
        # 开房
        # data = ['1', name, song_unlock, ]
        # song_unlock: base64 str
        name = self.data[1]
        song_unlock = b64decode(self.data[2])

        key = urandom(16)
        with Store.lock:
            room = self.generate_room()
            player = self.generate_player(name)

            player.song_unlock = song_unlock
            room.song_unlock = song_unlock
            room.host_id = player.player_id
            room.players[0] = player

            token = room.room_id
            player.token = token

            Store.link_play_data[token] = {
                'key': key,
                'room': room,
                'player_index': 0,
                'player_id': player.player_id
            }

        logging.info(f'TCP-Create room `{room.room_code}` by player `{name}`')
        return (0, room.room_code, room.room_id, token, b64encode(key).decode('utf-8'), player.player_id)

    def join_room(self) -> tuple:
        # 入房
        # data = ['2', name, song_unlock, room_code]
        # song_unlock: base64 str
        room_code = self.data[3].upper()
        key = urandom(16)
        name = self.data[1]
        song_unlock = b64decode(self.data[2])

        with Store.lock:
            if room_code not in Store.room_code_dict:
                # 房间号错误 / 房间不存在
                return '1202'
            room: Room = Store.room_code_dict[room_code]

            player_num = room.player_num
            if player_num == 4:
                # 满人
                return '1201'
            if player_num == 0:
                # 房间不存在
                return '1202'
            if room.state != 2:
                # 无法加入
                return '1205'

            token = unique_random(Store.link_play_data)

            player = self.generate_player(name)
            player.token = token
            player.song_unlock = song_unlock
            room.update_song_unlock()
            for i in range(4):
                if room.players[i].player_id == 0:
                    room.players[i] = player
                    player_index = i
                    break
            Store.link_play_data[token] = {
                'key': key,
                'room': room,
                'player_index': player_index,
                'player_id': player.player_id
            }

        logging.info(f'TCP-Player `{name}` joins room `{room_code}`')
        return (0, room_code, room.room_id, token, b64encode(key).decode('utf-8'), player.player_id, b64encode(room.song_unlock).decode('utf-8'))

    def update_room(self) -> tuple:
        # 房间信息更新
        # data = ['3', token]
        token = int(self.data[1])
        with Store.lock:
            if token not in Store.link_play_data:
                return '108'
            r = Store.link_play_data[token]
            room = r['room']
            logging.info(f'TCP-Room `{room.room_code}` info update')
            return (0, room.room_code, room.room_id, b64encode(r['key']).decode('utf-8'), room.players[r['player_index']].player_id, b64encode(room.song_unlock).decode('utf-8'))
