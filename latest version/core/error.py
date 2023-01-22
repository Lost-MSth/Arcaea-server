class ArcError(Exception):
    def __init__(self, message=None, error_code=108, api_error_code=-999, extra_data=None, status=200) -> None:
        self.message: str = message
        self.error_code: int = error_code
        self.api_error_code: int = api_error_code
        self.extra_data = extra_data
        self.status: int = status

    def __str__(self) -> str:
        return repr(self.message)


class InputError(ArcError):
    '''输入类型错误'''

    def __init__(self, message=None, error_code=108, api_error_code=-100, extra_data=None, status=200) -> None:
        super().__init__(message, error_code, api_error_code, extra_data, status)


class DataExist(ArcError):
    '''数据存在'''

    def __init__(self, message=None, error_code=108, api_error_code=-4, extra_data=None, status=200) -> None:
        super().__init__(message, error_code, api_error_code, extra_data, status)


class NoData(ArcError):
    '''数据不存在'''

    def __init__(self, message=None, error_code=108, api_error_code=-2, extra_data=None, status=200) -> None:
        super().__init__(message, error_code, api_error_code, extra_data, status)


class PostError(ArcError):
    '''缺少输入'''

    def __init__(self, message=None, error_code=108, api_error_code=-100, extra_data=None, status=200) -> None:
        super().__init__(message, error_code, api_error_code, extra_data, status)


class UserBan(ArcError):
    '''用户封禁'''

    def __init__(self, message=None, error_code=121, api_error_code=-202, extra_data=None, status=200) -> None:
        super().__init__(message, error_code, api_error_code, extra_data, status)


class ItemNotEnough(ArcError):
    '''物品数量不足'''

    def __init__(self, message=None, error_code=-6, api_error_code=-999, extra_data=None, status=200) -> None:
        super().__init__(message, error_code, api_error_code, extra_data, status)


class ItemUnavailable(ArcError):
    '''物品不可用'''

    def __init__(self, message=None, error_code=-6, api_error_code=-999, extra_data=None, status=200) -> None:
        super().__init__(message, error_code, api_error_code, extra_data, status)


class RedeemUnavailable(ArcError):
    '''兑换码不可用'''

    def __init__(self, message=None, error_code=505, api_error_code=-999, extra_data=None, status=200) -> None:
        super().__init__(message, error_code, api_error_code, extra_data, status)


class MapLocked(ArcError):
    '''地图锁定'''

    def __init__(self, message=None, error_code=108, api_error_code=-999, extra_data=None, status=200) -> None:
        super().__init__(message, error_code, api_error_code, extra_data, status)


class StaminaNotEnough(ArcError):
    '''体力不足'''

    def __init__(self, message=None, error_code=107, api_error_code=-999, extra_data=None, status=200) -> None:
        super().__init__(message, error_code, api_error_code, extra_data, status)


class TicketNotEnough(ArcError):
    '''记忆源点不足'''

    def __init__(self, message=None, error_code=-6, api_error_code=-999, extra_data=None, status=200) -> None:
        super().__init__(message, error_code, api_error_code, extra_data, status)


class FriendError(ArcError):
    '''好友系统出错'''

    def __init__(self, message=None, error_code=108, api_error_code=-999, extra_data=None, status=200) -> None:
        super().__init__(message, error_code, api_error_code, extra_data, status)


class NoAccess(ArcError):
    '''无权限'''

    def __init__(self, message=None, error_code=108, api_error_code=-999, extra_data=None, status=403) -> None:
        super().__init__(message, error_code, api_error_code, extra_data, status)


class Timeout(ArcError):
    '''超时'''
    pass


class RateLimit(ArcError):
    '''频率达到限制'''

    def __init__(self, message=None, error_code=108, api_error_code=-999, extra_data=None, status=429) -> None:
        super().__init__(message, error_code, api_error_code, extra_data, status)
