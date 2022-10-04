from os import urandom
from cryptography.hazmat.primitives.ciphers import (
    Cipher, algorithms, modes
)


def encrypt(key, plaintext, associated_data):
    iv = urandom(12)
    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv, min_tag_length=12),
    ).encryptor()
    encryptor.authenticate_additional_data(associated_data)
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    return (iv, ciphertext, encryptor.tag)


def decrypt(key, associated_data, iv, ciphertext, tag):
    decryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv, tag, min_tag_length=12),
    ).decryptor()
    decryptor.authenticate_additional_data(associated_data)
    return decryptor.update(ciphertext) + decryptor.finalize()
