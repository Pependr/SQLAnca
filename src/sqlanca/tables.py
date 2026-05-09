from typing import Protocol, Self, Any, Generator, Callable
from os import PathLike
from contextlib import contextmanager

import sqlite3 as sql


type CollationFn = Callable[[str, str], int]


class Column[T](Protocol):
	name: str
	type: str
	collation: CollationFn | None = None

	@property
	def query(self) -> str: ...


class AnyTable(Protocol):
	columns: tuple[Column[Any], ...]

	@property
	def query(self) -> str: ...


class TableConnection:
	def __init__(self, path: str | PathLike[Any], table: AnyTable) -> None:
		self.path = path
		self.table = table

	def __enter__(self) -> Self:
		self.conn = sql.connect(self.path, autocommit=False)

		for col in self.table.columns:
			if col.collation is not None:
				self.conn.create_collation(
					f"{col.name}_collation", col.collation
				)

		return self

	def __exit__(
		self,
		exc_type: type[Exception] | None,
		exc: Exception | None,
		tb: Any,
	) -> None:
		if exc is not None:
			self.conn.rollback()
		else:
			self.conn.commit()
		self.conn.close()

	@contextmanager
	def __cursor__(self) -> Generator[sql.Cursor, None, None]:
		cur = self.conn.cursor()
		yield cur
		cur.close()

	def create(self) -> None:
		with self.__cursor__() as cur:
			cur.execute(self.table.query)


class Table:
	def __init__(self, name: str, *cols: Column[Any]) -> None:
		self.name = name
		self.columns: tuple[Column[Any], ...] = cols

	def connect(self, path: str | PathLike[Any]) -> TableConnection:
		return TableConnection(path, self)

	@property
	def column_queries(self) -> tuple[str, ...]:
		return tuple(col.query for col in self.columns)

	@property
	def query(self) -> str:
		return f"CREATE TABLE {self.name} ({", ".join(self.column_queries)})"
