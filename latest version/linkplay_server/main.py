import base64
import logging
import random
import socketserver
import threading
import time
from os import urandom

# import binascii
from .aes import decrypt, encrypt
from .config import Config
from .udp_class import Player, Room, bi
from .udp_parser import CommandParser

# token: {'key': key, 'room': Room, 'player_index': player_index, 'player_id': player_id}
link_play_data = {}
room_id_dict = {}  # 'room_id': Room
room_code_dict = {}  # 'room_code': Room
player_dict = {}  # 'player_id' : Player
clean_timer = 0
lock = threading.RLock()

logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                    level=logging.INFO)


def random_room_code():
    # 随机生成房间号
    re = ''
    for _ in range(4):
        re += chr(random.randint(65, 90))
    for _ in range(2):
        re += str(random.randint(0, 9))

    return re


def unique_random(dataset, length=8, random_func=None):
    '''无重复随机，且默认非0'''
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
    del player_dict[link_play_data[token]['player_id']]
    del link_play_data[token]


def clear_room(room):
    # 清除房间信息
    room_id = room.room_id
    room_code = room.room_code
    del room_id_dict[room_id]
    del room_code_dict[room_code]
    del room


def memory_clean(now):
    # 内存清理
    lock.acquire()

    clean_room_list = []
    clean_player_list = []
    for token in link_play_data:
        room = link_play_data[token]['room']
        if now - room.timestamp >= Config.TIME_LIMIT:
            clean_room_list.append(room.room_id)

        if now - room.players[link_play_data[token]['player_index']].last_timestamp // 1000 >= Config.TIME_LIMIT:
            clean_player_list.append(token)

    for room_id in room_id_dict:
        if now - room_id_dict[room_id].timestamp >= Config.TIME_LIMIT:
            clean_room_list.append(room_id)

    for room_id in clean_room_list:
        if room_id in room_id_dict:
            clear_room(room_id_dict[room_id])

    for token in clean_player_list:
        clear_player(token)

    lock.release()


class UDP_handler(socketserver.BaseRequestHandler):
    def handle(self):
        client_msg, server = self.request
        try:
            token = client_msg[:8]
            iv = client_msg[8:20]
            tag = client_msg[20:32]
            ciphertext = client_msg[32:]
            if int.from_bytes(token, byteorder='little') in link_play_data:
                user = link_play_data[bi(token)]
            else:
                return None

            plaintext = decrypt(user['key'], b'', iv, ciphertext, tag)
        except Exception as e:
            logging.error(e)
            return None
        # print(binascii.b2a_hex(plaintext))

        commands = CommandParser(
            user['room'], user['player_index']).get_commands(plaintext)

        if user['room'].players[user['player_index']].player_id == 0:
            clear_player(bi(token))
            temp = []
            for i in commands:
                if i[:3] == b'\x06\x16\x12':
                    temp.append(i)
            commands = temp
            # 处理不能正确被踢的问题

        for i in commands:
            iv, ciphertext, tag = encrypt(user['key'], i, b'')
            # print(binascii.b2a_hex(i))

            server.sendto(token + iv + tag[:12] +
                          ciphertext, self.client_address)


class TCP_handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.data = self.rfile.readline().strip()

        message = self.data.decode('utf-8')
        # print(message)
        data = message.split('|')
        if data[0] != Config.AUTHENTICATION:
            self.wfile.write(b'No authentication')
            logging.warning('TCP-%s-No authentication' %
                            self.client_address[0])
            return None

        global clean_timer
        now = round(time.time() * 1000)
        if now - clean_timer >= Config.TIME_LIMIT:
            logging.info('Start cleaning memory...')
            clean_timer = now
            memory_clean(now)

        self.wfile.write(data_swap(data[1:]).encode('utf-8'))


def data_swap(data: list) -> str:
    # data: list[str] = [command, ...]
    if data[0] == '1':
        # 开房
        # data = ['1', name, song_unlock, ]
        # song_unlock: base64 str
        name = data[1]
        song_unlock = base64.b64decode(data[2])

        key = urandom(16)
        room_id = unique_random(room_id_dict)

        room = Room()
        room.room_id = room_id
        room_id_dict[room_id] = room

        player_id = unique_random(player_dict, 3)
        player = Player()
        player.player_id = player_id
        player.set_player_name(name)
        player_dict[player_id] = player

        player.song_unlock = song_unlock
        room.song_unlock = song_unlock
        room.host_id = player_id
        room.players[0] = player
        room.player_num = 1

        room_code = unique_random(room_code_dict, random_func=random_room_code)
        room.room_code = room_code
        room_code_dict[room_code] = room

        token = room_id
        player.token = token

        link_play_data[token] = {'key': key,
                                 'room': room,
                                 'player_index': 0,
                                 'player_id': player_id}

        logging.info('TCP-Create room `%s` by player `%s`' % (room_code, name))
        return '|'.join([str(x) for x in (0, room_code, room_id, token, base64.b64encode(key).decode('utf-8'), player_id)])

    elif data[0] == '2':
        # 入房
        # data = ['2', name, song_unlock, room_code]
        # song_unlock: base64 str
        room_code = data[3].upper()

        if room_code not in room_code_dict:
            # 房间号错误
            return '1202'

        room = room_code_dict[room_code]
        if room.player_num == 4:
            # 满人
            return '1201'
        elif room.state != 2:
            # 无法加入
            return '1205'

        name = data[1]
        song_unlock = base64.b64decode(data[2])

        key = urandom(16)
        token = unique_random(link_play_data)
        player_id = unique_random(player_dict, 3)

        player = Player()
        player.player_id = player_id
        player.set_player_name(name)
        player.token = token
        player_dict[player_id] = player
        player.song_unlock = song_unlock
        room.update_song_unlock()
        for i in range(4):
            if room.players[i].player_id == 0:
                room.players[i] = player
                player_index = i
                break
        link_play_data[token] = {'key': key,
                                 'room': room,
                                 'player_index': player_index,
                                 'player_id': player_id}

        logging.info('TCP-Player `%s` joins room `%s`' % (name, room_code))
        return '|'.join([str(x) for x in (0, room_code, room.room_id, token, base64.b64encode(key).decode('utf-8'), player_id, base64.b64encode(room.song_unlock).decode('utf-8'))])

    elif data[0] == '3':
        # 房间信息更新
        # data = ['3', token]
        token = int(data[1])
        if token in link_play_data:
            r = link_play_data[token]
            logging.info('TCP-Room `%s` info update' % room_code)
            return '|'.join([str(x) for x in (0, r['room'].room_code, r['room'].room_id, base64.b64encode(r['key']).decode('utf-8'), r['room'].players[r['player_index']].player_id, base64.b64encode(r['room'].song_unlock).decode('utf-8'))])
        else:
            return '108'


def link_play(ip: str = Config.HOST, udp_port: int = Config.UDP_PORT, tcp_port: int = Config.TCP_PORT):
    udp_server = socketserver.ThreadingUDPServer((ip, udp_port), UDP_handler)
    tcp_server = socketserver.ThreadingTCPServer((ip, tcp_port), TCP_handler)

    threads = [threading.Thread(target=udp_server.serve_forever), threading.Thread(
        target=tcp_server.serve_forever)]
    [t.start() for t in threads]
    [t.join() for t in threads]
