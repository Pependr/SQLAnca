from dataclasses import dataclass
from enum import StrEnum
from typing import Callable, Generator


class ColType(StrEnum):
	TEXT = "TEXT"
	INT = "INT"
	REAL = "REAL"
	NULL = "NULL"
	BLOB = "BLOB"


class PrimKey(StrEnum):
	ASC = "ASC"
	DESC = "DESC"


@dataclass(init=False, slots=True)
class Column[T]:
	type: ColType
	primary_key: PrimKey | None = None
	unique: bool = False
	null: bool = False
	default: T | None = None
	default_factory: Callable[[], T]
	generated: Generator[T, None, None]
