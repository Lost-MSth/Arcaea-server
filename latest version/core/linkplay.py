import socket
from base64 import b64decode, b64encode
from json import dumps, loads

from core.error import ArcError, Timeout

from .constant import Constant
from .user import UserInfo
from .util import aes_gcm_128_decrypt, aes_gcm_128_encrypt

socket.setdefaulttimeout(Constant.LINKPLAY_TIMEOUT)


def get_song_unlock(client_song_map: dict) -> bytes:
    '''处理可用歌曲bit，返回bytes'''

    user_song_unlock = [0] * Constant.LINKPLAY_UNLOCK_LENGTH
    for i in range(0, Constant.LINKPLAY_UNLOCK_LENGTH*2, 2):
        x = 0
        y = 0
        if str(i) in client_song_map:
            if client_song_map[str(i)][0]:
                x += 1
            if client_song_map[str(i)][1]:
                x += 2
            if client_song_map[str(i)][2]:
                x += 4
            if client_song_map[str(i)][3]:
                x += 8
        if str(i+1) in client_song_map:
            if client_song_map[str(i+1)][0]:
                y += 1
            if client_song_map[str(i+1)][1]:
                y += 2
            if client_song_map[str(i+1)][2]:
                y += 4
            if client_song_map[str(i+1)][3]:
                y += 8

        user_song_unlock[i // 2] = y*16 + x

    return bytes(user_song_unlock)


class Player(UserInfo):
    def __init__(self, c=None, user_id=None) -> None:
        super().__init__(c, user_id)
        self.player_id: int = 0
        self.token: int = 0
        self.key: bytes = None

        self.__song_unlock: bytes = None
        self.client_song_map: dict = None

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


class Room:
    def __init__(self) -> None:
        self.room_id: int = 0
        self.room_code: str = 'AAAA00'

        self.song_unlock: bytes = None

    def to_dict(self) -> dict:
        return {
            'roomId': str(self.room_id),
            'roomCode': self.room_code,
            'orderedAllowedSongs': (b64encode(self.song_unlock)).decode()
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
                tag = sock.recv(12)
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
            'utf-8') + len(ciphertext).to_bytes(8, byteorder='little') + iv + tag[:12] + ciphertext
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
        user.select_user_one_column('name')
        self.data_swap({
            'endpoint': 'create_room',
            'data': {
                'name': self.user.name,
                'song_unlock': b64encode(self.user.song_unlock).decode('utf-8')
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

        self.user.select_user_one_column('name')
        self.data_swap({
            'endpoint': 'join_room',
            'data': {
                'name': self.user.name,
                'song_unlock': b64encode(self.user.song_unlock).decode('utf-8'),
                'room_code': self.room.room_code
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
        self.data_swap({
            'endpoint': 'update_room',
            'data': {
                'token': self.user.token
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
