class SingyeongException(Exception):
    pass


class InvalidDSN(SingyeongException):
    pass


class UnsupportedEncoding(UserWarning):
    pass


class WSClosed(SingyeongException):
    pass
