def code_get_msg(code):
    # api接口code获取msg，返回字符串
    msg = {
        '0': '',
        '-1': 'See status code',
        '-2': 'No data',
        '-3': 'No data or user',
        '-4': 'No user_id',
        '-100': 'Wrong post data',
        '-101': 'Wrong data type',
        '-102': 'Wrong query parameter',
        '-103': 'Wrong sort parameter',
        '-104': 'Wrong sort order parameter',
        '-201': 'Wrong username or password',
        '-202': 'User is banned',
        '-999': 'Unknown error'
    }

    return msg[str(code)]
