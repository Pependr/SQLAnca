from typing import Callable, Literal
from dataclasses import dataclass, field
from sqlite3 import Connection


type ConflictFn = Callable[[Connection], None]
type CheckFn[T] = Callable[[T], bool]
type CollationResult = Literal[-1] | Literal[0] | Literal[1]
type CollationFn = Callable[[str, str], CollationResult]


@dataclass(frozen=True, slots=True, kw_only=True)
class NotNull:
	conflict_clause: ConflictFn = Connection.rollback
	repr: str = field(default="NOT NULL", init=False)

	def query(self, conn: Connection) -> str:
		return self.repr


@dataclass(frozen=True, slots=True, kw_only=True)
class Unique:
	conflict_clause: ConflictFn = Connection.rollback
	repr: str = field(default="UNIQUE", init=False)

	def query(self, conn: Connection) -> str:
		return self.repr


@dataclass(frozen=True, slots=True, kw_only=True)
class PrimaryKey:
	descending: bool = False
	autoincrement: bool = False
	conflict_clause: ConflictFn = Connection.rollback
	repr: str = field(default="PRIMARY KEY", init=False)

	def query(self, conn: Connection) -> str:
		q: list[str] = self.repr.split()

		if self.descending:
			q.append("DESC")
		else:
			q.append("ASC")

		if self.autoincrement:
			q.append("AUTOINCREMENT")

		return " ".join(q)


@dataclass(frozen=True, slots=True)
class Check[T]:
	check_fn: CheckFn[T]
	conflict_clause: ConflictFn = field(
		default=Connection.rollback, kw_only=True
	)
	repr: str = field(default="CHECK ({}(?))", init=False)

	def query(self, conn: Connection) -> str:
		conn.create_function(self.check_fn.__name__, 1, self.check_fn)
		return self.repr.format(self.check_fn.__name__)


@dataclass(frozen=True, slots=True)
class Default[T]:
	value: T
	repr: str = field(default="DEFAULT (?)", init=False)

	def query(self, conn: Connection) -> str:
		return self.repr


@dataclass(frozen=True, slots=True)
class Collate:
	collation_fn: CollationFn
	repr: str = field(default="COLLATE {}", init=False)

	def query(self, conn: Connection) -> str:
		conn.create_collation(self.collation_fn.__name__, self.collation_fn)
		return self.repr.format(self.collation_fn.__name__)
