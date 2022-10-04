import time
from .udp_class import Room, b


class CommandSender:
    def __init__(self, room: Room = Room()) -> None:
        self.room = room
        self.timestamp = round(time.time() * 1000000)

        self.random_code = b'\x11\x11\x11\x11\x00\x00\x00\x00'

    def command_0c(self):
        return b'\x06\x16\x0c\x09' + b(self.room.room_id, 8) + b(self.room.command_queue_length, 4) + self.random_code + b(self.room.state) + b(self.room.countdown, 4) + b(self.timestamp, 8) + b'\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b'

    def command_0d(self, code: int):
        return b'\x06\x16\x0d\x09' + b(self.room.room_id, 8) + b(self.room.command_queue_length, 4) + self.random_code + b(code) + b'\x07\x07\x07\x07\x07\x07\x07'

    def command_0e(self, player_index: int):
        # 分数广播
        player = self.room.players[player_index]
        return b'\x06\x16\x0e\x09' + b(self.room.room_id, 8) + b(self.room.command_queue_length, 4) + b(player.player_id, 8) + b(player.character_id) + b(player.is_uncapped) + b(player.difficulty) + b(player.score, 4) + b(player.timer, 4) + b(player.cleartype) + b(player.player_state) + b(player.download_percent) + b'\x01' + b(player.last_score, 4) + b(player.last_timer, 4) + b(player.online)

    def command_0f(self, player_index: int, song_idx: int):
        # 歌曲推荐
        player = self.room.players[player_index]
        return b'\x06\x16\x0f\x09' + b(self.room.room_id, 8) + b(self.room.command_queue_length, 4) + b(player.player_id, 8) + b(song_idx, 2) + b'\x06\x06\x06\x06\x06\x06'

    def command_10(self):
        # 房主宣告
        return b'\x06\x16\x10\x09' + b(self.room.room_id, 8) + b(self.room.command_queue_length, 4) + self.random_code + b(self.room.host_id, 8)

    def command_11(self):
        return b'\x06\x16\x11\x09' + b(self.room.room_id, 8) + b(self.room.command_queue_length, 4) + self.random_code + self.room.get_players_info() + b'\x08\x08\x08\x08\x08\x08\x08\x08'

    def command_12(self, player_index: int):
        player = self.room.players[player_index]
        return b'\x06\x16\x12\x09' + b(self.room.room_id, 8) + b(self.room.command_queue_length, 4) + self.random_code + b(player_index) + b(player.player_id, 8) + b(player.character_id) + b(player.is_uncapped) + b(player.difficulty) + b(player.score, 4) + b(player.timer, 4) + b(player.cleartype) + b(player.player_state) + b(player.download_percent) + b(player.online)

    def command_13(self):
        return b'\x06\x16\x13\x09' + b(self.room.room_id, 8) + b(self.room.command_queue_length, 4) + self.random_code + b(self.room.host_id, 8) + b(self.room.state) + b(self.room.countdown, 4) + b(self.timestamp, 8) + b(self.room.song_idx, 2) + b(self.room.interval, 2) + b(self.room.times, 7) + self.room.get_player_last_score() + b(self.room.last_song_idx, 2) + b(self.room.round_switch, 1) + b'\x01'

    def command_14(self):
        return b'\x06\x16\x14\x09' + b(self.room.room_id, 8) + b(self.room.command_queue_length, 4) + self.random_code + self.room.song_unlock + b'\x08\x08\x08\x08\x08\x08\x08\x08'

    def command_15(self):
        return b'\x06\x16\x15\x09' + b(self.room.room_id, 8) + b(self.room.command_queue_length, 4) + self.room.get_players_info() + self.room.song_unlock + b(self.room.host_id, 8) + b(self.room.state) + b(self.room.countdown, 4) + b(self.timestamp, 8) + b(self.room.song_idx, 2) + b(self.room.interval, 2) + b(self.room.times, 7) + self.room.get_player_last_score() + b(self.room.last_song_idx, 2) + b(self.room.round_switch, 1) + b'\x09\x09\x09\x09\x09\x09\x09\x09\x09'
