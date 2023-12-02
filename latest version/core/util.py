import hashlib
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from datetime import date
from time import mktime


def aes_gcm_128_encrypt(key, plaintext, associated_data):
    iv = os.urandom(12)
    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv, min_tag_length=12),
    ).encryptor()
    encryptor.authenticate_additional_data(associated_data)
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    return (iv, ciphertext, encryptor.tag)


def aes_gcm_128_decrypt(key, associated_data, iv, ciphertext, tag):
    decryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv, tag, min_tag_length=12),
    ).decryptor()
    decryptor.authenticate_additional_data(associated_data)
    return decryptor.update(ciphertext) + decryptor.finalize()


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


def get_today_timestamp():
    '''相对于本机本地时间的今天0点的时间戳'''
    return int(mktime(date.today().timetuple()))
