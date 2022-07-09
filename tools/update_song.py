import sqlite3

class Connect():
    # 数据库连接类，上下文管理

    def __init__(self, file_path='./arcaea_database.db'):
        """
            数据库连接，默认连接arcaea_database.db\ 
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


def insert(cursor, song_id, name, a, b, c, d):
    '''Insert a new song into database.'''
    cursor.execute(
        '''select exists(select * from chart where song_id=?)''', (song_id, ))
    if cursor.fetchone()[0]:
        return None
    cursor.execute(
        '''insert into chart values (?,?,?,?,?,?)''', (song_id, name, a, b, c, d))


def old_to_new():
    '''Update old database to new database.'''
    with Connect('./arcsong.db') as c:
        c.execute(
            '''select sid, name_en, rating_pst, rating_prs, rating_ftr, rating_byn from songs''')
        data = c.fetchall()
    with Connect() as c:
        for x in data:
            insert(c, x[0], x[1], x[2], x[3], x[4], x[5])


def main():
    old_to_new()


if __name__ == '__main__':
    main()
    print('Done.')
    input()
    exit()
