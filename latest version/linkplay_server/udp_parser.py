import logging
import time

from .udp_class import Room, bi
from .config import Config
from .udp_sender import CommandSender


class CommandParser:
    route = [None, 'command_01', 'command_02', 'command_03', 'command_04', 'command_05',
             'command_06', 'command_07', 'command_08', 'command_09', 'command_0a', 'command_0b']

    def __init__(self, room: Room, player_index: int = 0) -> None:
        self.room = room
        self.player_index = player_index
        self.s = CommandSender(self.room)
        self.command: bytes = None

    def get_commands(self, command: bytes):
        self.command = command
        r = getattr(self, self.route[self.command[2]])()

        re = []

        flag_13 = False
        for i in range(max(bi(self.command[12:16]), self.room.players[self.player_index].start_command_num), self.room.command_queue_length):
            if self.room.command_queue[i][2] == 0x13:
                if flag_13:
                    break
                flag_13 = True
            re.append(self.room.command_queue[i])

        if self.room.players[self.player_index].extra_command_queue:
            re += self.room.players[self.player_index].extra_command_queue
            self.room.players[self.player_index].extra_command_queue = []

        if r:
            re += r

        return re

    def command_01(self):
        # 给房主
        player_id = bi(self.command[24:32])
        for i in self.room.players:
            if i.player_id == player_id and i.online == 1:
                self.room.host_id = player_id
                logging.info(
                    f'Player `{i.name}` becomes the host of room `{self.room.room_code}`')

        self.s.random_code = self.command[16:24]
        self.room.command_queue.append(self.s.command_10())

    def command_02(self):
        self.s.random_code = self.command[16:24]
        song_idx = bi(self.command[24:26])

        flag = 2
        if self.room.state == 2:
            flag = 0
            self.room.state = 3
            self.room.song_idx = song_idx
            self.room.command_queue.append(self.s.command_11())
            self.room.command_queue.append(self.s.command_13())

        return [self.s.command_0d(flag)]

    def command_03(self):
        # 尝试进入结算
        self.s.random_code = self.command[16:24]
        player = self.room.players[self.player_index]
        player.score = bi(self.command[24:28])
        player.cleartype = self.command[28]
        player.difficulty = self.command[29]
        player.best_score_flag = self.command[30]
        player.finish_flag = 1
        player.last_timestamp -= Config.COMMAND_INTERVAL
        self.room.last_song_idx = self.room.song_idx

        self.room.command_queue.append(self.s.command_12(self.player_index))

        if self.room.is_finish():
            self.room.make_finish()
            self.room.command_queue.append(self.s.command_13())

    def command_04(self):
        # 踢人
        self.s.random_code = self.command[16:24]
        player_id = bi(self.command[24:32])
        flag = 2
        if self.room.players[self.player_index].player_id == self.room.host_id and player_id != self.room.host_id:
            for i in range(4):
                if self.room.players[i].player_id == player_id:
                    flag = 1
                    self.room.delete_player(i)
                    self.room.command_queue.append(self.s.command_12(i))
                    self.room.update_song_unlock()
                    self.room.command_queue.append(self.s.command_14())
                    break

        return [self.s.command_0d(flag)]

    def command_05(self):
        pass

    def command_06(self):
        self.s.random_code = self.command[16:24]
        self.room.state = 1
        self.room.song_idx = 0xffff

        self.room.command_queue.append(self.s.command_13())

    def command_07(self):
        self.s.random_code = self.command[16:24]
        self.room.players[self.player_index].song_unlock = self.command[24:536]
        self.room.update_song_unlock()

        self.room.command_queue.append(self.s.command_14())

    def command_08(self):
        self.room.round_switch = bi(self.command[24:25])
        self.s.random_code = self.command[16:24]
        self.room.command_queue.append(self.s.command_13())

    def command_09(self):
        re = []
        self.s.random_code = self.command[16:24]
        player = self.room.players[self.player_index]

        if bi(self.command[12:16]) == 0:
            player.online = 1
            self.room.state = 1
            self.room.update_song_unlock()
            player.start_command_num = self.room.command_queue_length
            self.room.command_queue.append(self.s.command_15())
        else:
            if self.s.timestamp - player.last_timestamp >= Config.COMMAND_INTERVAL:
                re.append(self.s.command_0c())
                player.last_timestamp = self.s.timestamp

            # 离线判断
            flag_13, player_index_list = self.room.check_player_online(
                self.s.timestamp)
            for i in player_index_list:
                self.room.command_queue.append(self.s.command_12(i))

            flag_11 = False
            flag_12 = False

            if player.online == 0:
                flag_12 = True
                player.online = 1

            if self.room.is_ready(1, 1):
                flag_13 = True
                self.room.state = 2

            if player.player_state != self.command[32]:
                flag_12 = True
                player.player_state = self.command[32]

            if player.difficulty != self.command[33] and player.player_state != 5 and player.player_state != 6 and player.player_state != 7 and player.player_state != 8:
                flag_12 = True
                player.difficulty = self.command[33]

            if player.cleartype != self.command[34] and player.player_state != 7 and player.player_state != 8:
                flag_12 = True
                player.cleartype = self.command[34]

            if player.download_percent != self.command[35]:
                flag_12 = True
                player.download_percent = self.command[35]

            if player.character_id != self.command[36]:
                flag_12 = True
                player.character_id = self.command[36]

            if player.is_uncapped != self.command[37]:
                flag_12 = True
                player.is_uncapped = self.command[37]

            if self.room.state == 3 and player.score != bi(self.command[24:28]):
                flag_12 = True
                player.score = bi(self.command[24:28])

            if self.room.is_ready(3, 4):
                flag_13 = True
                self.room.countdown = Config.COUNTDOWM_TIME
                self.room.timestamp = round(time.time() * 1000)
                self.room.state = 4
                if self.room.round_switch == 1:
                    # 将换房主时间提前到此刻
                    self.room.make_round()

                logging.info(f'Room `{self.room.room_code}` starts playing')

            if self.room.state in (4, 5, 6):
                timestamp = round(time.time() * 1000)
                self.room.countdown -= timestamp - self.room.timestamp
                self.room.timestamp = timestamp
                if self.room.state == 4 and self.room.countdown <= 0:
                    # 此处不清楚
                    self.room.state = 5
                    self.room.countdown = 5999
                    flag_11 = True
                    flag_13 = True

                if self.room.state == 5 and self.room.is_ready(5, 6):
                    self.room.state = 6
                    flag_13 = True

                if self.room.state == 5 and self.room.is_ready(5, 7):
                    self.room.state = 7
                    self.room.countdown = 0xffffffff
                    flag_13 = True

                if self.room.state == 5 and self.room.countdown <= 0:
                    print('我怎么知道这是啥')

                if self.room.state == 6 and self.room.countdown <= 0:
                    # 此处不清楚
                    self.room.state = 7
                    self.room.countdown = 0xffffffff
                    flag_13 = True

                self.room.countdown = self.room.countdown if self.room.countdown > 0 else 0

            if self.room.state in (7, 8):
                if player.timer < bi(self.command[28:32]) or bi(self.command[28:32]) == 0 and player.timer != 0:
                    player.last_timer = player.timer
                    player.last_score = player.score
                    player.timer = bi(self.command[28:32])
                    player.score = bi(self.command[24:28])

                if player.timer != 0 or self.room.state != 8:
                    for i in self.room.players:
                        i.extra_command_queue.append(
                            self.s.command_0e(self.player_index))

                if self.room.is_ready(8, 1):
                    flag_13 = True
                    self.room.state = 1
                    self.room.song_idx = 0xffff

                    for i in self.room.players:
                        i.timer = 0
                        i.score = 0

                if self.room.is_finish():
                    # 有人退房导致的结算
                    self.room.make_finish()
                    flag_13 = True

            if flag_11:
                self.room.command_queue.append(self.s.command_11())
            if flag_12:
                self.room.command_queue.append(
                    self.s.command_12(self.player_index))
            if flag_13:
                self.room.command_queue.append(self.s.command_13())

        return re

    def command_0a(self):
        # 退出房间
        self.room.delete_player(self.player_index)

        self.room.command_queue.append(self.s.command_12(self.player_index))

        if self.room.state in (2, 3):
            self.room.state = 1
            self.room.song_idx = 0xffff
        # self.room.command_queue.append(self.s.command_11())
        self.room.command_queue.append(self.s.command_13())
        self.room.command_queue.append(self.s.command_14())

    def command_0b(self):
        # 推荐歌曲
        song_idx = bi(self.command[16:18])
        for i in range(4):
            if self.player_index != i and self.room.players[i].online == 1:
                self.room.players[i].extra_command_queue.append(
                    self.s.command_0f(self.player_index, song_idx))
