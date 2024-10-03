import logging
from time import time
from random import randint

from .config import Config


def b(value, length=1):
    return value.to_bytes(length=length, byteorder='little')


def bi(value):
    return int.from_bytes(value, byteorder='little')


class Score:
    def __init__(self) -> None:
        self.difficulty = 0xff

        self.score = 0
        self.cleartype = 0
        self.timer = 0

        self.best_score_flag = 0  # personal best
        self.best_player_flag = 0  # high score

        # 5.10 新增
        self.shiny_perfect_count = 0  # 2 bytes
        self.perfect_count = 0  # 2 bytes
        self.near_count = 0  # 2 bytes
        self.miss_count = 0  # 2 bytes
        self.early_count = 0  # 2 bytes
        self.late_count = 0  # 2 bytes

        self.healthy = 0  # 4 bytes signed? 不确定，但似乎没影响

    def copy(self, x: 'Score'):
        self.difficulty = x.difficulty
        self.score = x.score
        self.cleartype = x.cleartype
        self.timer = x.timer
        self.best_score_flag = x.best_score_flag
        self.best_player_flag = x.best_player_flag
        self.shiny_perfect_count = x.shiny_perfect_count
        self.perfect_count = x.perfect_count
        self.near_count = x.near_count
        self.miss_count = x.miss_count
        self.early_count = x.early_count
        self.late_count = x.late_count
        self.healthy = x.healthy

    def clear(self):
        self.difficulty = 0xff
        self.score = 0
        self.cleartype = 0
        self.timer = 0
        self.best_score_flag = 0
        self.best_player_flag = 0
        self.shiny_perfect_count = 0
        self.perfect_count = 0
        self.near_count = 0
        self.miss_count = 0
        self.early_count = 0
        self.late_count = 0
        self.healthy = 0

    def __str__(self):
        return f'Score: {self.score}, Cleartype: {self.cleartype}, Difficulty: {self.difficulty}, Timer: {self.timer}, Best Score Flag: {self.best_score_flag}, Best Player Flag: {self.best_player_flag}, Shiny Perfect: {self.shiny_perfect_count}, Perfect: {self.perfect_count}, Near: {self.near_count}, Miss: {self.miss_count}, Early: {self.early_count}, Late: {self.late_count}, Healthy: {self.healthy}'


class Player:
    def __init__(self, player_index: int = 0) -> None:
        self.player_id = 0
        self.player_name = b'\x45\x6d\x70\x74\x79\x50\x6c\x61\x79\x65\x72\x00\x00\x00\x00\x00'
        self.token = 0

        self.character_id = 0xff
        self.is_uncapped = 0

        self.score = Score()
        self.last_score = Score()

        self.finish_flag = 0

        self.player_state = 1
        self.download_percent = 0
        self.online = 0

        self.last_timestamp = 0
        self.extra_command_queue = []

        self.song_unlock: bytes = b'\x00' * Config.LINK_PLAY_UNLOCK_LENGTH

        self.start_command_num = 0

        # 5.10 新增

        self.voting: int = 0x8000  # 2 bytes, song_idx, 0xffff 为不选择，0x8000 为默认值
        self.player_index: int = player_index  # 1 byte 不确定对不对
        self.switch_2: int = 0  # 1 byte

        self.rating_ptt: int = 0  # 2 bytes
        self.is_hide_rating: int = 0  # 1 byte
        self.is_staff: int = 0  # 1 byte

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
            'rating_ptt': self.rating_ptt,
            'is_hide_rating': self.is_hide_rating == 1,
            'last_song': {
                'difficulty': self.last_score.difficulty,
                'score': self.last_score.score,
                'cleartype': self.last_score.cleartype,
                'shine_perfect': self.last_score.shiny_perfect_count,
                'perfect': self.last_score.perfect_count,
                'near': self.last_score.near_count,
                'miss': self.last_score.miss_count,
                'early': self.last_score.early_count,
                'late': self.last_score.late_count,
            },
            'song': {
                'difficulty': self.score.difficulty,
                'score': self.score.score,
                'cleartype': self.score.cleartype,
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

    @property
    def info(self) -> bytes:
        re = bytearray()
        re.extend(b(self.player_id, 8))
        re.append(self.character_id)
        re.append(self.is_uncapped)
        re.append(self.score.difficulty)
        re.extend(b(self.score.score, 4))
        re.extend(b(self.score.timer, 4))
        re.append(self.score.cleartype)
        re.append(self.player_state)
        re.append(self.download_percent)
        re.append(self.online)

        re.extend(b(self.voting, 2))
        re.append(self.player_index)
        re.append(self.switch_2)
        re.extend(b(self.rating_ptt, 2))
        re.append(self.is_hide_rating)
        re.append(self.is_staff)

        return bytes(re)

    @property
    def last_score_info(self) -> bytes:
        if self.player_id == 0:
            return b'\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        x = self.last_score
        re = bytearray()
        re.append(self.character_id)
        re.append(x.difficulty)
        re.extend(b(x.score, 4))
        re.append(x.cleartype)
        re.append(x.best_score_flag)
        re.append(x.best_player_flag)
        re.extend(b(x.shiny_perfect_count, 2))
        re.extend(b(x.perfect_count, 2))
        re.extend(b(x.near_count, 2))
        re.extend(b(x.miss_count, 2))
        re.extend(b(x.early_count, 2))
        re.extend(b(x.late_count, 2))
        re.extend(b(x.healthy, 4))

        return bytes(re)


class Room:

    def __init__(self) -> None:
        self.room_id = 0
        self.room_code = 'AAAA00'
        self.share_token = 'abcde12345'  # 5.10 新增

        self.countdown = 0xffffffff
        self.timestamp = 0
        self._state = 0
        self.song_idx = 0xffff  # 疑似 idx * 5
        self.last_song_idx = 0xffff  # 疑似 idx * 5

        self.song_unlock = b'\xFF' * Config.LINK_PLAY_UNLOCK_LENGTH

        self.host_id = 0
        self.players = [Player(0), Player(1), Player(2), Player(3)]

        self.interval = 1000
        self.times = 100  # ???

        self.round_mode: int = 1  # 5.10 从 bool 修改为 int 1~3
        self.is_public = 0  # 5.10 新增
        self.timed_mode = 0  # 5.10 新增

        self.selected_voter_player_id: int = 0  # 5.10 新增

        self.command_queue = []

        self.next_state_timestamp = 0  # 计时模式下一个状态时间

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, value: int):
        self._state = value
        self.countdown = 0xffffffff

    def to_dict(self) -> dict:
        p = [i.to_dict() for i in self.players if i.player_id != 0]
        for i in p:
            i['is_host'] = i['multiplay_player_id'] == self.host_id
        return {
            'room_id': self.room_id,
            'room_code': self.room_code,
            'share_token': self.share_token,
            'state': self.state,
            'song_idx': self.song_idx,
            'last_song_idx': self.last_song_idx if not self.is_playing else 0xffff,
            'host_id': self.host_id,
            'players': p,
            'round_mode': self.round_mode,
            'last_timestamp': self.timestamp,
            'is_enterable': self.is_enterable,
            'is_matchable': self.is_matchable,
            'is_playing': self.is_playing,
            'is_public': self.is_public == 1,
            'timed_mode': self.timed_mode == 1,
        }

    @property
    def room_info(self) -> bytes:
        re = bytearray()
        re.extend(b(self.host_id, 8))
        re.append(self.state)
        re.extend(b(self.countdown, 4))
        re.extend(b(self.timestamp, 8))
        re.extend(b(self.song_idx, 2))
        re.extend(b(self.interval, 2))
        re.extend(b(self.times, 7))
        re.extend(self.get_player_last_score())
        re.extend(b(self.last_song_idx, 2))
        re.append(self.round_mode)
        re.append(self.is_public)
        re.append(self.timed_mode)
        re.extend(b(self.selected_voter_player_id, 8))
        return bytes(re)

    @property
    def is_enterable(self) -> bool:
        return 0 < self.player_num < 4 and self.state == 2

    @property
    def is_matchable(self) -> bool:
        return self.is_public and 0 < self.player_num < 4 and self.state == 1

    @property
    def is_playing(self) -> bool:
        return self.state in (4, 5, 6, 7)

    @property
    def command_queue_length(self) -> int:
        return len(self.command_queue)

    @property
    def player_num(self) -> int:
        now = round(time() * 1000000)
        if now - self.timestamp >= 1000000:
            self.check_player_online(now)
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
        re = bytearray()
        for i in self.players:
            re.extend(i.info)
            re.append(0)
            re.extend(i.player_name)
        return bytes(re)

    def get_player_last_score(self):
        # 获取上次曲目玩家分数，返回bytes
        if self.last_song_idx == 0xffff:
            return b'\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' * 4
        return b''.join(i.last_score_info for i in self.players)

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
        self.players[player_index] = Player(player_index)
        self.update_song_unlock()

        if self.state in (2, 3):
            self.state = 1
            self.song_idx = 0xffff
            self.voting_clear()

        if self.state in (1, 2) and self.timed_mode and self.player_num <= 1:
            self.next_state_timestamp = 0
            self.countdown = 0xffffffff

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
        if self.state != 7:
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
            if player.player_id == 0:
                continue
            player.finish_flag = 0
            player.last_score.copy(player.score)
            player.last_score.best_player_flag = 0

            if player.last_score.score > max_score:
                max_score = player.last_score.score
                max_score_i = [i]
            elif player.last_score.score == max_score:
                max_score_i.append(i)

        for i in max_score_i:
            self.players[i].last_score.best_player_flag = 1

        self.voting_clear()
        for i in self.players:
            i.score.clear()

        logging.info(
            f'Room `{self.room_code}` finishes song `{self.song_idx}`')
        for i in self.players:
            if i.player_id != 0:
                logging.info(f'- Player `{i.name}` - {i.last_score}')

    @property
    def is_all_player_voted(self) -> bool:
        # 是否所有玩家都投票
        if self.state != 2:
            return False

        for i in self.players:
            if i.player_id != 0 and i.voting == 0x8000:
                return False

        return True

    def random_song(self):
        random_list = []
        for i in range(Config.LINK_PLAY_UNLOCK_LENGTH):
            for j in range(8):
                if self.song_unlock[i] & (1 << j):
                    random_list.append(i * 8 + j)

        if not random_list:
            self.song_idx = 0
        else:
            self.song_idx = random_list[randint(0, len(random_list) - 1)]

    def make_voting(self):
        # 投票
        self.state = 3
        self.selected_voter_player_id = 0

        random_list = []
        random_list_player_id = []
        for i in self.players:
            if i.player_id == 0 or i.voting == 0xffff or i.voting == 0x8000:
                continue
            random_list.append(i.voting)
            random_list_player_id.append(i.player_id)

        if random_list:
            idx = randint(0, len(random_list) - 1)
            self.song_idx = random_list[idx] * 5
            self.selected_voter_player_id = random_list_player_id[idx]
        else:
            self.random_song()

        logging.info(
            f'Room `{self.room_code}` votes song `{self.song_idx}`')

    def voting_clear(self):
        # 清除投票
        self.selected_voter_player_id = 0
        for i in self.players:
            i.voting = 0x8000

    @property
    def should_next_state(self) -> bool:
        if not self.timed_mode and self.state not in (4, 5, 6):
            self.countdown = 0xffffffff
            return False
        now = round(time() * 1000000)
        if self.countdown == 0xffffffff:
            # 还没开始计时
            if self.is_public and self.state == 1:
                self.next_state_timestamp = now + Config.COUNTDOWN_MATCHING
            elif self.state == 2:
                self.next_state_timestamp = now + Config.COUNTDOWN_SELECT_SONG
            elif self.state == 3:
                self.next_state_timestamp = now + Config.COUNTDOWN_SELECT_DIFFICULTY
            elif self.state == 4:
                self.next_state_timestamp = now + Config.COUNTDOWN_SONG_READY
            elif self.state == 5 or self.state == 6:
                self.next_state_timestamp = now + Config.COUNTDOWN_SONG_START
            elif self.state == 8:
                self.next_state_timestamp = now + Config.COUNTDOWN_RESULT
            else:
                return False

        # 不是哥们，616 你脑子怎么长的，上个版本是毫秒时间戳，新版本变成了微秒？？？那你这倒计时怎么还是毫秒啊！！！
        self.countdown = (self.next_state_timestamp - now) // 1000
        if self.countdown <= 0:
            self.countdown = 0
            return True
        return False
