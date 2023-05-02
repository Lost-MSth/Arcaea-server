import os
import sqlite3
from datetime import datetime
from time import mktime

LOG_DATABASE_PATH = './arcaea_log.db'


class Connect():
    # 数据库连接类，上下文管理

    def __init__(self, file_path=LOG_DATABASE_PATH):
        """
            数据库连接
            接受：文件路径
            返回：sqlite3连接操作对象
        """
        self.file_path = file_path

    def __enter__(self):
        self.conn = sqlite3.connect(self.file_path)
        self.c = self.conn.cursor()
        return self.c

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is not None:
            print(f'exc_type: {exc_type}')
            print(f'exc_val: {exc_val}')
            print(f'exc_tb: {exc_tb}')
            if self.conn:
                self.conn.rollback()

        if self.conn:
            self.conn.commit()
            self.conn.close()

        return True


def clean_by_time(table_name: str, time_colume_name: str, colume_count: int):
    with Connect() as c:
        today = datetime.now()
        print(f'The time now is {today}.')
        day = input(
            'Please input the number of days the data before which you want to delete: ')
        try:
            day = int(day)
        except ValueError:
            print('Invalid input!')
            return
        time = mktime(today.timetuple()) - day * 24 * 60 * 60
        delete_count = c.execute(
            f'select count(*) from {table_name} where {time_colume_name} < ?', (time,)).fetchone()[0]
        all_count = c.execute(
            f'select count(*) from {table_name}').fetchone()[0]
        print(
            f'Before {day} days, there are {delete_count} records to be deleted, {all_count} records in total.')
        flag = input('Are you sure to delete these records? (y/n) ')
        if flag == 'y' or flag == 'Y':
            if delete_count >= 1000000:
                print(
                    'It will cost a long time to delete these records, please wait patiently...')
            print('Deleting...')
            c.execute('PRAGMA cache_size = 32768')
            c.execute('PRAGMA synchronous = OFF')
            c.execute('PRAGMA temp_store = MEMORY')
            if delete_count / all_count >= 0.8:
                data = c.execute(
                    f'select * from {table_name} where {time_colume_name} > ?', (time,)).fetchall()
                c.execute(f'delete from {table_name}')
                c.executemany(
                    f'insert into {table_name} values ({",".join(["?"]*colume_count)})', data)
            else:
                c.execute(
                    f'delete from {table_name} where {time_colume_name} < ?', (time,))
            c.execute('PRAGMA temp_store = DEFAULT')
            print('Delete successfully!')
        else:
            print('Delete canceled!')


def vacuum():
    print('This operation will release unused space in the database file.')
    print('It will cost a long time to release unused space if the database file is so large.')
    flag = input('Are you sure to release unused space? (y/n) ')
    if flag == 'y' or flag == 'Y':
        with Connect() as c:
            print('Releasing unused space...')
            c.execute('vacuum')
            print('Release unused space successfully!')
    else:
        print('Release unused space canceled!')


def main():
    if not os.path.exists(LOG_DATABASE_PATH):
        print('The database file `arcaea_log.db` does not exist!')
    print('-- Arcaea Server Log Database Cleaner --')
    print('Note: It is more recommended to delete the database file directly.')
    while True:
        print('-' * 40)
        print('1. clean `user_score` table')
        print('2. clean `user_rating` table')
        print('3. release unused space (`vacuum` command)')
        print('0. exit')
        choice = input('Please input your choice: ')
        if choice == '1':
            clean_by_time('user_score', 'time_played', 13)
        elif choice == '2':
            clean_by_time('user_rating', 'time', 3)
        elif choice == '3':
            vacuum()
        elif choice == '0':
            break
        else:
            print('Invalid choice!')


if __name__ == '__main__':
    main()
    input('Press `Enter` key to exit.')
