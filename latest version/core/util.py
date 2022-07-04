import hashlib
import os


def md5(code):
    # md5加密算法
    code = code.encode()
    md5s = hashlib.md5()
    md5s.update(code)
    codes = md5s.hexdigest()

    return codes


def get_file_md5(file_path):
    # 计算文件MD5
    if not os.path.isfile(file_path):
        return None
    myhash = hashlib.md5()
    with open(file_path, 'rb') as f:
        while True:
            b = f.read(8096)
            if not b:
                break
            myhash.update(b)

    return myhash.hexdigest()
