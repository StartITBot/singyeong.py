import urllib.parse
from typing import Optional

from .enums import Encoding
from .exceptions import InvalidDSN


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

        match: urllib.parse.ParseResult = urllib.parse.urlparse(dsn)
        if match.scheme not in ("singyeong", "ssingyeong"):
            raise InvalidDSN('unknown url type: %s' % match.scheme)

        self.encryption = match.scheme == "ssingyeong"
        self.login = match.username
        self.password = match.password
        self.host = match.hostname
        self.port = match.port or (443 if self.encryption else 80)
        query = urllib.parse.parse_qs(match.query)
        self.encoding = Encoding(query.get("encoding", ['json'])[0])

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
