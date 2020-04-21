import hashlib


def file_sha512(file):
    HASH_CHUNK_SIZE = 2 ** 17  # 128KiB - empirical value
    h_sha512 = hashlib.sha512()
    with file.open('rb') as fo:
        chunk = fo.read(HASH_CHUNK_SIZE)
        while chunk:
            h_sha512.update(chunk)
            chunk = fo.read(HASH_CHUNK_SIZE)
    fo.close()
    return h_sha512.digest()