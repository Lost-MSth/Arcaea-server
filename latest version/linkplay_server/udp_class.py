import logging
from time import time

from .config import Config


def b(value, length=1):
    return value.to_bytes(length=length, byteorder='little')


def bi(value):
    return int.from_bytes(value, byteorder='little')


class Player:
    def __init__(self) -> None:
        self.player_id = 0
        self.player_name = b'\x45\x6d\x70\x74\x79\x50\x6c\x61\x79\x65\x72\x00\x00\x00\x00\x00'
        self.token = 0

        self.character_id = 0xff
        self.last_character_id = 0xff
        self.is_uncapped = 0

        self.difficulty = 0xff
        self.last_difficulty = 0xff
        self.score = 0
        self.last_score = 0
        self.timer = 0
        self.last_timer = 0
        self.cleartype = 0
        self.last_cleartype = 0
        self.best_score_flag = 0
        self.best_player_flag = 0
        self.finish_flag = 0

        self.player_state = 1
        self.download_percent = 0
        self.online = 0

        self.last_timestamp = 0
        self.extra_command_queue = []

        self.song_unlock: bytes = b'\x00' * Config.LINK_PLAY_UNLOCK_LENGTH

        self.start_command_num = 0

    @property
    def name(self) -> str:
        return self.player_name.decode('ascii').rstrip('\x00')

    def to_dict(self) -> dict:
        return {
            'multiplay_player_id': self.player_id,
            'name': self.name,
            'is_online': self.online == 1,
            'character_id': self.character_id,
            'is_uncapped': self.is_uncapped == 1,
            'last_song': {
                'difficulty': self.last_difficulty,
                'score': self.last_score,
                'cleartype': self.last_cleartype,
            },
            'song': {
                'difficulty': self.difficulty,
                'score': self.score,
                'cleartype': self.cleartype,
            },
            'player_state': self.player_state,
            'last_timestamp': self.last_timestamp,
        }

    def set_player_name(self, player_name: str):
        self.player_name = player_name.encode('ascii')
        if len(self.player_name) > 16:
            self.player_name = self.player_name[:16]
        else:
            self.player_name += b'\x00' * (16 - len(self.player_name))


class Room:
    def __init__(self) -> None:
        self.room_id = 0
        self.room_code = 'AAAA00'

        self.countdown = 0xffffffff
        self.timestamp = 0
        self.state = 0
        self.song_idx = 0xffff
        self.last_song_idx = 0xffff

        self.song_unlock = b'\xFF' * Config.LINK_PLAY_UNLOCK_LENGTH

        self.host_id = 0
        self.players = [Player(), Player(), Player(), Player()]

        self.interval = 1000
        self.times = 100

        self.round_switch = 0

        self.command_queue = []

    def to_dict(self) -> dict:
        p = [i.to_dict() for i in self.players if i.player_id != 0]
        for i in p:
            i['is_host'] = i['player_id'] == self.host_id
        return {
            'room_id': self.room_id,
            'room_code': self.room_code,
            'state': self.state,
            'song_idx': self.song_idx,
            'last_song_idx': self.last_song_idx if not self.is_playing else 0xffff,
            'host_id': self.host_id,
            'players': p,
            'round_switch': self.round_switch == 1,
            'last_timestamp': self.timestamp,
            'is_enterable': self.is_enterable,
            'is_playing': self.is_playing,
        }

    @property
    def is_enterable(self) -> bool:
        return 0 < self.player_num < 4 and self.state == 2

    @property
    def is_playing(self) -> bool:
        return self.state in (4, 5, 6, 7)

    @property
    def command_queue_length(self) -> int:
        return len(self.command_queue)

    @property
    def player_num(self) -> int:
        self.check_player_online()
        return sum(i.player_id != 0 for i in self.players)

    def check_player_online(self, now: int = None):
        # 检测玩家是否被自动踢出房间 / 离线判断
        now = round(time() * 1000000) if now is None else now
        flag = False
        player_index_list = []
        for i, x in enumerate(self.players):
            if x.player_id == 0 or x.last_timestamp == 0:
                continue
            if now - x.last_timestamp >= Config.PLAYER_TIMEOUT:
                self.delete_player(i)
                flag = True
                player_index_list.append(i)
            elif x.online == 1 and now - x.last_timestamp >= Config.PLAYER_PRE_TIMEOUT:
                x.online = 0
                player_index_list.append(i)

        return flag, player_index_list

    def get_players_info(self):
        # 获取所有玩家信息
        re = b''
        for i in self.players:
            re += b(i.player_id, 8) + b(i.character_id) + b(i.is_uncapped) + b(i.difficulty) + b(i.score, 4) + \
                b(i.timer, 4) + b(i.cleartype) + b(i.player_state) + \
                b(i.download_percent) + b(i.online) + b'\x00' + i.player_name
        return re

    def get_player_last_score(self):
        # 获取上次曲目玩家分数，返回bytes
        if self.last_song_idx == 0xffff:
            return b'\xff\xff\x00\x00\x00\x00\x00\x00\x00' * 4
        re = b''

        for i in range(4):
            player = self.players[i]

            if player.player_id != 0:
                re += b(player.last_character_id) + b(player.last_difficulty) + b(player.last_score, 4) + b(
                    player.last_cleartype) + b(player.best_score_flag) + b(player.best_player_flag)
            else:
                re += b'\xff\xff\x00\x00\x00\x00\x00\x00\x00'

        return re

    def make_round(self):
        # 轮换房主
        for i in range(4):
            if self.players[i].player_id == self.host_id:
                for j in range(1, 4):
                    player = self.players[(i + j) % 4]
                    if player.player_id != 0:
                        self.host_id = player.player_id
                        logging.info(
                            f'Player `{player.name}` becomes the host of room `{self.room_code}`')
                        break
                break

    def delete_player(self, player_index: int):
        # 删除某个玩家
        player = self.players[player_index]
        if player.player_id == self.host_id:
            self.make_round()

        logging.info(
            f'Player `{player.name}` leaves room `{self.room_code}`')

        self.players[player_index].online = 0
        self.players[player_index] = Player()
        self.update_song_unlock()

    def update_song_unlock(self):
        # 更新房间可用歌曲
        r = bi(b'\xff' * Config.LINK_PLAY_UNLOCK_LENGTH)
        for i in self.players:
            if i.player_id != 0:
                r &= bi(i.song_unlock)

        self.song_unlock = b(r, Config.LINK_PLAY_UNLOCK_LENGTH)

    def is_ready(self, old_state: int, player_state: int):
        # 是否全部准备就绪
        if self.state == old_state:
            for i in self.players:
                if i.player_id != 0 and (i.player_state != player_state or i.online == 0):
                    return False

            return True
        return False

    def is_finish(self):
        # 是否全部进入结算
        if self.state == 8:
            return False

        for i in self.players:
            if i.player_id != 0 and (i.finish_flag == 0 or i.online == 0):
                return False

        return True

    def make_finish(self):
        # 结算
        self.state = 8
        self.last_song_idx = self.song_idx

        max_score = 0
        max_score_i = []
        for i in range(4):
            player = self.players[i]
            if player.player_id != 0:
                player.finish_flag = 0
                player.last_timer = player.timer
                player.last_score = player.score
                player.last_cleartype = player.cleartype
                player.last_character_id = player.character_id
                player.last_difficulty = player.difficulty
                player.best_player_flag = 0

                if player.last_score > max_score:
                    max_score = player.last_score
                    max_score_i = [i]
                elif player.last_score == max_score:
                    max_score_i.append(i)

        for i in max_score_i:
            self.players[i].best_player_flag = 1

        logging.info(
            f'Room `{self.room_code}` finishes song `{self.song_idx}`')
        for i in self.players:
            if i.player_id != 0:
                logging.info(
                    f'- Player `{i.name}` - Score: {i.last_score}  Cleartype: {i.last_cleartype}  Difficulty: {i.last_difficulty}')
