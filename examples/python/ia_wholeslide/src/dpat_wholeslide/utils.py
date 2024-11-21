"""
Utilities
"""

from functools import partial

import requests

from dpat_wholeslide.version import (
    SECTRA_IA_API_MIN_VERSION,
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
