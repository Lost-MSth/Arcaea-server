from .sql import Connect
import base64


def get_song_unlock(client_song_map):
    # 处理可用歌曲bit，返回bytes

    user_song_unlock = [0] * 512
    for i in range(0, 1024, 2):
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


def create_room(conn, user_id, client_song_map):
    # 创建房间，返回错误码和房间与用户信息
    error_code = 108

    with Connect() as c:
        c.execute('''select name from user where user_id=?''', (user_id,))
        x = c.fetchone()
        if x is not None:
            name = x[0]

    song_unlock = get_song_unlock(client_song_map)

    conn.send((1, name, song_unlock))
    if conn.poll(10):
        data = conn.recv()
    else:
        data = (-1,)

    if data[0] == 0:
        error_code = 0
        return error_code, {'roomCode': data[1],
                            'roomId': str(data[2]),
                            'token': str(data[3]),
                            'key': (base64.b64encode(data[4])).decode(),
                            'playerId': str(data[5]),
                            'userId': user_id,
                            'orderedAllowedSongs': (base64.b64encode(song_unlock)).decode()
                            }

    return error_code, None


def join_room(conn, user_id, client_song_map, room_code):
    # 加入房间，返回错误码和房间与用户信息
    error_code = 108

    with Connect() as c:
        c.execute('''select name from user where user_id=?''', (user_id,))
        x = c.fetchone()
        if x is not None:
            name = x[0]

    song_unlock = get_song_unlock(client_song_map)

    conn.send((2, name, song_unlock, room_code))
    if conn.poll(10):
        data = conn.recv()
    else:
        data = (-1,)

    if data[0] == 0:
        error_code = 0
        return error_code, {'roomCode': data[1],
                            'roomId': str(data[2]),
                            'token': str(data[3]),
                            'key': (base64.b64encode(data[4])).decode(),
                            'playerId': str(data[5]),
                            'userId': user_id,
                            'orderedAllowedSongs': (base64.b64encode(data[6])).decode()
                            }
    else:
        error_code = data[0]

    return error_code, None


def update_room(conn, user_id, token):
    # 更新房间，返回错误码和房间与用户信息
    error_code = 108

    conn.send((3, int(token)))
    if conn.poll(10):
        data = conn.recv()
    else:
        data = (-1,)

    if data[0] == 0:
        error_code = 0
        return error_code, {'roomCode': data[1],
                            'roomId': str(data[2]),
                            'token': token,
                            'key': (base64.b64encode(data[3])).decode(),
                            'playerId': str(data[4]),
                            'userId': user_id,
                            'orderedAllowedSongs': (base64.b64encode(data[5])).decode()
                            }
    else:
        error_code = data[0]

    return error_code, None
