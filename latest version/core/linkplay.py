import socket
from base64 import b64decode, b64encode
from json import dumps, loads
from threading import RLock
from time import time

from core.error import ArcError, Timeout

from .constant import Constant
from .user import UserInfo
from .util import aes_gcm_128_decrypt, aes_gcm_128_encrypt

socket.setdefaulttimeout(Constant.LINKPLAY_TIMEOUT)


def get_song_unlock(client_song_map: 'dict[str, list]') -> bytes:
    '''处理可用歌曲bit，返回bytes'''

    user_song_unlock = [0] * Constant.LINKPLAY_UNLOCK_LENGTH

    for k, v in client_song_map.items():
        for i in range(5):
            if not v[i]:
                continue
            index = int(k) * 5 + i
            user_song_unlock[index // 8] |= 1 << (index % 8)

    return bytes(user_song_unlock)


class Player(UserInfo):
    def __init__(self, c=None, user_id=None) -> None:
        super().__init__(c, user_id)
        self.player_id: int = 0
        self.token: int = 0
        self.key: bytes = None

        self.__song_unlock: bytes = None
        self.client_song_map: dict = None

        self.last_match_timestamp: int = 0
        self.match_times: int = None  # 已匹配次数，减 1 后乘 5 就大致是匹配时间
        self.match_room: Room = None  # 匹配到的房间，这个仅用来在两个人同时匹配时使用，一人建房，通知另一个人加入

    def to_dict(self) -> dict:
        return {
            'userId': self.user_id,
            'playerId': str(self.player_id),
            'token': str(self.token),
            'key': (b64encode(self.key)).decode()
        }

    @property
    def song_unlock(self) -> bytes:
        if self.__song_unlock is None:
            self.get_song_unlock()
        return self.__song_unlock

    def get_song_unlock(self, client_song_map: dict = None) -> bytes:
        if client_song_map is not None:
            self.client_song_map = client_song_map
        self.__song_unlock = get_song_unlock(self.client_song_map)

    def calc_available_chart_num(self, song_unlock: bytes) -> int:
        '''计算交叠后可用谱面数量'''
        new_unlock = [i & j for i, j in zip(self.song_unlock, song_unlock)]
        s = 0
        for i in range(len(new_unlock)):
            for j in range(8):
                if new_unlock[i] & (1 << j):
                    s += 1
        return s


class Room:
    def __init__(self) -> None:
        self.room_id: int = 0
        self.room_code: str = 'AAAA00'

        self.song_unlock: bytes = None

        self.share_token: str = 'abcde12345'

    def to_dict(self) -> dict:
        return {
            'roomId': str(self.room_id),
            'roomCode': self.room_code,
            'orderedAllowedSongs': (b64encode(self.song_unlock)).decode(),
            'shareToken': self.share_token
        }


class RemoteMultiPlayer:
    TCP_AES_KEY = Constant.LINKPLAY_TCP_SECRET_KEY.encode(
        'utf-8').ljust(16, b'\x00')[:16]

    def __init__(self) -> None:
        self.user: 'Player' = None
        self.room: 'Room' = None

        self.data_recv: 'dict | list' = None

    def to_dict(self) -> dict:
        return dict(self.room.to_dict(), **self.user.to_dict())

    @staticmethod
    def tcp(data: bytes) -> bytes:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((Constant.LINKPLAY_HOST,
                          Constant.LINKPLAY_TCP_PORT))

            sock.sendall(data)
            try:
                cipher_len = int.from_bytes(sock.recv(8), byteorder='little')
                if cipher_len > Constant.LINKPLAY_TCP_MAX_LENGTH:
                    raise ArcError(
                        'Too long body from link play server', status=400)
                iv = sock.recv(12)
                tag = sock.recv(16)
                ciphertext = sock.recv(cipher_len)
                received = aes_gcm_128_decrypt(
                    RemoteMultiPlayer.TCP_AES_KEY, b'', iv, ciphertext, tag)
            except socket.timeout as e:
                raise Timeout(
                    'Timeout when waiting for data from link play server.', status=400) from e
            # print(received)
            return received

    def data_swap(self, data: dict) -> dict:

        iv, ciphertext, tag = aes_gcm_128_encrypt(
            self.TCP_AES_KEY, dumps(data).encode('utf-8'), b'')
        send_data = Constant.LINKPLAY_AUTHENTICATION.encode(
            'utf-8') + len(ciphertext).to_bytes(8, byteorder='little') + iv + tag + ciphertext
        recv_data = self.tcp(send_data)
        self.data_recv = loads(recv_data)

        code = self.data_recv['code']
        if code != 0:
            raise ArcError(f'Link Play error code: {code}', code, status=400)

        return self.data_recv

    def create_room(self, user: 'Player' = None) -> None:
        '''创建房间'''
        if user is not None:
            self.user = user
        user.select_user_about_link_play()
        self.data_swap({
            'endpoint': 'create_room',
            'data': {
                'name': self.user.name,
                'song_unlock': b64encode(self.user.song_unlock).decode('utf-8'),
                'rating_ptt': self.user.rating_ptt,
                'is_hide_rating': self.user.is_hide_rating,
                'match_times': self.user.match_times
            }
        })

        self.room = Room()
        x = self.data_recv['data']
        self.room.room_code = x['room_code']
        self.room.room_id = int(x['room_id'])
        self.room.song_unlock = self.user.song_unlock
        self.user.token = int(x['token'])
        self.user.key = b64decode(x['key'])
        self.user.player_id = int(x['player_id'])

    def join_room(self, room: 'Room' = None, user: 'Player' = None) -> None:
        '''加入房间'''
        if user is not None:
            self.user = user
        if room is not None:
            self.room = room

        self.user.select_user_about_link_play()
        self.data_swap({
            'endpoint': 'join_room',
            'data': {
                'name': self.user.name,
                'song_unlock': b64encode(self.user.song_unlock).decode('utf-8'),
                'room_code': self.room.room_code,
                'rating_ptt': self.user.rating_ptt,
                'is_hide_rating': self.user.is_hide_rating,
                'match_times': self.user.match_times
            }
        })
        x = self.data_recv['data']
        self.room.room_code = x['room_code']
        self.room.room_id = int(x['room_id'])
        self.room.song_unlock = b64decode(x['song_unlock'])
        self.user.token = int(x['token'])
        self.user.key = b64decode(x['key'])
        self.user.player_id = int(x['player_id'])

    def update_room(self, user: 'Player' = None) -> None:
        '''更新房间'''
        if user is not None:
            self.user = user

        self.user.select_user_about_link_play()
        self.data_swap({
            'endpoint': 'update_room',
            'data': {
                'token': self.user.token,
                'rating_ptt': self.user.rating_ptt,
                'is_hide_rating': self.user.is_hide_rating
            }
        })

        self.room = Room()
        x = self.data_recv['data']
        self.room.room_code = x['room_code']
        self.room.room_id = int(x['room_id'])
        self.room.song_unlock = b64decode(x['song_unlock'])
        self.user.key = b64decode(x['key'])
        self.user.player_id = int(x['player_id'])

    def get_rooms(self, offset=0, limit=50) -> dict:
        '''获取房间列表'''
        self.data_swap({
            'endpoint': 'get_rooms',
            'data': {
                'offset': offset,
                'limit': limit
            }
        })

        return self.data_recv['data']

    def select_room(self, room_code: str = None, share_token: str = None) -> dict:
        self.data_swap({
            'endpoint': 'select_room',
            'data': {
                'room_code': room_code,
                'share_token': share_token
            }
        })

        return self.data_recv['data']

    def get_match_rooms(self) -> dict:
        '''获取一定数量的公共房间列表'''
        self.data_swap({
            'endpoint': 'get_match_rooms',
            'data': {
                'limit': 100
            }
        })

        return self.data_recv['data']


class MatchStore:

    last_get_rooms_timestamp = 0
    room_cache: 'list[Room]' = []

    player_queue: 'dict[int, Player]' = {}

    lock = RLock()

    last_memory_clean_timestamp = 0

    def __init__(self, c=None) -> None:
        self.c = c
        self.remote = RemoteMultiPlayer()

    def refresh_rooms(self):
        now = time()
        if now - self.last_get_rooms_timestamp < Constant.LINKPLAY_MATCH_GET_ROOMS_INTERVAL:
            return
        MatchStore.room_cache = self.remote.get_match_rooms()['rooms']
        MatchStore.last_get_rooms_timestamp = now

    def init_player(self, user: 'Player'):
        user.match_times = 0
        MatchStore.player_queue[user.user_id] = user
        user.last_match_timestamp = time()
        user.c = self.c
        user.select_user_about_link_play()
        user.c = None

    def clear_player(self, user_id: int):
        MatchStore.player_queue.pop(user_id, None)

    def clean_room_cache(self):
        MatchStore.room_cache = []
        MatchStore.last_get_rooms_timestamp = 0

    def memory_clean(self):
        now = time()
        if now - self.last_memory_clean_timestamp < Constant.LINKPLAY_MEMORY_CLEAN_INTERVAL:
            return
        with self.lock:
            for i in MatchStore.player_queue:
                if now - i.last_match_timestamp > Constant.LINKPLAY_MATCH_TIMEOUT:
                    self.clear_player(i)

    def match(self, user_id: int):
        user = MatchStore.player_queue.get(user_id)
        if user is None:
            raise ArcError(
                f'User `{user_id}` not found in match queue.', code=999)

        if user.match_room is not None:
            # 二人开新房，第二人加入
            user.c = self.c
            self.remote.join_room(user.match_room, user)
            self.clear_player(user_id)
            return self.remote.to_dict()

        self.refresh_rooms()

        rule = min(user.match_times, len(Constant.LINKPLAY_MATCH_PTT_ABS) -
                   1, len(Constant.LINKPLAY_MATCH_UNLOCK_MIN) - 1)
        ptt_abs = Constant.LINKPLAY_MATCH_PTT_ABS[rule]
        unlock_min = Constant.LINKPLAY_MATCH_UNLOCK_MIN[rule]

        # 加入已有房间
        for i in MatchStore.room_cache:
            f = True
            num = 0
            for j in i['players']:
                if j['player_id'] != 0:
                    num += 1
                    if abs(user.rating_ptt - j['rating_ptt']) >= ptt_abs:
                        f = False
                        break

            # 有玩家非正常退房时，next_state_timestamp 不为 0，有概率新玩家进不来，所以使用 num 统计玩家数量

            if f and user.calc_available_chart_num(b64decode(i['song_unlock'])) >= unlock_min and ((time() + 2) * 1000000 < i['next_state_timestamp'] or i['next_state_timestamp'] <= 0 or num == 1):
                room = Room()
                room.room_code = i['room_code']
                user.c = self.c
                self.remote.join_room(room, user)
                self.clean_room_cache()
                self.clear_player(user_id)
                return self.remote.to_dict()

        now = time()

        # 二人开新房，第一人开房
        for p in MatchStore.player_queue.values():
            if p.user_id == user_id or now - p.last_match_timestamp > Constant.LINKPLAY_MATCH_TIMEOUT:
                continue
            new_rule = min(rule, p.match_times)
            if abs(user.rating_ptt - p.rating_ptt) < Constant.LINKPLAY_MATCH_PTT_ABS[new_rule] and user.calc_available_chart_num(p.song_unlock) >= Constant.LINKPLAY_MATCH_UNLOCK_MIN[new_rule]:
                user.c = self.c
                self.remote.create_room(user)
                self.clear_player(user_id)
                p.match_room = self.remote.room
                return self.remote.to_dict()

        user.match_times += 1
        user.last_match_timestamp = now

        return None
