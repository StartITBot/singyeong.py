import re
from typing import Optional

from .enums import Encoding
from .exceptions import InvalidDSN

RE_SINGYEONG_DSN = re.compile(r'^(?P<encryption>s)?singyeong:\/\/(?P<login>[^@:]+)(?::(?P<password>[^@]+))?@(?P<host>'
                              r'[\w-]+)(?::(?P<port>\d{1,5}))?\/?(?:\?encoding=(?P<encoding>json|etf|msgpack))?')


class DSN:
    __slots__ = ('encryption', 'login', 'password', 'host', 'port', 'encoding',)

    encryption: bool
    login: str
    password: Optional[str]
    host: str
    port: int
    encoding: Encoding

    def __init__(self, dsn):
        if isinstance(dsn, DSN):
            self.encryption = dsn.encryption
            self.login = dsn.login
            self.password = dsn.password
            self.host = dsn.host
            self.port = dsn.port
            self.encoding = dsn.encoding
            return

        match = RE_SINGYEONG_DSN.fullmatch(dsn)
        if not match:
            raise InvalidDSN()

        group = match.groupdict()
        self.encryption = bool(group['encryption'])
        self.login = group['login']
        self.password = group['password']
        self.host = group['host']
        self.port = int(group['port'] or 80)
        self.encoding = Encoding(group['encoding'] or "json")

    def __str__(self):
        parts = []
        parts.append(f"{'s' if self.encryption else ''}singyeong://")
        parts.append(self.login)
        if self.password:
            parts.append(":")
            parts.append(self.password)
        parts.append("@")
        parts.append(self.host)
        if self.port != 80:
            parts.append(":")
            parts.append(str(self.port))
        if self.encoding != Encoding.JSON:
            parts.append("/?encoding=")
            parts.append(self.encoding.value)
        return ''.join(parts)
