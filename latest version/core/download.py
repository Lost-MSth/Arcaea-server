import os
from functools import lru_cache
from json import loads
from time import time

from flask import make_response, redirect, send_from_directory, url_for

from .config_manager import Config
from .constant import Constant
from .error import ConfigError, NoAccess
from .limiter import ArcLimiter
from .user import User
from .util import get_file_md5, join_path, md5, secure_link_md5


@lru_cache(maxsize=Constant.LRU_CACHE_MAX_SIZE['get_song_file_md5'])
def get_song_file_md5(song_id: str, file_name: str) -> str:
    path = os.path.join(Constant.SONG_FILE_FOLDER_PATH, song_id, file_name)
    if not os.path.isfile(path):
        return None
    return get_file_md5(path)


class SonglistParser:
    '''songlist 文件解析器'''

    FILE_NAMES = ['0.aff', '1.aff', '2.aff', '3.aff', '4.aff',
                  'base.ogg', '3.ogg', 'video.mp4', 'video_audio.ogg', 'video_720.mp4', 'video_1080.mp4']

    has_songlist = False
    songs: dict = {}  # {song_id: value, ...}
    # value: bitmap

    pack_info: 'dict[str, set]' = {}  # {pack_id: {song_id, ...}, ...}
    free_songs: set = set()  # {song_id, ...}
    world_songs: set = set()  # {world_song_id, ...}

    def __init__(self, path=Constant.SONGLIST_FILE_PATH) -> None:
        self.path = path
        self.data: list = []
        self.parse()

    @staticmethod
    def is_available_file(song_id: str, file_name: str) -> bool:
        '''判断文件是否允许被下载'''
        if song_id not in SonglistParser.songs:
            # songlist没有，则只限制文件名
            return file_name in SonglistParser.FILE_NAMES
        rule = SonglistParser.songs[song_id]
        for i, v in enumerate(SonglistParser.FILE_NAMES):
            if file_name == v and rule & (1 << i) != 0:
                return True
        return False

    @staticmethod
    def get_user_unlocks(user) -> set:
        '''user: UserInfo类或子类的实例'''
        x = SonglistParser
        if user is None:
            return set()

        r = set()
        for i in user.packs:
            if i in x.pack_info:
                r.update(x.pack_info[i])

        if Constant.SINGLE_PACK_NAME in x.pack_info:
            r.update(x.pack_info[Constant.SINGLE_PACK_NAME]
                     & set(user.singles))
        r.update(set(i if i[-1] != '3' else i[:-1]
                     for i in (x.world_songs & set(user.world_songs))))
        r.update(x.free_songs)

        return r

    def parse_one(self, song: dict) -> dict:
        '''解析单个歌曲'''
        # TODO: byd_local_unlock ???
        if 'id' not in song:
            return {}
        r = 0
        if 'remote_dl' in song and song['remote_dl']:
            r |= 32
            for i in song.get('difficulties', []):
                if i['ratingClass'] == 3 and i.get('audioOverride', False):
                    r |= 64
                r |= 1 << i['ratingClass']
        else:  # 針對remote_dl為False時BYD難度強制下載的處理
            for i in song.get('difficulties', []):
                if i['ratingClass'] == 3:
                    r |= 8
                    if i.get('audioOverride', False):
                        r |= 64

        for extra_file in song.get('additional_files', []):
            x = extra_file['file_name']
            if x == SonglistParser.FILE_NAMES[7]:
                r |= 128
            elif x == SonglistParser.FILE_NAMES[8]:
                r |= 256
            elif x == SonglistParser.FILE_NAMES[9]:
                r |= 512
            elif x == SonglistParser.FILE_NAMES[10]:
                r |= 1024

        return {song['id']: r}

    def parse_one_unlock(self, song: dict) -> None:
        '''解析单个歌曲解锁方式'''
        if 'id' not in song or 'set' not in song or 'purchase' not in song:
            return {}
        x = SonglistParser
        if Constant.FREE_PACK_NAME == song['set']:
            if any(i['ratingClass'] == 3 for i in song.get('difficulties', [])):
                x.world_songs.add(song['id'] + '3')
            x.free_songs.add(song['id'])
            return None

        if song.get('world_unlock', False):
            x.world_songs.add(song['id'])

        if song['purchase'] == '':
            return None

        x.pack_info.setdefault(song['set'], set()).add(song['id'])

    def parse(self) -> None:
        '''解析songlist文件'''
        if not os.path.isfile(self.path):
            return
        with open(self.path, 'rb') as f:
            self.data = loads(f.read()).get('songs', [])
        self.has_songlist = True
        for x in self.data:
            self.songs.update(self.parse_one(x))
            self.parse_one_unlock(x)


class UserDownload:
    '''
        用户下载类

        properties: `user` - `UserInfo`类或子类的实例
    '''

    limiter = ArcLimiter(
        str(Constant.DOWNLOAD_TIMES_LIMIT) + '/day', 'download')

    def __init__(self, c_m=None, user=None) -> None:
        self.c_m = c_m
        self.user = user

        self.song_id: str = None
        self.file_name: str = None

        self.token: str = None
        self.token_time: int = None

    @property
    def is_limited(self) -> bool:
        '''是否达到用户最大下载量'''
        if self.user is None:
            self.select_for_check()

        return not self.limiter.test(str(self.user.user_id))

    @property
    def is_valid(self) -> bool:
        '''链接是否有效且未过期'''
        if self.token_time is None:
            self.select_for_check()
        return int(time()) - self.token_time <= Constant.DOWNLOAD_TIME_GAP_LIMIT

    def download_hit(self) -> bool:
        '''下载次数+1，返回成功与否bool值'''
        return self.limiter.hit(str(self.user.user_id))

    def select_for_check(self) -> None:
        '''利用token、song_id、file_name查询其它信息'''
        self.c_m.execute('''select user_id, time from download_token where song_id=? and file_name=? and token = ? limit 1;''',
                         (self.song_id, self.file_name, self.token))

        x = self.c_m.fetchone()
        if not x:
            raise NoAccess('The token `%s` is not valid.' %
                           self.token, status=403)
        self.user = User()
        self.user.user_id = x[0]
        self.token_time = x[1]

    def generate_token(self) -> None:
        self.token_time = int(time())
        self.token = md5(str(self.user.user_id) + self.song_id +
                         self.file_name + str(self.token_time) + str(os.urandom(8)))

    def insert_download_token(self) -> None:
        '''将数据插入数据库，让这个下载链接可用'''
        self.c_m.execute('''insert or replace into download_token values(:a,:b,:c,:d,:e)''', {
            'a': self.user.user_id, 'b': self.song_id, 'c': self.file_name, 'd': self.token, 'e': self.token_time})

    @property
    def url(self) -> str:
        '''生成下载链接'''
        if self.token is None:
            self.generate_token()
            # self.insert_download_token() # 循环插入速度慢，改为executemany
        if Constant.DOWNLOAD_LINK_PREFIX:
            prefix = Constant.DOWNLOAD_LINK_PREFIX
            if prefix[-1] != '/':
                prefix += '/'
            return f'{prefix}{self.song_id}/{self.file_name}?t={self.token}'
        return url_for('download', file_path=f'{self.song_id}/{self.file_name}', t=self.token, _external=True)

    @property
    def hash(self) -> str:
        return get_song_file_md5(self.song_id, self.file_name)


class DownloadList(UserDownload):
    '''
        下载列表类
        properties: `user` - `User`类或子类的实例
    '''

    def __init__(self, c_m=None, user=None) -> None:
        super().__init__(c_m, user)

        self.song_ids: list = None
        self.url_flag: bool = None

        self.downloads: list = []
        self.urls: dict = {}

    @classmethod
    def initialize_cache(cls) -> None:
        '''初始化歌曲数据缓存，包括md5、文件目录遍历、解析songlist'''
        SonglistParser()
        if Config.SONG_FILE_HASH_PRE_CALCULATE:
            x = cls()
            x.url_flag = False
            x.add_songs()
            del x

    @staticmethod
    def clear_all_cache() -> None:
        '''清除所有歌曲文件有关缓存'''
        get_song_file_md5.cache_clear()
        DownloadList.get_one_song_file_names.cache_clear()
        DownloadList.get_all_song_ids.cache_clear()
        SonglistParser.songs = {}
        SonglistParser.pack_info = {}
        SonglistParser.free_songs = set()
        SonglistParser.world_songs = set()
        SonglistParser.has_songlist = False

    def clear_download_token(self) -> None:
        '''清除过期下载链接'''
        self.c_m.execute('''delete from download_token where time<?''',
                         (int(time()) - Constant.DOWNLOAD_TIME_GAP_LIMIT,))

    def insert_download_tokens(self) -> None:
        '''插入所有下载链接'''
        self.c_m.executemany('''insert or replace into download_token values(?,?,?,?,?)''', [(
            self.user.user_id, x.song_id, x.file_name, x.token, x.token_time) for x in self.downloads])

    @staticmethod
    @lru_cache(maxsize=Constant.LRU_CACHE_MAX_SIZE['get_one_song_file_names'])
    def get_one_song_file_names(song_id: str) -> list:
        '''获取一个歌曲文件夹下的所有合法文件名，有lru缓存'''
        r = []
        for i in os.scandir(os.path.join(Constant.SONG_FILE_FOLDER_PATH, song_id)):
            file_name = i.name
            if i.is_file() and SonglistParser.is_available_file(song_id, file_name):
                r.append(file_name)
        return r

    def add_one_song(self, song_id: str) -> None:

        re = {}
        for i in self.get_one_song_file_names(song_id):
            x = UserDownload(self.c_m, self.user)
            self.downloads.append(x)
            x.song_id = song_id
            x.file_name = i
            if i == 'base.ogg':
                if 'audio' not in re:
                    re['audio'] = {}

                re['audio']["checksum"] = x.hash
                if self.url_flag:
                    re['audio']["url"] = x.url
            elif i == '3.ogg':
                if 'audio' not in re:
                    re['audio'] = {}

                if self.url_flag:
                    re['audio']['3'] = {"checksum": x.hash, "url": x.url}
                else:
                    re['audio']['3'] = {"checksum": x.hash}
            elif i in ('video.mp4', 'video_audio.ogg', 'video_720.mp4', 'video_1080.mp4'):
                if 'additional_files' not in re:
                    re['additional_files'] = []

                if self.url_flag:
                    re['additional_files'].append(
                        {"checksum": x.hash, "url": x.url, 'file_name': i})
                else:
                    re['additional_files'].append(
                        {"checksum": x.hash, 'file_name': i})
                # 有参数 requirement 作用未知
            else:
                if 'chart' not in re:
                    re['chart'] = {}

                if self.url_flag:
                    re['chart'][i[0]] = {"checksum": x.hash, "url": x.url}
                else:
                    re['chart'][i[0]] = {"checksum": x.hash}

        self.urls.update({song_id: re})

    @staticmethod
    @lru_cache()
    def get_all_song_ids() -> list:
        '''获取全歌曲文件夹列表，有lru缓存'''
        return [i.name for i in os.scandir(Constant.SONG_FILE_FOLDER_PATH) if i.is_dir()]

    def add_songs(self, song_ids: list = None) -> None:
        '''添加一个或多个歌曲到下载列表，若`song_ids`为空，则添加所有歌曲'''
        if song_ids is not None:
            self.song_ids = song_ids

        if not self.song_ids:
            self.song_ids = self.get_all_song_ids()
            if Config.DOWNLOAD_FORBID_WHEN_NO_ITEM and SonglistParser.has_songlist:
                # 没有歌曲时不允许下载
                self.song_ids = list(SonglistParser.get_user_unlocks(
                    self.user) & set(self.song_ids))

            for i in self.song_ids:
                self.add_one_song(i)
        else:
            if Config.DOWNLOAD_FORBID_WHEN_NO_ITEM and SonglistParser.has_songlist:
                # 没有歌曲时不允许下载
                self.song_ids = list(SonglistParser.get_user_unlocks(
                    self.user) & set(self.song_ids))

            for i in self.song_ids:
                if os.path.isdir(os.path.join(Constant.SONG_FILE_FOLDER_PATH, i)):
                    self.add_one_song(i)

        if self.url_flag:
            self.clear_download_token()
            self.insert_download_tokens()


class DownloadManager:

    def __init__(self, file_path: str, is_bundle: bool = False) -> None:
        self.file_path = file_path
        self.is_bundle = is_bundle
        self._s3 = None

        if Config.REMOTE_DOWNLOAD_MODE == 's3':
            self._set_s3_client()

    @property
    def expire_time(self) -> int:
        return Constant.BUNDLE_DOWNLOAD_TIME_GAP_LIMIT if self.is_bundle else Constant.DOWNLOAD_TIME_GAP_LIMIT

    def get_response(self):
        if Config.REMOTE_DOWNLOAD_MODE == 'nginx':
            return self._nginx_secure_link()
        elif Config.DOWNLOAD_USE_NGINX_X_ACCEL_REDIRECT:
            return self._nginx_x_accel_redirect()
        elif Config.REMOTE_DOWNLOAD_MODE == 's3':
            return self._s3_generate_presigned_url()
        else:
            return self._default_localhost_download()

    def _default_localhost_download(self):
        folder = Constant.CONTENT_BUNDLE_FOLDER_PATH if self.is_bundle else Constant.SONG_FILE_FOLDER_PATH
        return send_from_directory(folder, self.file_path, as_attachment=True, conditional=True)

    def _nginx_x_accel_redirect(self):
        prefix = Config.BUNDLE_NGINX_X_ACCEL_REDIRECT_PREFIX if self.is_bundle else Config.NGINX_X_ACCEL_REDIRECT_PREFIX
        response = make_response()
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['X-Accel-Redirect'] = join_path(
            prefix, self.file_path, start_sep=True, end_sep=False)
        return response

    def _nginx_secure_link(self):
        options = Config.REMOTE_DOWNLOAD_OPTIONS.get('nginx', {})
        if not options:
            raise ConfigError('Nginx secure link is not configured.')
        prefix = options.get('bundle_download_link_prefix') if self.is_bundle else options.get(
            'download_link_prefix')
        host = options.get('bundle_download_link_host') if self.is_bundle else options.get(
            'download_link_host')
        secret_key = options.get('secret_key')
        if not prefix or not host or not secret_key:
            raise ConfigError('Nginx secure link is not properly configured.')

        expire = self.expire_time
        expires = int(time()) + expire

        path = join_path(prefix, self.file_path, start_sep=True, end_sep=False)
        raw = f'{expires}|{path} {secret_key}'

        url = join_path(host, path, start_sep=False, end_sep=False) + \
            f'?md5={secure_link_md5(raw)}&expires={expires}'
        return redirect(url)

    def _set_s3_client(self):
        import boto3
        from botocore.config import Config as BotoConfig
        options = Config.REMOTE_DOWNLOAD_OPTIONS.get('s3', {})
        if not options:
            raise ConfigError('S3 remote download is not configured.')
        args = {
            'endpoint_url': options.get('endpoint_url'),
            'aws_access_key_id': options.get('aws_access_key_id'),
            'aws_secret_access_key': options.get('aws_secret_access_key'),
            'region_name': options.get('region_name'),
            'config': BotoConfig(**options.get('config', {})),
            'api_version': options.get('api_version'),
            'use_ssl': options.get('use_ssl', True),
            'verify': options.get('verify'),
            'aws_session_token': options.get('aws_session_token'),
            'aws_account_id': options.get('aws_account_id'),
        }
        self._s3 = boto3.client(
            's3',
            **args
        )

    def _s3_generate_presigned_url(self):
        options = Config.REMOTE_DOWNLOAD_OPTIONS.get('s3', {})
        bucket_name = options.get(
            'song_bucket_name') if not self.is_bundle else options.get('bundle_bucket_name')
        key_prefix = options.get('song_file_key_prefix') if not self.is_bundle else options.get(
            'bundle_file_key_prefix')
        if not bucket_name or not key_prefix:
            raise ConfigError('S3 remote download is not properly configured.')

        key = join_path(key_prefix, self.file_path,
                        start_sep=False, end_sep=False)
        url = self._s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': key},
            ExpiresIn=self.expire_time
        )
        return redirect(url)
