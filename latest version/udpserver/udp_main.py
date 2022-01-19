import socketserver
import threading
import os
import random
import time
# import binascii
from . import aes
from .udp_parser import CommandParser
from .udp_class import Room, Player, bi
from .udp_config import Config


# token: {'key': key, 'room': Room, 'player_index': player_index, 'player_id': player_id}
link_play_data = {}
room_id_dict = {}  # 'room_id': Room
room_code_dict = {}  # 'room_code': Room
player_dict = {}  # 'player_id' : Player
clean_timer = 0


def random_room_code():
    # 随机生成房间号
    re = ''
    for _ in range(4):
        re += chr(random.randint(65, 90))
    for _ in range(2):
        re += str(random.randint(0, 9))

    return re


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


class UDPhandler(socketserver.BaseRequestHandler):
    def handle(self):
        client_msg, server = self.request
        token = client_msg[:8]
        iv = client_msg[8:20]
        tag = client_msg[20:32]
        ciphertext = client_msg[32:]
        if int.from_bytes(token, byteorder='little') in link_play_data:
            user = link_play_data[bi(token)]
        else:
            return None

        plaintext = aes.decrypt(user['key'], b'', iv, ciphertext, tag)
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
            iv, ciphertext, tag = aes.encrypt(user['key'], i, b'')
            # print(binascii.b2a_hex(i))

            server.sendto(token + iv + tag[:12] +
                          ciphertext, self.client_address)


def server_run(ip, port):
    server = socketserver.ThreadingUDPServer((ip, port), UDPhandler)
    server.serve_forever()


def data_swap(conn):
    clean_timer = 0
    while True:
        try:
            data = conn.recv()
        except EOFError:
            break

        now = round(time.time() * 1000)
        if now - clean_timer >= Config.TIME_LIMIT:
            clean_timer = now
            memory_clean(now)

        if data[0] == 1:
            # 开房
            key = os.urandom(16)
            room_id = bi(os.urandom(8))
            while room_id in room_id_dict and room_id == 0:
                room_id = bi(os.urandom(8))
            room = Room()
            room.room_id = room_id
            room_id_dict[room_id] = room

            player_id = bi(os.urandom(3))
            while player_id in player_dict and player_id == 0:
                player_id = bi(os.urandom(3))
            player = Player()
            player.player_id = player_id
            player.set_player_name(data[1])
            player_dict[player_id] = player

            player.song_unlock = data[2]
            room.song_unlock = data[2]
            room.host_id = player_id
            room.players[0] = player
            room.player_num = 1

            room_code = random_room_code()
            while room_code in room_code_dict:
                room_code = random_room_code()
            room.room_code = room_code
            room_code_dict[room_code] = room

            token = room_id
            player.token = token

            link_play_data[token] = {'key': key,
                                     'room': room,
                                     'player_index': 0,
                                     'player_id': player_id}

            conn.send((0, room_code, room_id, token, key, player_id))

        elif data[0] == 2:
            room_code = data[3].upper()
            if room_code not in room_code_dict:
                # 房间号错误
                conn.send((1202, ))
            else:
                room = room_code_dict[room_code]
                if room.player_num == 4:
                    # 满人
                    conn.send((1201, ))
                elif room.state != 2:
                    # 无法加入
                    conn.send((1205, ))
                else:
                    key = os.urandom(16)
                    token = bi(os.urandom(8))

                    player_id = bi(os.urandom(3))
                    while player_id in player_dict and player_id == 0:
                        player_id = bi(os.urandom(3))
                    player = Player()
                    player.player_id = player_id
                    player.set_player_name(data[1])
                    player.token = token
                    player_dict[player_id] = player

                    player.song_unlock = data[2]

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

                    conn.send((0, room_code, room.room_id,
                               token, key, player_id, room.song_unlock))
        elif data[0] == 3:
            token = data[1]
            if token in link_play_data:
                r = link_play_data[token]
                conn.send((0, r['room'].room_code, r['room'].room_id, r['key'],
                           r['room'].players[r['player_index']].player_id, r['room'].song_unlock))
            else:
                conn.send((108, ))


def link_play(conn, ip: str, port: int):
    try:
        server = threading.Thread(target=server_run, args=(ip, port))
        data_exchange = threading.Thread(target=data_swap, args=(conn,))
        server.start()
        data_exchange.start()
    except:
        pass
