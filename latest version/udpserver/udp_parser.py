from operator import irshift
from .udp_sender import CommandSender
from .udp_class import bi, Room
from .udp_config import Config
import time


class CommandParser:
    def __init__(self, room: Room, player_index: int = 0) -> None:
        self.room = room
        self.player_index = player_index

    def get_commands(self, command):
        self.command = command
        l = {b'\x06\x16\x01': self.command_01,
             b'\x06\x16\x02': self.command_02,
             b'\x06\x16\x03': self.command_03,
             b'\x06\x16\x04': self.command_04,
             b'\x06\x16\x05': self.command_05,
             b'\x06\x16\x06': self.command_06,
             b'\x06\x16\x07': self.command_07,
             b'\x06\x16\x08': self.command_08,
             b'\x06\x16\x09': self.command_09,
             b'\x06\x16\x0a': self.command_0a,
             b'\x06\x16\x0b': self.command_0b
             }
        r = l[command[:3]]()

        re = []

        flag_13 = False
        for i in range(max(bi(self.command[12:16]), self.room.players[self.player_index].start_command_num), self.room.command_queue_length):
            if self.room.command_queue[i][:3] == b'\x06\x16\x13':
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

        x = CommandSender(self.room)
        x.random_code = self.command[16:24]
        self.room.command_queue_length += 1
        self.room.command_queue.append(x.command_10())

        return None

    def command_02(self):
        x = CommandSender(self.room)
        x.random_code = self.command[16:24]
        song_idx = bi(self.command[24:26])

        flag = 2
        if self.room.state == 2:
            flag = 0
            self.room.state = 3
            self.room.song_idx = song_idx
            self.room.command_queue_length += 1
            self.room.command_queue.append(x.command_11())
            self.room.command_queue_length += 1
            self.room.command_queue.append(x.command_13())

        return [x.command_0d(flag)]

    def command_03(self):
        # 尝试进入结算
        x = CommandSender(self.room)
        x.random_code = self.command[16:24]
        player = self.room.players[self.player_index]
        player.score = bi(self.command[24:28])
        player.cleartype = self.command[28]
        player.difficulty = self.command[29]
        player.best_score_flag = self.command[30]
        player.finish_flag = 1
        player.last_timestamp -= Config.COMMAND_INTERVAL
        self.room.last_song_idx = self.room.song_idx

        self.room.command_queue_length += 1
        self.room.command_queue.append(x.command_12(self.player_index))

        if self.room.is_finish():
            self.room.make_finish()
            self.room.command_queue_length += 1
            self.room.command_queue.append(x.command_13())

        return None

    def command_04(self):
        # 踢人
        x = CommandSender(self.room)
        x.random_code = self.command[16:24]
        player_id = bi(self.command[24:32])
        flag = 2
        if self.room.players[self.player_index].player_id == self.room.host_id and player_id != self.room.host_id:
            for i in range(4):
                if self.room.players[i].player_id == player_id:
                    flag = 1
                    self.room.delete_player(i)
                    self.room.command_queue_length += 1
                    self.room.command_queue.append(x.command_12(i))
                    self.room.update_song_unlock()
                    self.room.command_queue_length += 1
                    self.room.command_queue.append(x.command_14())
                    break

        return [x.command_0d(flag)]

    def command_05(self):
        pass

    def command_06(self):
        x = CommandSender(self.room)
        x.random_code = self.command[16:24]
        self.room.state = 1
        self.room.song_idx = 0xffff

        self.room.command_queue_length += 1
        self.room.command_queue.append(x.command_13())
        return None

    def command_07(self):
        x = CommandSender(self.room)
        x.random_code = self.command[16:24]
        self.room.players[self.player_index].song_unlock = self.command[24:536]
        self.room.update_song_unlock()

        self.room.command_queue_length += 1
        self.room.command_queue.append(x.command_14())
        return None

    def command_08(self):
        self.room.round_switch = bi(self.command[24:25])
        x = CommandSender(self.room)
        x.random_code = self.command[16:24]
        self.room.command_queue_length += 1
        self.room.command_queue.append(x.command_13())

        return None

    def command_09(self):
        re = []
        x = CommandSender(self.room)
        x.random_code = self.command[16:24]
        player = self.room.players[self.player_index]

        if bi(self.command[12:16]) == 0:
            player.online = 1
            self.room.state = 1
            self.room.update_song_unlock()
            player.start_command_num = self.room.command_queue_length
            self.room.command_queue_length += 1
            self.room.command_queue.append(x.command_15())
        else:
            if x.timestamp - player.last_timestamp >= Config.COMMAND_INTERVAL:
                re.append(x.command_0c())
                player.last_timestamp = x.timestamp

            # 离线判断
            for i in range(4):
                if i != self.player_index:
                    t = self.room.players[i]
                    if t.player_id != 0:
                        if t.last_timestamp != 0:
                            if t.online == 1 and x.timestamp - t.last_timestamp >= 5000000:
                                t.online = 0
                                self.room.command_queue_length += 1
                                self.room.command_queue.append(x.command_12(i))
                            elif t.online == 0 and x.timestamp - t.last_timestamp >= Config.PLAYER_TIMEOUT:
                                self.room.delete_player(i)
                                self.room.command_queue_length += 1
                                self.room.command_queue.append(x.command_12(i))

            flag_11 = False
            flag_12 = False
            flag_13 = False

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

            if self.room.state == 4 or self.room.state == 5 or self.room.state == 6:
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

                if self.room.countdown <= 0:
                    self.room.countdown = 0

            if self.room.state == 7 or self.room.state == 8:
                if player.timer < bi(self.command[28:32]) or bi(self.command[28:32]) == 0 and player.timer != 0:
                    player.last_timer = player.timer
                    player.last_score = player.score
                    player.timer = bi(self.command[28:32])
                    player.score = bi(self.command[24:28])

                if player.timer != 0 or self.room.state != 8:
                    for i in self.room.players:
                        i.extra_command_queue.append(
                            x.command_0e(self.player_index))

                if self.room.is_ready(8, 1):
                    flag_13 = True
                    self.room.state = 1
                    self.room.song_idx = 0xffff
                    if self.room.round_switch == 1:
                        self.room.make_round()

                    for i in self.room.players:
                        i.timer = 0
                        i.score = 0

                if self.room.is_finish():
                    # 有人退房导致的结算
                    self.room.make_finish()
                    flag_13 = True

            if flag_11:
                self.room.command_queue_length += 1
                self.room.command_queue.append(x.command_11())
            if flag_12:
                self.room.command_queue_length += 1
                self.room.command_queue.append(x.command_12(self.player_index))
            if flag_13:
                self.room.command_queue_length += 1
                self.room.command_queue.append(x.command_13())

        return re

    def command_0a(self):
        # 退出房间
        self.room.delete_player(self.player_index)

        x = CommandSender(self.room)
        self.room.command_queue_length += 1
        self.room.command_queue.append(x.command_12(self.player_index))

        if self.room.state == 3:
            self.room.state = 1
            self.room.song_idx = 0xffff
        # self.room.command_queue_length += 1
        # self.room.command_queue.append(x.command_11())
        self.room.command_queue_length += 1
        self.room.command_queue.append(x.command_13())
        self.room.command_queue_length += 1
        self.room.command_queue.append(x.command_14())
        return None

    def command_0b(self):
        # 推荐歌曲
        song_idx = bi(self.command[16:18])
        x = CommandSender(self.room)
        for i in range(4):
            if self.player_index != i and self.room.players[i].online == 1:
                self.room.players[i].extra_command_queue.append(
                    x.command_0f(self.player_index, song_idx))

        return None
