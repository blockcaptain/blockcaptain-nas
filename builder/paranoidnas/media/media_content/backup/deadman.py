import urllib3
import contextlib
from traceback import format_exception

_http = urllib3.PoolManager()
_endpoint = "https://hc-ping.com/"


class Deadman(contextlib.AbstractContextManager):
    def __init__(self, guid):
        self._guid = guid

    def __enter__(self) -> None:
        self._ping("/start")

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type is None:
            self._ping("")
        else:
            self._ping("/fail", "".join(format_exception(exc_type, exc_value, traceback)))

    def _ping(self, suffix: str, message: str = None):
        _http.request("POST", f"{_endpoint}{self._guid}{suffix}", body=message, timeout=5.0)
