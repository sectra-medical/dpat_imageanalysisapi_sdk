import logging
import time
from functools import wraps
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)


def connection_retry():
    """Decorator used to retry requests if connection cannot be established."""

    def decorator(fn):
        @wraps(fn)
        def _request(*args, **kwargs):
            trial = 1
            while trial < 5:
                try:
                    return fn(*args, **kwargs)
                except ConnectionError:
                    delay = 2**trial
                    logger.warning(
                        "IDS7 connection error trial %s/5, retrying in %ss",
                        trial,
                        delay,
                    )
                    trial += 1
                    time.sleep(delay)
            logger.error("Request failed after 5 trials")
            raise ConnectionError()

        return _request

    return decorator


JSONPayload = Union[List[Dict[str, Any]], Dict[str, Any]]
