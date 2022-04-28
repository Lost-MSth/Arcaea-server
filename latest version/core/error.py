class ArcError(Exception):
    api_error_code = -999
    error_code = 108
    message = None
    extra_data = None

    def __init__(self, message=None, error_code=None, api_error_code=None, extra_data=None) -> None:
        self.message = message
        if error_code:
            self.error_code = error_code
        if api_error_code:
            self.api_error_code = api_error_code
        if extra_data:
            self.extra_data = extra_data

    def __str__(self) -> str:
        return repr(self.message)


class InputError(ArcError):
    # 输入类型错误
    def __init__(self, message=None, error_code=None, api_error_code=-100, extra_data=None) -> None:
        super().__init__(message, error_code, api_error_code, extra_data)


class DataExist(ArcError):
    # 数据存在
    pass


class NoData(ArcError):
    # 数据不存在
    def __init__(self, message=None, error_code=None, api_error_code=-2, extra_data=None) -> None:
        super().__init__(message, error_code, api_error_code, extra_data)


class PostError(ArcError):
    # 缺少输入
    def __init__(self, message=None, error_code=None, api_error_code=-100, extra_data=None) -> None:
        super().__init__(message, error_code, api_error_code, extra_data)


class UserBan(ArcError):
    # 用户封禁
    def __init__(self, message=None, error_code=121, api_error_code=None, extra_data=None) -> None:
        super().__init__(message, error_code, api_error_code, extra_data)


class NoAccess(ArcError):
    # 无权限
    pass
