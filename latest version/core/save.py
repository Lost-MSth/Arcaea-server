import json
from time import time

from .config_manager import Config
from .constant import Constant
from .error import InputError, NoData
from .util import md5


class SaveData:

    def __init__(self, c=None) -> None:
        self.c = c
        self.user = None

        self.scores_data = []
        self.clearlamps_data = []
        self.clearedsongs_data = []
        self.unlocklist_data = []
        self.installid_data: str = ''
        self.devicemodelname_data: str = ''
        self.story_data = []
        self.createdAt: int = 0
        self.finalestate_data: str = ''

    def to_dict(self):
        return {
            "user_id": self.user.user_id,
            "story": {
                "": self.story_data
            },
            "devicemodelname": {
                "val": self.devicemodelname_data
            },
            "installid":  {
                "val": self.installid_data
            },
            "unlocklist": {
                "": self.unlocklist_data
            },
            "clearedsongs": {
                "": self.clearedsongs_data
            },
            "clearlamps": {
                "": self.clearlamps_data
            },
            "scores": {
                "": self.scores_data
            },
            "version": {
                "val": 1
            },
            "createdAt": self.createdAt,
            'finalestate': {
                'val': self.finalestate_data
            }
        }

    def select_scores(self, user) -> None:
        '''
            parameter: `user` - `User`类或子类的实例
        '''
        self.user = user
        self.c.execute('''select scores_data, clearlamps_data from user_save where user_id=:a''',
                       {'a': user.user_id})
        x = self.c.fetchone()
        if not x:
            raise NoData(f'User `{user.user_id}` has no cloud save data')

        self.scores_data: list = json.loads(x[0])[""]
        self.clearlamps_data: list = json.loads(x[1])[""]

    def select_all(self, user) -> None:
        '''
            parameter: `user` - `User`类或子类的实例
        '''
        self.user = user
        self.c.execute('''select * from user_save where user_id=:a''',
                       {'a': user.user_id})
        x = self.c.fetchone()
        if x:
            self.scores_data = json.loads(x[1])[""]
            self.clearlamps_data = json.loads(x[2])[""]
            self.clearedsongs_data = json.loads(x[3])[""]
            self.unlocklist_data = json.loads(x[4])[""]
            self.installid_data = json.loads(x[5])["val"]
            self.devicemodelname_data = json.loads(x[6])["val"]
            self.story_data = json.loads(x[7])[""]
            if x[8] is not None:
                self.createdAt = int(x[8])
            self.finalestate_data = x[9] if x[9] is not None else ''

        if Config.SAVE_FULL_UNLOCK:
            self.installid_data = "0fcec8ed-7b62-48e2-9d61-55041a22b123"  # 使得可以进入存档选择上传或下载界面
            for i in self.story_data:
                i['c'] = True
                i['r'] = True
            for i in self.unlocklist_data:
                x = i['unlock_key']
                if x[-3:] == '101':
                    i['complete'] = 100
                elif x[:16] == 'aegleseeker|2|3|':
                    i['complete'] = 10
                elif x == 'saikyostronger|2|3|einherjar|2':
                    i['complete'] = 6
                elif x == 'saikyostronger|2|3|laqryma|2':
                    i['complete'] = 3
                elif x[-5:-2] == '109':
                    i['complete'] = 3
                else:
                    i['complete'] = 1

            self.finalestate_data = '|'.join(
                ['0', '100'] + [str(x[0]) if i in [64, 65, 66, 71] else str(x[1]) for i, x in enumerate(Constant.FINALE_SWITCH)] + ['1337'])

    def update_all(self, user) -> None:
        '''
            parameter: `user` - `User`类或子类的实例
        '''
        self.createdAt = int(time() * 1000)
        self.c.execute('''insert or replace into user_save values(:a,:b,:c,:d,:e,:f,:g,:h,:i,:j)''', {
            'a': user.user_id, 'b': json.dumps({'': self.scores_data}), 'c': json.dumps({'': self.clearlamps_data}), 'd': json.dumps({'': self.clearedsongs_data}), 'e': json.dumps({'': self.unlocklist_data}), 'f': json.dumps({'val': self.installid_data}), 'g': json.dumps({'val': self.devicemodelname_data}), 'h': json.dumps({'': self.story_data}), 'i': self.createdAt, 'j': self.finalestate_data})

    def set_value(self, key: str, value: str, checksum: str) -> None:
        '''
            从Arcaea客户端给的奇怪字符串中获取存档数据，并进行数据校验
        '''
        if not value:
            return None
        if key not in self.__dict__:
            raise KeyError(
                'Property `%s` is not found in the instance of `SaveData` class.' % key)

        if md5(value) == checksum:
            if key in ('installid_data', 'devicemodelname_data', 'finalestate_data'):
                self.__dict__[key] = json.loads(value)['val']
            else:
                self.__dict__[key] = json.loads(value)['']
        else:
            raise InputError('Hash value of cloud save data mismatches.')
