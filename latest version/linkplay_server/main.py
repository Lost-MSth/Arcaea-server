# import binascii
import logging
import socketserver
import threading

from .aes import decrypt, encrypt
from .config import Config
from .store import Store, TCPRouter, clear_player, clear_room
from .udp_class import bi
from .udp_parser import CommandParser

logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                    level=logging.INFO)


class UDP_handler(socketserver.BaseRequestHandler):
    def handle(self):
        client_msg, server = self.request
        # print(client_msg)
        try:
            token = client_msg[:8]
            iv = client_msg[8:20]
            tag = client_msg[20:32]
            ciphertext = client_msg[32:]
            if bi(token) not in Store.link_play_data:
                return None
            user = Store.link_play_data[bi(token)]

            plaintext = decrypt(user['key'], b'', iv, ciphertext, tag)
        except Exception as e:
            logging.error(e)
            return None

        # if Config.DEBUG:
        #     logging.info(
        #         f'UDP-From-{self.client_address[0]}-{binascii.b2a_hex(plaintext)}')

        commands = CommandParser(
            user['room'], user['player_index']).get_commands(plaintext)

        if user['room'].players[user['player_index']].player_id == 0:
            clear_player(bi(token))
            if user['room'].player_num == 0:
                clear_room(user['room'])
            commands = [i for i in commands if i[2] == 0x12]
            # 处理不能正确被踢的问题

        for i in commands:
            iv, ciphertext, tag = encrypt(user['key'], i, b'')
            # if Config.DEBUG:
            #     logging.info(
            #         f'UDP-To-{self.client_address[0]}-{binascii.b2a_hex(i)}')

            server.sendto(token + iv + tag[:12] +
                          ciphertext, self.client_address)


class TCP_handler(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            self.data = self.rfile.readline().strip()
            message = self.data.decode('utf-8')
        except Exception as e:
            logging.error(e)
            return None

        if Config.DEBUG:
            logging.info(f'TCP-From-{self.client_address[0]}-{message}')
        data = message.split('|')
        if data[0] != Config.AUTHENTICATION:
            self.wfile.write(b'No authentication')
            logging.warning(f'TCP-{self.client_address[0]}-No authentication')
            return None

        r = TCPRouter(data[1:]).handle()
        if Config.DEBUG:
            logging.info(f'TCP-To-{self.client_address[0]}-{r}')
        self.wfile.write(r.encode('utf-8'))


def link_play(ip: str = Config.HOST, udp_port: int = Config.UDP_PORT, tcp_port: int = Config.TCP_PORT):
    udp_server = socketserver.ThreadingUDPServer((ip, udp_port), UDP_handler)
    tcp_server = socketserver.ThreadingTCPServer((ip, tcp_port), TCP_handler)

    threads = [threading.Thread(target=udp_server.serve_forever), threading.Thread(
        target=tcp_server.serve_forever)]
    [t.start() for t in threads]
    [t.join() for t in threads]
