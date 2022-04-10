class ArcError(Exception):
    api_error_code = -999
    error_code = 108
    message = None

    def __init__(self, message=None, error_code=None, api_error_code=None) -> None:
        self.message = message
        if error_code:
            self.error_code = error_code
        if api_error_code:
            self.api_error_code = api_error_code

    def __str__(self) -> str:
        return repr(self.message)


class InputError(ArcError):
    def __init__(self, message=None, error_code=None, api_error_code=-100) -> None:
        super().__init__(message, error_code, api_error_code)


class DataExist(ArcError):
    pass


class PostError(ArcError):
    def __init__(self, message=None, error_code=None, api_error_code=-100) -> None:
        super().__init__(message, error_code, api_error_code)
