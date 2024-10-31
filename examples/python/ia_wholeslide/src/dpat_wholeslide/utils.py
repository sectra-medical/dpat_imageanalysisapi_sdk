import os
import fcntl
import time

from functools import reduce, partial

import requests

from dpat_wholeslide.version import (
    __version__,
    SECTRA_IA_API_MIN_VERSION,
    SECTRA_IA_API_MAX_VERSION,
)

def requests_session_from_callbackinfo(callback_info):
    bearer_token = callback_info["token"]
    url = callback_info["url"].rstrip("/") + "/"
    s = requests.Session()
    # uncomment s.verify below if you do not yet have a valid certificate
    # s.verify = False
    s.headers.update({
      'Authorization': f'Bearer {bearer_token}',
      'X-Sectra-ApiVersion': f'{SECTRA_IA_API_MIN_VERSION}',
    })
    def new_request(prefix, f, method, url, *args, **kwargs):
        return f(method, prefix + url, *args, **kwargs)
    s.request = partial(new_request, url, s.request)
    return s

def dig(data, *keys):
     """ safely traverse a nested dictionary """
     for key in keys:
         try:
             data = data[key]
         except (TypeError, KeyError, IndexError):
             return None
     return data

def lock_acquire(lock_file, timeout = 5.0):
    start_time = current_time = time.time()
    pid = os.getpid()
    while current_time < start_time + timeout:
        lock_file_fd = try_acquire(lock_file)
        if lock_file_fd:
            return lock_file_fd
        time.sleep(0.5)
        current_time = time.time()

def lock_try_acquire(lock_file):
    open_mode = os.O_RDWR | os.O_CREAT | os.O_TRUNC
    fd = os.open(lock_file, open_mode)
    lock_file_fd = None
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, OSError):
        pass
    else:
        lock_file_fd = fd

    if lock_file_fd is None:
        os.close(fd)

    return lock_file_fd


def lock_release(lock_file_fd):
    fcntl.flock(lock_file_fd, fcntl.LOCK_UN)
    os.close(lock_file_fd)
    return None
