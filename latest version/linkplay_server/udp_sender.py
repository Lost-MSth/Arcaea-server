from time import time

from .udp_class import Room, b


class CommandSender:

    PROTOCOL_NAME = b'\x06\x16'
    PROTOCOL_VERSION = b'\x09'

    def __init__(self, room: Room = None) -> None:
        self.room = room
        self.timestamp = round(time() * 1000000)

        self.random_code = b'\x11\x11\x11\x11\x00\x00\x00\x00'

    @staticmethod
    def command_encode(t: tuple):
        r = b''.join(t)
        x = 16 - len(r) % 16
        return r + b(x) * x

    def command_prefix(self, command: bytes):
        length = self.room.command_queue_length
        if command >= b'\x10':
            length += 1

        return (self.PROTOCOL_NAME, command, self.PROTOCOL_VERSION, b(self.room.room_id, 8), b(length, 4))

    def command_0c(self):
        return self.command_encode((*self.command_prefix(b'\x0c'), self.random_code, b(self.room.state), b(self.room.countdown, 4), b(self.timestamp, 8)))

    def command_0d(self, code: int):
        return self.command_encode((*self.command_prefix(b'\x0d'), self.random_code, b(code)))

    def command_0e(self, player_index: int):
        # 分数广播
        player = self.room.players[player_index]
        return self.command_encode((*self.command_prefix(b'\x0e'), b(player.player_id, 8), b(player.character_id), b(player.is_uncapped), b(player.difficulty), b(player.score, 4), b(player.timer, 4), b(player.cleartype), b(player.player_state), b(player.download_percent), b'\x01', b(player.last_score, 4), b(player.last_timer, 4), b(player.online)))

    def command_0f(self, player_index: int, song_idx: int):
        # 歌曲推荐
        player = self.room.players[player_index]
        return self.command_encode((*self.command_prefix(b'\x0f'), b(player.player_id, 8), b(song_idx, 2)))

    def command_10(self):
        # 房主宣告
        return self.command_encode((*self.command_prefix(b'\x10'), self.random_code, b(self.room.host_id, 8)))

    def command_11(self):
        return self.command_encode((*self.command_prefix(b'\x11'), self.random_code, self.room.get_players_info()))

    def command_12(self, player_index: int):
        player = self.room.players[player_index]
        return self.command_encode((*self.command_prefix(b'\x12'), self.random_code, b(player_index), b(player.player_id, 8), b(player.character_id), b(player.is_uncapped), b(player.difficulty), b(player.score, 4), b(player.timer, 4), b(player.cleartype), b(player.player_state), b(player.download_percent), b(player.online)))

    def command_13(self):
        return self.command_encode((*self.command_prefix(b'\x13'), self.random_code, b(self.room.host_id, 8), b(self.room.state), b(self.room.countdown, 4), b(self.timestamp, 8), b(self.room.song_idx, 2), b(self.room.interval, 2), b(self.room.times, 7), self.room.get_player_last_score(), b(self.room.last_song_idx, 2), b(self.room.round_switch, 1)))

    def command_14(self):
        return self.command_encode((*self.command_prefix(b'\x14'), self.random_code, self.room.song_unlock))

    def command_15(self):
        return self.command_encode((*self.command_prefix(b'\x15'), self.room.get_players_info(), self.room.song_unlock, b(self.room.host_id, 8), b(self.room.state), b(self.room.countdown, 4), b(self.timestamp, 8), b(self.room.song_idx, 2), b(self.room.interval, 2), b(self.room.times, 7), self.room.get_player_last_score(), b(self.room.last_song_idx, 2), b(self.room.round_switch, 1)))
