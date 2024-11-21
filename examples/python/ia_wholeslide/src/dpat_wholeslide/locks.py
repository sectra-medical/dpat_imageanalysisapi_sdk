"""
module for flock-based locks (work on POSIX filesystems through the Linux kernel)
"""

import os
import time
import fcntl

def lock_acquire(lock_file, timeout = 5.0):
    start_time = current_time = time.time()
    while current_time < start_time + timeout:
        lock_file_fd = lock_try_acquire(lock_file)
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
