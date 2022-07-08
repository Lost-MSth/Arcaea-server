from .util import md5
from .error import InputError
from setting import Config
from time import time
import json


class SaveData:

    def __init__(self, c=None) -> None:
        self.c = c
        self.scores_data = []
        self.clearlamps_data = []
        self.clearedsongs_data = []
        self.unlocklist_data = []
        self.installid_data: str = ''
        self.devicemodelname_data: str = ''
        self.story_data = []
        self.createdAt: int = 0
        self.finalestate_data: str = "0|100|5616|85146|402821|148126|629916|492991|982851|510091|1912|942819|100606|919245|26270|781178|265839|354540|1611284|6478221|7178089|9580111|139100|2757121|1411969|2249637|3927929|26270|781178|265839|7692918|1245269|5628557|6199755|8340388|6897967|9435206|8853182|6483214|4923592|718524|8922556|7939972|1762215|877327|7939972|3229801|3217716|1642203|2487749|1624592|5357186|5362614|4202613|27003|7178029|4047038|9202383|8677179|4916716|2126424|2140654|5258529|1844588|7228940|3956629|65189|8123987|74181243|9173764|6123461|37167213|671214|171272315|1337"

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
            # 'finalestate': {
            #     'val': self.finalestate_data
            # }
        }

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

        if Config.SAVE_FULL_UNLOCK:
            self.installid_data = "0fcec8ed-7b62-48e2-9d61-55041a22b123"  # 使得可以进入存档选择上传或下载界面
            for i in self.story_data:
                i['c'] = True
                i['r'] = True
            for i in self.unlocklist_data:
                if i['unlock_key'][-3:] == '101':
                    i['complete'] = 100
                elif i['unlock_key'][:16] == 'aegleseeker|2|3|':
                    i['complete'] = 10
                elif i['unlock_key'] == 'saikyostronger|2|3|einherjar|2':
                    i['complete'] = 6
                elif i['unlock_key'] == 'saikyostronger|2|3|laqryma|2':
                    i['complete'] = 3
                else:
                    i['complete'] = 1

    def update_all(self, user) -> None:
        '''
            parameter: `user` - `User`类或子类的实例
        '''
        self.createdAt = int(time() * 1000)
        self.c.execute('''delete from user_save where user_id=:a''', {
                       'a': user.user_id})
        self.c.execute('''insert into user_save values(:a,:b,:c,:d,:e,:f,:g,:h,:i)''', {
            'a': user.user_id, 'b': json.dumps({'': self.scores_data}), 'c': json.dumps({'': self.clearlamps_data}), 'd': json.dumps({'': self.clearedsongs_data}), 'e': json.dumps({'': self.unlocklist_data}), 'f': json.dumps({'val': self.installid_data}), 'g': json.dumps({'val': self.devicemodelname_data}), 'h': json.dumps({'': self.story_data}), 'i': self.createdAt})

    def set_value(self, key: str, value: str, checksum: str) -> None:
        '''
            从Arcaea客户端给的奇怪字符串中获取存档数据，并进行数据校验
        '''
        if key not in self.__dict__:
            raise KeyError(
                'Property `%s` is not found in the instance of `SaveData` class.' % key)

        if md5(value) == checksum:
            if key == 'installid_data' or key == 'devicemodelname_data':
                self.__dict__[key] = json.loads(value)['val']
            else:
                self.__dict__[key] = json.loads(value)['']
        else:
            raise InputError('Hash value of cloud save data mismatches.')
