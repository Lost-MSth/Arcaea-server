import logging

from .config import Config
from .udp_class import Room, bi
from .udp_sender import CommandSender


class CommandParser:

    route = {
        0x01: 'command_01',
        0x02: 'command_02',
        0x03: 'command_03',
        0x04: 'command_04',
        0x06: 'command_06',
        0x07: 'command_07',
        0x08: 'command_08',
        0x09: 'command_09',
        0x0a: 'command_0a',
        0x0b: 'command_0b',
        0x20: 'command_20',
        0x22: 'command_22',
        0x23: 'command_23',
    }

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
            re += self.room.players[self.player_index].extra_command_queue[-12:]
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
        # 房主选歌
        if self.room.round_mode == 3:
            logging.warning('Error: round_mode == 3 in command 02')
            return None
        self.s.random_code = self.command[16:24]
        song_idx = bi(self.command[24:26])

        flag = 5
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
        player.score.score = bi(self.command[24:28])
        player.score.cleartype = self.command[28]
        player.score.difficulty = self.command[29]
        player.score.best_score_flag = self.command[30]
        player.score.shiny_perfect_count = bi(self.command[31:33])
        player.score.perfect_count = bi(self.command[33:35])
        player.score.near_count = bi(self.command[35:37])
        player.score.miss_count = bi(self.command[37:39])
        player.score.early_count = bi(self.command[39:41])
        player.score.late_count = bi(self.command[41:43])
        player.score.healthy = bi(self.command[43:47])
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
                    self.room.command_queue.append(self.s.command_14())
                    break

        return [self.s.command_0d(flag)]

    def command_06(self):
        self.s.random_code = self.command[16:24]
        self.room.state = 1
        self.room.song_idx = 0xffff
        self.room.voting_clear()

        self.room.command_queue.append(self.s.command_13())

    def command_07(self):
        self.s.random_code = self.command[16:24]
        self.room.players[self.player_index].song_unlock = self.command[24:536]
        self.room.update_song_unlock()

        self.room.command_queue.append(self.s.command_14())

        # 07 可能需要一个 0d 响应，code = 0x0b

    def command_08(self):
        # 可能弃用
        logging.warning('Command 08 is outdated')
        pass
        # self.room.round_mode = bi(self.command[24:25])
        # self.s.random_code = self.command[16:24]
        # self.room.command_queue.append(self.s.command_13())

    def command_09(self):
        self.s.random_code = self.command[16:24]
        player = self.room.players[self.player_index]

        if bi(self.command[12:16]) == 0:
            player.online = 1
            self.room.state = 1
            self.room.update_song_unlock()
            player.start_command_num = self.room.command_queue_length
            self.room.command_queue.append(self.s.command_15())
            return None

        flag_0c = False

        if self.s.timestamp - player.last_timestamp >= Config.COMMAND_INTERVAL:
            flag_0c = True
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

        if self.room.state in (1, 2) and player.player_state == 8:
            # 还在结算给踢了
            # 冗余，为了保险
            self.room.delete_player(self.player_index)
            self.room.command_queue.append(
                self.s.command_12(self.player_index))
            self.room.command_queue.append(self.s.command_14())

        if self.room.is_ready(1, 1) and ((self.room.player_num > 1 and not self.room.is_public) or (self.room.is_public and self.room.player_num == 4)):
            flag_13 = True
            self.room.state = 2

        if self.room.state == 1 and self.room.is_public and self.room.player_num > 1 and self.room.should_next_state:
            flag_0c = True
            flag_13 = True
            self.room.state = 2

        if self.room.state in (2, 3) and self.room.player_num < 2:
            flag_13 = True
            self.room.state = 1

        if self.room.state == 2 and self.room.should_next_state:
            flag_0c = True
            self.room.state = 3
            flag_13 = True
            if self.room.round_mode == 3:
                self.room.make_voting()
            else:
                self.room.random_song()

        if player.player_state != self.command[32]:
            flag_12 = True
            player.player_state = self.command[32]

        if player.score.difficulty != self.command[33] and player.player_state not in (5, 6, 7, 8):
            flag_12 = True
            player.score.difficulty = self.command[33]

        if player.score.cleartype != self.command[34] and player.player_state != 7 and player.player_state != 8:
            flag_12 = True
            player.score.cleartype = self.command[34]

        if player.download_percent != self.command[35]:
            flag_12 = True
            player.download_percent = self.command[35]

        if player.character_id != self.command[36]:
            flag_12 = True
            player.character_id = self.command[36]

        if player.is_uncapped != self.command[37]:
            flag_12 = True
            player.is_uncapped = self.command[37]

        if self.room.state == 3 and player.score.score != bi(self.command[24:28]):
            flag_12 = True
            player.score.score = bi(self.command[24:28])

        if self.room.is_ready(3, 4) or (self.room.state == 3 and self.room.should_next_state):
            flag_13 = True
            flag_0c = True
            self.room.state = 4

            if self.room.round_mode == 2:
                # 将换房主时间提前到此刻
                self.room.make_round()
            logging.info(f'Room `{self.room.room_code}` starts playing')

        if self.room.state == 4:
            if player.download_percent != 0xff:
                # 有人没下载完把他踢了！
                self.room.delete_player(self.player_index)
                self.room.command_queue.append(
                    self.s.command_12(self.player_index))
                self.room.command_queue.append(self.s.command_14())

            if self.room.should_next_state:
                self.room.state = 5
                flag_11 = True
                flag_13 = True

        if self.room.state == 5:
            flag_13 = True
            if self.room.is_ready(5, 6):
                self.room.state = 6
            if self.room.is_ready(5, 7):
                self.room.state = 7

        if self.room.state in (5, 6) and self.room.should_next_state:
            # 此处不清楚
            self.room.state = 7
            flag_13 = True

        if self.room.state in (7, 8):
            player_now_timer = bi(self.command[28:32])
            if player.score.timer < player_now_timer or player_now_timer == 0 and player.score.timer != 0:
                player.last_score.timer = player.score.timer
                player.last_score.score = player.score.score
                player.score.timer = player_now_timer
                player.score.score = bi(self.command[24:28])

            if player.score.timer != 0 or self.room.state != 8:
                for i in self.room.players:
                    i.extra_command_queue.append(
                        self.s.command_0e(self.player_index))

            if self.room.is_ready(8, 1):
                flag_13 = True
                self.room.state = 1
                self.room.song_idx = 0xffff

            if self.room.state == 8 and self.room.should_next_state:
                flag_0c = True
                flag_13 = True
                self.room.state = 1
                self.room.song_idx = 0xffff

            if self.room.state in (1, 2) and player.player_state == 8:
                # 还在结算给踢了
                self.room.delete_player(self.player_index)
                self.room.command_queue.append(
                    self.s.command_12(self.player_index))
                self.room.command_queue.append(self.s.command_14())

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

        if flag_0c:
            return [self.s.command_0c()]

    def command_0a(self):
        # 退出房间
        self.room.delete_player(self.player_index)

        self.room.command_queue.append(self.s.command_12(self.player_index))

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

    def command_20(self):
        # 表情
        sticker_id = bi(self.command[16:18])
        for i in range(4):
            if self.player_index != i and self.room.players[i].online == 1:
                self.room.players[i].extra_command_queue.append(
                    self.s.command_21(self.player_index, sticker_id))

    def command_22(self):
        # 房间设置，懒得判断房主
        self.s.random_code = self.command[16:24]
        self.room.is_public = self.command[25]
        if self.room.is_public == 0:
            self.room.round_mode = self.command[24]
            self.room.timed_mode = self.command[26]
        else:
            self.room.round_mode = 3
            self.room.timed_mode = 1
            self.room.state = 1
        self.room.command_queue.append(self.s.command_11())
        self.room.command_queue.append(self.s.command_13())
        return [self.s.command_0d(1)]

    def command_23(self):
        # 歌曲投票
        self.s.random_code = self.command[16:24]
        if self.room.player_num < 2:
            return [self.s.command_0d(6)]
        if self.room.state != 2:
            return [self.s.command_0d(5)]
        player = self.room.players[self.player_index]
        player.voting = bi(self.command[24:26])
        logging.info(
            f'Player `{player.name}` votes for song `{player.voting}`')
        self.room.command_queue.append(self.s.command_12(self.player_index))

        if self.room.is_all_player_voted:
            self.room.make_voting()
            self.room.command_queue.append(self.s.command_13())

        return [self.s.command_0d(1)]
