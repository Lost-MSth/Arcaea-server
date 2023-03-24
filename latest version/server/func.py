from functools import wraps
from traceback import format_exc

from flask import current_app, g, jsonify

from core.config_manager import Config
from core.error import ArcError, NoAccess

has_arc_hash = False
try:
    from core.arc_crypto import ArcHashChecker  # type: ignore
    has_arc_hash = True
except ModuleNotFoundError:
    pass

default_error = ArcError('Unknown Error', status=500)


def error_return(e: ArcError = default_error):  # 错误返回
    # -7 处理交易时发生了错误
    # -5 所有的曲目都已经下载完毕
    # -4 您的账号已在别处登录
    # -3 无法连接至服务器
    # 2 Arcaea服务器正在维护
    # 9 新版本请等待几分钟
    # 100 无法在此ip地址下登录游戏
    # 101 用户名占用
    # 102 电子邮箱已注册
    # 103 已有一个账号由此设备创建
    # 104 用户名密码错误
    # 105 24小时内登入两台设备
    # 106 121 账户冻结
    # 107 你没有足够的体力
    # 113 活动已结束
    # 114 该活动已结束，您的成绩不会提交
    # 115 请输入有效的电子邮箱地址
    # 120 封号警告
    # 122 账户暂时冻结
    # 123 账户被限制
    # 124 你今天不能再使用这个IP地址创建新的账号
    # 150 非常抱歉您已被限制使用此功能
    # 151 目前无法使用此功能
    # 160 账户未邮箱认证，请检查邮箱
    # 161  账户认证过期，请重新注册
    # 401 用户不存在
    # 403 无法连接至服务器
    # 501 502 -6 此物品目前无法获取
    # 504 无效的序列码
    # 505 此序列码已被使用
    # 506 你已拥有了此物品
    # 601 好友列表已满
    # 602 此用户已是好友
    # 604 你不能加自己为好友
    # 903 下载量超过了限制，请24小时后重试
    # 905 请在再次使用此功能前等待24小时
    # 910 重新请求验证邮件前需等待x分钟 extra: retry_at
    # 1001 设备数量达到上限
    # 1002 此设备已使用过此功能
    # 1201 房间已满
    # 1202 房间号码无效
    # 1203 请将Arcaea更新至最新版本
    # 1205 此房间目前无法加入
    # 9801 下载歌曲时发生问题，请再试一次
    # 9802 保存歌曲时发生问题，请检查设备空间容量
    # 9803 下载已取消
    # 9905 没有在云端发现任何数据
    # 9907 更新数据时发生了问题
    # 9908 服务器只支持最新的版本，请更新Arcaea
    # 其它 发生未知错误
    r = {"success": False, "error_code": e.error_code}
    if e.extra_data:
        r['extra'] = e.extra_data

    return jsonify(r), e.status


def success_return(value=None):
    r = {"success": True}
    if value is not None:
        r['value'] = value
    return jsonify(r)


def arc_try(view):
    '''替代try/except，记录`ArcError`为warning'''
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        try:
            data = view(*args, **kwargs)
            if data is None:
                return error_return()
            return data
        except ArcError as e:
            if Config.ALLOW_WARNING_LOG:
                current_app.logger.warning(format_exc())
            user = g.get("user", None)
            current_app.logger.warning(
                f'{user.user_id if user is not None else ""} - {e.error_code}|{e.api_error_code}: {e}')
            return error_return(e)

    return wrapped_view


def header_check(request) -> ArcError:
    '''检查请求头是否合法'''
    headers = request.headers
    if Config.ALLOW_APPVERSION:  # 版本检查
        if 'AppVersion' not in headers or headers['AppVersion'] not in Config.ALLOW_APPVERSION:
            return NoAccess('Invalid app version', 1203)

    if has_arc_hash and not ArcHashChecker(request).check():
        return NoAccess('Invalid request')

    return None
