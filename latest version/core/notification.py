from .config_manager import Config
from .user import User
from .sql import Connect

from time import time


class BaseNotification:

    notification_type = None

    def __init__(self, c_m=None) -> None:
        self.receiver = None
        self.sender = None
        self.timestamp = None
        self.content = None

        self.c_m = c_m

    @property
    def is_expired(self) -> bool:
        now = round(time() * 1000)
        return now - self.timestamp > Config.NOTIFICATION_EXPIRE_TIME

    def to_dict(self) -> dict:
        raise NotImplementedError()

    def insert(self):
        self.receiver.select_user_one_column('mp_notification_enabled', True, bool)
        if not self.receiver.mp_notification_enabled:
            return

        self.c_m.execute(
            '''select max(id) from notification where user_id = ?''', (self.receiver.user_id,))
        x = self.c_m.fetchone()
        if x is None or x[0] is None:
            x = 0
        else:
            x = x[0] + 1

        self.c_m.execute(
            '''insert into notification values (?, ?, ?, ?, ?, ?, ?)''',
            (self.receiver.user_id, x, self.notification_type, self.content,
             self.sender.user_id, self.sender.name, self.timestamp)
        )


class RoomInviteNotification(BaseNotification):

    notification_type = 'room_inv'

    @classmethod
    def from_list(cls, l: list, user: User = None) -> 'RoomInviteNotification':
        x = cls()
        x.sender = User()
        x.sender.user_id = l[2]
        x.sender.name = l[3]
        x.content = l[1]
        x.timestamp = l[4]
        x.receiver = user
        return x

    @classmethod
    def from_sender(cls, sender: User, receiver: User, share_token: str, c_m) -> 'RoomInviteNotification':
        x = cls()
        x.c_m = c_m
        x.sender = sender
        x.receiver = receiver
        x.content = share_token
        x.timestamp = round(time() * 1000)
        return x

    def to_dict(self) -> dict:
        return {
            'sender': self.sender.name,
            'type': self.notification_type,
            'shareToken': self.content,
            'sendTs': self.timestamp
        }


class NotificationFactory:
    def __init__(self, c_m: Connect, user=None):
        self.c_m = c_m
        self.user = user

    def get_notification(self) -> 'list[BaseNotification]':
        r = []

        self.c_m.execute('''select type, content, sender_user_id, sender_name, timestamp from notification where user_id = ?''',
                         (self.user.user_id,))
        for i in self.c_m.fetchall():
            x = None
            if i[0] == 'room_inv':
                x = RoomInviteNotification.from_list(i, self.user)

            if x is not None and not x.is_expired:
                r.append(x)
        self.c_m.execute(
            '''delete from notification where user_id = ?''', (self.user.user_id,))
        return r
