import json
import os
from functools import lru_cache
from time import time

from flask import url_for

from .config_manager import Config
from .constant import Constant
from .error import NoAccess, NoData, RateLimit
from .limiter import ArcLimiter


class BundlePart:
    def __init__(self) -> None:
        self.path: str = None  # relative path
        self.size: int = 0
        self.url: str = None


class ContentBundle:

    def __init__(self) -> None:
        self.version: str = None
        self.prev_version: str = None
        self.app_version: str = None
        self.uuid: str = None
        self.part_num: int = None

        self.json_size: int = None
        # self.bundle_size: int = None
        self.json_path: str = None  # relative path
        self.bundle_parts: 'list[BundlePart]' = []

        self.json_url: str = None

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
        x.part_num = json_data.get('totalPartitions', 1)
        if x.prev_version is None:
            x.prev_version = '0.0.0'
        return x

    def to_dict(self) -> dict:
        r = {
            'contentBundleVersion': self.version,
            'appVersion': self.app_version,
            'jsonSize': self.json_size,
        }
        if self.json_url:
            r['jsonUrl'] = self.json_url
            parts = []
            for p in self.bundle_parts:
                part = {'bundleSize': p.size}
                if p.url:
                    part['bundleUrl'] = p.url
                parts.append(part)
            if parts:
                r['bundleParts'] = parts
        return r

    def calculate_size(self) -> None:
        self.json_size = os.path.getsize(os.path.join(
            Constant.CONTENT_BUNDLE_FOLDER_PATH, self.json_path))
        for part in self.bundle_parts:
            part.size = os.path.getsize(os.path.join(
                Constant.CONTENT_BUNDLE_FOLDER_PATH, part.path))


class BundleParser:

    # {app_version: [ List[ContentBundle] ]}
    bundles: 'dict[str, list[ContentBundle]]' = {}
    # {app_version: max bundle version}
    max_bundle_version: 'dict[str, str]' = {}

    # {bundle version: [next versions]} 宽搜索引
    next_versions: 'dict[str, list[str]]' = {}
    # {(bver, b prev version): ContentBundle} 正向索引
    version_tuple_bundles: 'dict[tuple[str, str], ContentBundle]' = {}

    def __init__(self) -> None:
        if not self.bundles:
            self.parse()

    def re_init(self) -> None:
        self.bundles.clear()
        self.max_bundle_version.clear()
        self.next_versions.clear()
        self.version_tuple_bundles.clear()
        self.get_bundles.cache_clear()
        self.parse()

    def parse(self) -> None:
        for root, dirs, files in os.walk(Constant.CONTENT_BUNDLE_FOLDER_PATH):
            for file in files:
                if not file.endswith('.json'):
                    continue

                json_path = os.path.join(root, file)
                stem = file[:-5]

                with open(json_path, 'rb') as f:
                    data = json.load(f)

                x = ContentBundle.from_json(data)

                x.json_path = os.path.relpath(
                    json_path, Constant.CONTENT_BUNDLE_FOLDER_PATH)
                # x.bundle_path = os.path.relpath(
                #     bundle_path, Constant.CONTENT_BUNDLE_FOLDER_PATH)

                x.json_path = x.json_path.replace('\\', '/')
                # x.bundle_path = x.bundle_path.replace('\\', '/')

                # Single-file bundle (backward compat)
                single = os.path.join(root, f'{stem}.cb')
                if os.path.isfile(single):
                    part = BundlePart()
                    part.path = os.path.relpath(
                        single, Constant.CONTENT_BUNDLE_FOLDER_PATH).replace('\\', '/')
                    x.bundle_parts.append(part)
                else:
                    # Multi-part bundles: stem_0.cb, stem_1.cb, ...
                    for part_idx in range(x.part_num):
                        part_path = os.path.join(root, f'{stem}_{part_idx}.cb')
                        if not os.path.isfile(part_path):
                            break
                        part = BundlePart()
                        part.path = os.path.relpath(
                            part_path, Constant.CONTENT_BUNDLE_FOLDER_PATH).replace('\\', '/')
                        x.bundle_parts.append(part)

                if not x.bundle_parts:
                    raise FileNotFoundError(
                        f'Bundle file(s) not found for: {json_path}')
                x.calculate_size()

                self.bundles.setdefault(x.app_version, []).append(x)

                self.version_tuple_bundles[(x.version, x.prev_version)] = x
                self.next_versions.setdefault(
                    x.prev_version, []).append(x.version)

        # sort by version
        for k, v in self.bundles.items():
            v.sort(key=lambda x: x.version_tuple)
            self.max_bundle_version[k] = v[-1].version

    @staticmethod
    @lru_cache(maxsize=Constant.LRU_CACHE_MAX_SIZE['get_bundles'])
    def get_bundles(app_ver: str, b_ver: str) -> 'list[ContentBundle]':
        if Config.BUNDLE_STRICT_MODE:
            return BundleParser.bundles.get(app_ver, [])

        k = b_ver if b_ver else '0.0.0'

        target_version = BundleParser.max_bundle_version.get(app_ver, '0.0.0')
        if k == target_version:
            return []

        # BFS
        q = [[k]]
        ans = None
        while True:
            qq = []
            for x in q:
                if x[-1] == target_version:
                    ans = x
                    break
                for y in BundleParser.next_versions.get(x[-1], []):
                    if y in x:
                        continue
                    qq.append(x + [y])

            if ans is not None or not qq:
                break
            q = qq

        if not ans:
            raise NoData(
                f'No bundles found for app version: {app_ver}, bundle version: {b_ver}', status=404)

        r = []
        for i in range(1, len(ans)):
            r.append(BundleParser.version_tuple_bundles[(ans[i], ans[i-1])])

        return r


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
        bundles: 'list[ContentBundle]' = BundleParser.get_bundles(
            self.client_app_version, self.client_bundle_version)

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

            x.json_url = url_func(t1)

            sql_list.append((t1, x.json_path, now, self.device_id))
            for part in x.bundle_parts:
                t = os.urandom(64).hex()
                part.url = url_func(t)
                sql_list.append((t, part.path, now, self.device_id))

            r.append(x.to_dict())

        if not sql_list:
            return []

        self.clear_expired_token()

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

    def clear_expired_token(self) -> None:
        self.c_m.execute(
            '''delete from bundle_download_token where time < ?''', (int(time() - Constant.BUNDLE_DOWNLOAD_TIME_GAP_LIMIT),))
