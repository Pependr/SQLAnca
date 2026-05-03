from sqlanca._internals import get_public_members

from typing import Any, Callable

from enum import Enum
from dataclasses import dataclass


type Validator[T] = Callable[[T], T]


class ColumnError[T](ValueError):
    def __init__(self, col: Column[T], message: str) -> None:
        self.col = col
        super().__init__(message)


class ColType(Enum):
    TEXT = str
    INT = int
    REAL = float
    NULL = None
    BLOB = bytes


@dataclass(slots=True, kw_only=True)
class Column[T]:
    type: ColType
    not_null: bool = True
    primary_key: bool = False
    default: T | None = None
    default_factory: Callable[[], T] | None = None

    def __post_init__(self) -> None:
        if self.default is not None and self.default_factory is not None:
            raise ColumnError(self,
            "A column cannot have both 'default' and 'default_factory' specified at the same time")

        if self.primary_key and self.type is not ColType.INT:
            raise ColumnError(self,
            "A primary key column must be of type INT")


def validates[T](col: str) -> Callable[[Validator[T]], staticmethod[[T], T]]:
    def decorator(fn: Validator[T]) -> staticmethod[[T], T]:
        setattr(fn, "__validator_method__", col)
        return staticmethod(fn)

    return decorator
        

class Table:
    def __init_subclass__(cls, /) -> None:
        cls.__columns__: dict[str, Column[Any]] = {}
        cls.__validators__: dict[str, list[Validator[Any]]] = {}

        for name, member in get_public_members(cls):
            if isinstance(member, Column):
                cls.__columns__[name] = member
            elif hasattr(member, "__validator_method__"):
                col: str = getattr(member, "__validator_method__")
                if col not in cls.__validators__:
                    cls.__validators__[col] = []
                cls.__validators__[col].append(member)

