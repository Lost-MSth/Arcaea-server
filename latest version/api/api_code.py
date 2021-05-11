def code_get_msg(code):
    # api接口code获取msg，返回字符串
    msg = {
        '0': '',
        '-1': 'See status code',
        '-2': 'No data',
        '-3': 'No data or user',
        '-4': 'No user_id',
        '-101': 'Wrong data type',
        '-102': 'Wrong query parameter',
        '-103': 'Wrong sort parameter',
        '-104': 'Wrong sort order parameter'
    }

    return msg[str(code)]
