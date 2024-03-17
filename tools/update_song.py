import os
import sqlite3


SONG_DATABASE_PATH = './arcsong.db'
SERVER_DATABASE_PATH = './arcaea_database.db'


class Connect():
    # 数据库连接类，上下文管理

    def __init__(self, file_path=SERVER_DATABASE_PATH):
        """
            数据库连接\ 
            接受：文件路径\ 
            返回：sqlite3连接操作对象
        """
        self.file_path = file_path

    def __enter__(self):
        self.conn = sqlite3.connect(self.file_path)
        self.c = self.conn.cursor()
        return self.c

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is not None:
            if self.conn:
                self.conn.rollback()

        if self.conn:
            self.conn.commit()
            self.conn.close()

        return True


def insert(cursor, song_id, name, a, b, c, d, e, update_type=0):
    '''Insert a new song into database.'''
    if update_type == 0 or update_type == 1:
        cursor.execute(
            '''select exists(select * from chart where song_id=?)''', (song_id, ))
        if cursor.fetchone()[0]:
            if update_type == 0:
                # 重复则不更新，以服务端数据库数据为准
                return
            elif update_type == 1:
                # 重复则更新，以`arcsong.db`数据为准
                cursor.execute('''update chart set name=?, rating_pst=?, rating_prs=?, rating_ftr=?, rating_byn=?, rating_etr=? where song_id=?''',
                               (name, a, b, c, d, e, song_id))
                return

    cursor.execute(
        '''insert into chart values (?,?,?,?,?,?,?)''', (song_id, name, a, b, c, d, e))


def from_song_datebase():
    '''Get song data from song database and insert them into server's database.'''
    with Connect(SONG_DATABASE_PATH) as c:
        c.execute('''select name from sqlite_master where type="table"''')
        tables = [x[0] for x in c.fetchall()]
        if 'songs' in tables:
            c.execute(
                '''select sid, name_en, rating_pst, rating_prs, rating_ftr, rating_byn from songs''')
            data = []
            for x in c.fetchall():
                data.append((x[0], x[1], x[2], x[3], x[4], x[5], -1))
        elif 'charts' in tables:
            c.execute(
                '''select song_id, rating_class, name_en, rating from charts''')
            songs = {}
            for song_id, rating_class, name_en, rating in c.fetchall():
                if song_id not in songs:
                    songs[song_id] = [-1, -1, -1, -1, -1, name_en]
                songs[song_id][rating_class] = rating

            data = [(x, y[-1], y[0], y[1], y[2], y[3], y[4])
                    for x, y in songs.items()]
        else:
            print('Error: Cannot find table `songs` or `charts` in the database.')
            return

    # 用户确认更新方式
    update_type = 0
    x = input('Type a number to decide the update type:\n0: Do not update if the song already exists in the server database.\n1: Update even if the song already exists in the server database.\n2: Clear chart data in the server database and then update.\nYour choice: ')
    x = x.strip()
    if x not in ('0', '1', '2'):
        print('Error: Invalid input.')
        return
    update_type = int(x)

    with Connect() as c:
        if update_type == 2:
            # 清空数据表后更新
            c.execute('''delete from chart''')
        for x in data:
            insert(c, x[0], x[1], x[2], x[3], x[4], x[5], x[6], update_type)

    print('Seems to be done.')


def check_file():
    if not os.path.isfile(SONG_DATABASE_PATH) or not os.path.isfile(SERVER_DATABASE_PATH):
        print('Error: Files cannot be found.')
        print('Note: Please make sure that both `arcsong.db` and `arcaea_server.db` are in this directory.')
        return False
    return True


def main():
    if check_file():
        from_song_datebase()


if __name__ == '__main__':
    main()
    input('Press `Enter` key to exit.')
