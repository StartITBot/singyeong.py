from abc import ABCMeta, abstractmethod
from typing import Union, List

from .types import VersionType
from .utils import with_type

undefined = object()


class Operator(metaclass=ABCMeta):
    @property
    @abstractmethod
    def key(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def as_dict(self):
        raise NotImplementedError


class ComparisonOperator(Operator, metaclass=ABCMeta):
    def __init__(self, path: str, to: Union[VersionType, str, int, float, list]):
        self.path = path
        self.to = with_type(to)

    def as_dict(self):
        return {
            "path": self.path,
            "op": self.key,
            "to": self.to
        }


class Equal(ComparisonOperator):
    @property
    def key(self):
        return '$eq'


class NotEqual(ComparisonOperator):
    @property
    def key(self):
        return '$ne'


class GreaterThan(ComparisonOperator):
    @property
    def key(self):
        return '$gt'


class GreaterThanEqual(ComparisonOperator):
    @property
    def key(self):
        return '$gte'


class LessThan(ComparisonOperator):
    @property
    def key(self):
        return '$lt'


class LessThanEqual(ComparisonOperator):
    @property
    def key(self):
        return '$lte'


class In(ComparisonOperator):
    @property
    def key(self):
        return '$in'


class Contains(ComparisonOperator):
    @property
    def key(self):
        return '$contains'


class NotContains(ComparisonOperator):
    @property
    def key(self):
        return '$ncontains'


class LogicalOperator(Operator, metaclass=ABCMeta):
    def __init__(self, *args):
        self.args = args

    def as_dict(self):
        return {
            "op": self.key,
            "with": [dict(a) for a in self.args]
        }


class And(LogicalOperator):
    @property
    def key(self):
        return '$and'


class Or(LogicalOperator):
    @property
    def key(self):
        return '$or'


class Nor(LogicalOperator):
    @property
    def key(self):
        return '$nor'


class Selector(metaclass=ABCMeta):
    def __init__(self, name):
        self.name = name

    @property
    @abstractmethod
    def key(self) -> str:
        raise NotImplementedError

    def as_dict(self):
        return {self.key: self.name}


class Minimum(Selector):
    @property
    def key(self):
        return '$min'


class Maximum(Selector):
    @property
    def key(self):
        return '$max'


class Average(Selector):
    @property
    def key(self):
        return '$avg'


class Target:
    def __init__(
            self, *,
            application: str = undefined,
            restricted: bool = undefined,
            key: str = undefined,
            droppable: bool = undefined,
            optional: bool = undefined,
            selector: Selector = undefined,
            operators: List[Operator] = undefined
    ):
        """
        Routing query for finding receiving nodes

        :param application: ID of the application to query against
        :param restricted: Whether or not to allow restricted-mode clients in the query results
        :param key: The key used for consistent-hashing when choosing a client from the output
        :param droppable: Whether or not this payload can be dropped if it isn't routable
        :param optional: Whether or not this query is optional, ie. will be ignored and a client
        will be chosen randomly if it matches nothing.
        :param selector: The selector used. May be null.
        :param operators: The ops used for querying.
        """

        self.application = application
        self.restricted = restricted
        self.key = key
        self.droppable = droppable
        self.optional = optional

        self.selector = selector.as_dict() if isinstance(selector, Selector) else selector
        self.operators = undefined if operators is undefined else [a.as_dict() for a in operators]

    def as_dict(self):
        output = {}

        if self.application is not undefined:
            output['application'] = self.application

        if self.restricted is not undefined:
            output['restricted'] = self.restricted

        if self.key is not undefined:
            output['key'] = self.key

        if self.droppable is not undefined:
            output['droppable'] = self.droppable

        if self.optional is not undefined:
            output['optional'] = self.optional

        if self.operators is not undefined:
            output['ops'] = self.operators

        if self.selector is not undefined:
            output['selector'] = self.selector

        return output

    def __repr__(self):
        return f"<Target {self.as_dict()!r}>"
