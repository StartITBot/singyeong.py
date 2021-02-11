from enum import IntEnum, Enum


class OpCode(IntEnum):
    HELLO = 0
    IDENTIFY = 1
    READY = 2
    INVALID = 3
    DISPATCH = 4
    HEARTBEAT = 5
    HEARTBEAT_ACK = 6
    GOODBYE = 7
    ERROR = 8


class Encoding(Enum):
    JSON = "json"
    ETF = "etf"
    MSGPACK = "msgpack"
