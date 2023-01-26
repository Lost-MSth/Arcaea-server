import hashlib
import os


def md5(code: str) -> str:
    # md5加密算法
    code = code.encode()
    md5s = hashlib.md5()
    md5s.update(code)
    codes = md5s.hexdigest()

    return codes


def get_file_md5(file_path: str) -> str:
    '''计算文件MD5，假设是文件'''
    myhash = hashlib.md5()
    with open(file_path, 'rb') as f:
        while True:
            b = f.read(8192)
            if not b:
                break
            myhash.update(b)

    return myhash.hexdigest()


def try_rename(path: str, new_path: str) -> str:
    '''尝试重命名文件，并尝试避免命名冲突（在后面加自增数字），返回最终路径'''
    final_path = new_path
    if os.path.exists(new_path):
        i = 1
        while os.path.exists(new_path + str(i)):
            i += 1

        final_path = new_path + str(i)

    os.rename(path, final_path)
    return final_path
