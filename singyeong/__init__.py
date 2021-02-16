__title__ = 'singyeong'
__author__ = 'StartIT'
__license__ = 'MIT'
__copyright__ = 'Copyright (c) 2021 StartIT'
__version__ = '1.0.1'

__path__ = __import__('pkgutil').extend_path(__path__, __name__)

from collections import namedtuple

from .client import Client
from .query import VersionType, Equal, NotEqual, GreaterThan, GreaterThanEqual, LessThan, LessThanEqual, \
    In, Contains, NotContains, And, Or, Nor, Minimum, Maximum, Average, Target
from .message import Message

VersionInfo = namedtuple('VersionInfo', 'major minor micro releaselevel serial')

version_info = VersionInfo(major=1, minor=0, micro=1, releaselevel='alpha', serial=0)
