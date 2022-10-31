import os
import sys
from importlib import import_module
from json import load
from shutil import copy, copy2
from time import time

from core.config_manager import Config
from core.constant import ARCAEA_SERVER_VERSION
from core.course import Course
from core.purchase import Purchase
from core.sql import Connect, DatabaseMigrator
from core.user import UserRegister
from core.util import try_rename


class DatabaseInit:
    def __init__(self, db_path: str = Config.SQLITE_DATABASE_PATH, init_folder_path: str = Config.DATABASE_INIT_PATH) -> None:
        self.db_path = db_path
        self.init_folder_path = init_folder_path
        self.c = None
        self.init_data = None

    @property
    def sql_path(self) -> str:
        return os.path.join(self.init_folder_path, 'tables.sql')

    @property
    def course_path(self) -> str:
        return os.path.join(self.init_folder_path, 'courses.json')

    @property
    def pack_path(self) -> str:
        return os.path.join(self.init_folder_path, 'packs.json')

    @property
    def single_path(self) -> str:
        return os.path.join(self.init_folder_path, 'singles.json')

    def table_init(self) -> None:
        '''初始化数据库结构'''
        with open(self.sql_path, 'r') as f:
            self.c.executescript(f.read())
        self.c.execute('''insert into config values("version", :a);''', {
            'a': ARCAEA_SERVER_VERSION})

    def character_init(self) -> None:
        '''初始化搭档信息'''
        for i in range(0, len(self.init_data.char)):
            skill_requires_uncap = 1 if i == 2 else 0
            if i in [0, 1, 2, 4, 13, 26, 27, 28, 29, 36, 21, 42, 43, 11, 12, 19, 5]:
                max_level = 30
                uncapable = 1
            else:
                max_level = 20
                uncapable = 0
            sql = '''insert into character values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
            self.c.execute(sql, (i, self.init_data.char[i], max_level, self.init_data.frag1[i], self.init_data.prog1[i], self.init_data.overdrive1[i], self.init_data.frag20[i], self.init_data.prog20[i], self.init_data.overdrive20[i],
                                 self.init_data.frag30[i], self.init_data.prog30[i], self.init_data.overdrive30[i], self.init_data.skill_id[i], self.init_data.skill_unlock_level[i], skill_requires_uncap, self.init_data.skill_id_uncap[i], self.init_data.char_type[i], uncapable))

        self.c.execute('''insert into character values(?,?,20,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)''', (
            99, 'shirahime', 38, 33, 28, 66, 58, 50, 66, 58, 50, 'frags_preferred_song', 0, 0, '', 0))

        for i in self.init_data.char_core:
            self.c.executemany('''insert into char_item values(?,?,'core',?)''', [
                (i, j['core_id'], j['amount']) for j in self.init_data.char_core[i]])

    def insert_purchase_item(self, purchases: list):
        '''处理singles和packs'''
        for i in purchases:
            x = Purchase(self.c).from_dict(i)
            x.insert_all()

    def item_init(self) -> None:
        '''初始化物品信息'''
        self.c.executemany('''insert into item values(?,"core",1)''',
                           [(i,) for i in self.init_data.cores])
        self.c.executemany('''insert into item values(?,"world_song",1)''', [
            (i,) for i in self.init_data.world_songs])
        self.c.executemany('''insert into item values(?,"world_unlock",1)''', [
            (i,) for i in self.init_data.world_unlocks])
        self.c.executemany('''insert into item values(?,"course_banner",1)''', [
            (i,) for i in self.init_data.course_banners])

        self.c.execute('''insert into item values(?,?,?)''',
                       ('fragment', 'fragment', 1))
        self.c.execute('''insert into item values(?,?,?)''',
                       ('memory', 'memory', 1))
        self.c.execute('''insert into item values(?,?,?)''',
                       ('anni5tix', 'anni5tix', 1))

        with open(self.pack_path, 'r') as f:
            self.insert_purchase_item(load(f))

        with open(self.single_path, 'r') as f:
            self.insert_purchase_item(load(f))

        self.c.execute(
            '''select exists(select * from item where item_id='epilogue')''')
        if self.c.fetchone() == (0,):
            self.c.execute(
                '''insert into item values('epilogue','pack',1)''')

    def course_init(self) -> None:
        '''初始化课题信息'''
        courses = []
        with open(self.course_path, 'r', encoding='utf-8') as f:
            courses = load(f)
        for i in courses:
            x = Course(self.c).from_dict(i)
            x.insert_all()

    def role_power_init(self) -> None:
        '''初始化power和role'''
        self.c.executemany('''insert into role values(?,?)''', [(
            self.init_data.role[i], self.init_data.role_caption[i]) for i in range(len(self.init_data.role))])

        self.c.executemany('''insert into power values(?,?)''', [(
            self.init_data.power[i], self.init_data.power_caption[i]) for i in range(len(self.init_data.power))])

        for i in self.init_data.role_power:
            self.c.executemany('''insert into role_power values(?,?)''', [
                               (i, j) for j in self.init_data.role_power[i]])

    def admin_init(self) -> None:
        '''初始化测试账号'''
        x = UserRegister(self.c)
        x.user_code = '123456789'
        x.user_id = 2000000
        x.name = 'admin'
        x.email = 'admin@admin.com'
        now = int(time() * 1000)

        x._insert_user_char()

        self.c.execute('''insert into user(user_id, name, password, join_date, user_code, rating_ptt, 
        character_id, is_skill_sealed, is_char_uncapped, is_char_uncapped_override, is_hide_rating, favorite_character, max_stamina_notification_enabled, current_map, ticket, prog_boost, email)
        values(:user_id, :name, :password, :join_date, :user_code, 0, 0, 0, 0, 0, 0, -1, 0, '', :memories, 0, :email)
        ''', {'user_code': x.user_code, 'user_id': x.user_id, 'join_date': now, 'name': x.name, 'password': '41e5653fc7aeb894026d6bb7b2db7f65902b454945fa8fd65a6327047b5277fb', 'memories': 114514, 'email': x.email})
        self.c.execute('''insert into recent30(user_id) values(:user_id)''', {
                       'user_id': x.user_id})
        self.c.execute(
            '''insert into user_role values(?, "admin")''', (x.user_id,))

    def init(self) -> None:
        sys.path.append(os.path.join(sys.path[0], self.init_folder_path))
        self.init_data = import_module('arc_data').InitData

        with Connect(self.db_path) as c:
            self.c = c
            self.table_init()
            self.character_init()
            self.item_init()
            self.course_init()
            self.role_power_init()
            self.admin_init()


class FileChecker:

    def __init__(self, app=None):
        self.app = app

    def check_file(self, file_path: str) -> bool:
        f = os.path.isfile(file_path)
        if not f:
            self.app.logger.warning('File `%s` is missing.' % file_path)
        return f

    def check_folder(self, folder_path: str) -> bool:
        f = os.path.isdir(folder_path)
        if not f:
            self.app.logger.warning('Folder `%s` is missing.' % folder_path)
        return f

    def chech_update_database(self) -> bool:
        if not self.check_file(Config.SQLITE_DATABASE_PATH):
            # 新建数据库
            try:
                self.app.logger.info(
                    'Try to new the file `%s`.' % Config.SQLITE_DATABASE_PATH)
                DatabaseInit().init()
                self.app.logger.info(
                    'Success to new the file `%s`.' % Config.SQLITE_DATABASE_PATH)
            except:
                self.app.logger.warning(
                    'Fail to new the file `%s`.' % Config.SQLITE_DATABASE_PATH)
                return False
        else:
            # 检查更新
            with Connect() as c:
                try:
                    c.execute('''select value from config where id="version"''')
                    x = c.fetchone()
                except:
                    x = None
            # 数据库自动更新，不强求
            if not x or x[0] != ARCAEA_SERVER_VERSION:
                self.app.logger.warning(
                    'Maybe the file `%s` is an old version.' % Config.SQLITE_DATABASE_PATH)
                try:
                    self.app.logger.info(
                        'Try to update the file `%s`.' % Config.SQLITE_DATABASE_PATH)

                    if not os.path.isdir(Config.SQLITE_DATABASE_BACKUP_FOLDER_PATH):
                        os.makedirs(Config.SQLITE_DATABASE_BACKUP_FOLDER_PATH)

                    backup_path = try_rename(Config.SQLITE_DATABASE_PATH, os.path.join(
                        Config.SQLITE_DATABASE_BACKUP_FOLDER_PATH, os.path.split(Config.SQLITE_DATABASE_PATH)[-1] + '.bak'))

                    try:
                        copy2(backup_path, Config.SQLITE_DATABASE_PATH)
                    except:
                        copy(backup_path, Config.SQLITE_DATABASE_PATH)

                    temp_path = os.path.join(
                        *os.path.split(Config.SQLITE_DATABASE_PATH)[:-1], 'old_arcaea_database.db')
                    if os.path.isfile(temp_path):
                        os.remove(temp_path)

                    try_rename(Config.SQLITE_DATABASE_PATH, temp_path)

                    DatabaseInit().init()
                    self.update_database(temp_path)

                    self.app.logger.info(
                        'Success to update the file `%s`.' % Config.SQLITE_DATABASE_PATH)

                except ValueError:
                    self.app.logger.warning(
                        'Fail to update the file `%s`.' % Config.SQLITE_DATABASE_PATH)

        return True

    @staticmethod
    def update_database(old_path: str, new_path: str = Config.SQLITE_DATABASE_PATH) -> None:
        '''更新数据库，并删除旧文件'''
        if os.path.isfile(old_path) and os.path.isfile(new_path):
            DatabaseMigrator(old_path, new_path).update_database()
            os.remove(old_path)

    def check_before_run(self) -> bool:
        '''运行前检查，返回布尔值'''
        return self.check_folder(Config.SONG_FILE_FOLDER_PATH) & self.chech_update_database()
