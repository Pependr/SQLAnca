from dataclasses import dataclass
from sqlite3 import Connection
from typing import Callable

type ConflictFn = Callable[[Connection], None]


@dataclass(frozen=True, slots=True, kw_only=True)
class NotNull:
	conflict_clause: ConflictFn = Connection.rollback

	@property
	def query(self) -> str:
		return "NOT NULL"


@dataclass(frozen=True, slots=True, kw_only=True)
class Unique:
	conflict_clause: ConflictFn = Connection.rollback

	@property
	def query(self) -> str:
		return "UNIQUE"


@dataclass(frozen=True, slots=True, kw_only=True)
class PrimaryKey:
	descending: bool = False
	autoincrement: bool = False
	conflict_clause: ConflictFn = Connection.rollback

	@property
	def query(self) -> str:
		q: list[str] = ["PRIMARY", "KEY"]

		if self.descending:
			q.append("DESC")
		else:
			q.append("ASC")

		if self.autoincrement:
			q.append("AUTOINCREMENT")

		return " ".join(q)
