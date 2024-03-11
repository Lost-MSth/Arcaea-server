import json
import os
from time import time

from flask import url_for

from .constant import Constant
from .error import NoAccess, RateLimit
from .limiter import ArcLimiter


class ContentBundle:

    def __init__(self) -> None:
        self.version: str = None
        self.prev_version: str = None
        self.app_version: str = None
        self.uuid: str = None

        self.json_size: int = None
        self.bundle_size: int = None
        self.json_path: str = None  # relative path
        self.bundle_path: str = None  # relative path

        self.json_url: str = None
        self.bundle_url: str = None

    @staticmethod
    def parse_version(version: str) -> tuple:
        try:
            r = tuple(map(int, version.split('.')))
        except AttributeError:
            r = (0, 0, 0)
        return r

    @property
    def version_tuple(self) -> tuple:
        return self.parse_version(self.version)

    @classmethod
    def from_json(cls, json_data: dict) -> 'ContentBundle':
        x = cls()
        x.version = json_data['versionNumber']
        x.prev_version = json_data['previousVersionNumber']
        x.app_version = json_data['applicationVersionNumber']
        x.uuid = json_data['uuid']
        return x

    def to_dict(self) -> dict:
        r = {
            'contentBundleVersion': self.version,
            'appVersion': self.app_version,
            'jsonSize': self.json_size,
            'bundleSize': self.bundle_size,
        }
        if self.json_url and self.bundle_url:
            r['jsonUrl'] = self.json_url
            r['bundleUrl'] = self.bundle_url
        return r

    def calculate_size(self) -> None:
        self.json_size = os.path.getsize(os.path.join(
            Constant.CONTENT_BUNDLE_FOLDER_PATH, self.json_path))
        self.bundle_size = os.path.getsize(os.path.join(
            Constant.CONTENT_BUNDLE_FOLDER_PATH, self.bundle_path))


class BundleParser:

    # {app_version: [ List[ContentBundle] ]}
    bundles: 'dict[str, list[ContentBundle]]' = {}
    max_bundle_version: 'dict[str, str]' = {}

    def __init__(self) -> None:
        self.parse()

    def re_init(self) -> None:
        self.bundles.clear()
        self.max_bundle_version.clear()
        self.parse()

    def parse(self) -> None:
        for root, dirs, files in os.walk(Constant.CONTENT_BUNDLE_FOLDER_PATH):
            for file in files:
                if not file.endswith('.json'):
                    continue

                json_path = os.path.join(root, file)
                bundle_path = os.path.join(root, f'{file[:-5]}.cb')

                with open(json_path, 'rb') as f:
                    data = json.load(f)

                x = ContentBundle.from_json(data)

                x.json_path = os.path.relpath(
                    json_path, Constant.CONTENT_BUNDLE_FOLDER_PATH)
                x.bundle_path = os.path.relpath(
                    bundle_path, Constant.CONTENT_BUNDLE_FOLDER_PATH)

                x.json_path = x.json_path.replace('\\', '/')
                x.bundle_path = x.bundle_path.replace('\\', '/')

                if not os.path.isfile(bundle_path):
                    raise FileNotFoundError(
                        f'Bundle file not found: {bundle_path}')
                x.calculate_size()

                if x.app_version not in self.bundles:
                    self.bundles[x.app_version] = []
                self.bundles[x.app_version].append(x)

        # sort by version
        for k, v in self.bundles.items():
            v.sort(key=lambda x: x.version_tuple)
            self.max_bundle_version[k] = v[-1].version


class BundleDownload:

    limiter = ArcLimiter(
        Constant.BUNDLE_DOWNLOAD_TIMES_LIMIT, 'bundle_download')

    def __init__(self, c_m=None):
        self.c_m = c_m

        self.client_app_version = None
        self.client_bundle_version = None
        self.device_id = None

    def set_client_info(self, app_version: str, bundle_version: str, device_id: str = None) -> None:
        self.client_app_version = app_version
        self.client_bundle_version = bundle_version
        self.device_id = device_id

    def get_bundle_list(self) -> list:
        bundles: 'list[ContentBundle]' = BundleParser.bundles.get(
            self.client_app_version, [])
        if not bundles:
            return []

        now = time()

        if Constant.BUNDLE_DOWNLOAD_LINK_PREFIX:
            prefix = Constant.BUNDLE_DOWNLOAD_LINK_PREFIX
            if prefix[-1] != '/':
                prefix += '/'

            def url_func(x): return f'{prefix}{x}'
        else:
            def url_func(x): return url_for(
                'bundle_download', token=x, _external=True)

        sql_list = []
        r = []
        for x in bundles:
            if x.version_tuple <= ContentBundle.parse_version(self.client_bundle_version):
                continue
            t1 = os.urandom(64).hex()
            t2 = os.urandom(64).hex()

            x.json_url = url_func(t1)
            x.bundle_url = url_func(t2)

            sql_list.append((t1, x.json_path, now, self.device_id))
            sql_list.append((t2, x.bundle_path, now, self.device_id))
            r.append(x.to_dict())

        if not sql_list:
            return []

        self.c_m.executemany(
            '''insert into bundle_download_token values (?, ?, ?, ?)''', sql_list)

        return r

    def get_path_by_token(self, token: str, ip: str) -> str:
        r = self.c_m.execute(
            '''select file_path, time, device_id from bundle_download_token where token = ?''', (token,)).fetchone()
        if not r:
            raise NoAccess('Invalid token.', status=403)
        file_path, create_time, device_id = r

        if time() - create_time > Constant.BUNDLE_DOWNLOAD_TIME_GAP_LIMIT:
            raise NoAccess('Expired token.', status=403)

        if file_path.endswith('.cb') and not self.limiter.hit(ip):
            raise RateLimit(
                f'Too many content bundle downloads, IP: {ip}, DeviceID: {device_id}', status=429)

        return file_path
