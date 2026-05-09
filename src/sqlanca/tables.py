from sqlanca.columns import __MISSING__

from typing import Protocol, Self, Any, ReadOnly, Generator, Callable
from os import PathLike
from contextlib import contextmanager

import sqlite3 as sql


type CollationFn = Callable[[str, str], int]


class Column[T](Protocol):
	name: ReadOnly[str]
	type: ReadOnly[str]
	default: ReadOnly[T]
	collation: ReadOnly[CollationFn | None]

	@property
	def query(self) -> str: ...


class TableConnection:
	def __init__(self, path: str | PathLike[Any], table: Table) -> None:
		self.path = path
		self.table = table

	def __enter__(self) -> Self:
		self.conn = sql.connect(self.path, autocommit=False)
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
		for col in self.table.columns:
			if col.collation is not None:
				self.conn.create_collation(
					f"{col.name}_collation", col.collation
				)
		self.conn.commit()

		with self.__cursor__() as cur:
			cur.execute(self.table.query, self.table.column_defaults)


class Table:
	def __init__(self, name: str, *cols: Column[Any]) -> None:
		self.name = name
		self.columns: tuple[Column[Any], ...] = cols

	def connect(self, path: str | PathLike[Any]) -> TableConnection:
		return TableConnection(path, self)

	@property
	def query(self) -> str:
		return f"CREATE TABLE {self.name} ({", ".join(self.column_queries)})"

	@property
	def column_names(self) -> tuple[str, ...]:
		return tuple(col.name for col in self.columns)

	@property
	def column_queries(self) -> tuple[str, ...]:
		return tuple(col.query for col in self.columns)

	@property
	def column_defaults(self) -> tuple[Any, ...]:
		return tuple(
			col.default
			for col in self.columns
			if col.default is not __MISSING__
		)
