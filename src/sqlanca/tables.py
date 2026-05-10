from typing import Protocol, Self, Any, Generator
from os import PathLike
from contextlib import contextmanager

import sqlite3 as sql


class Column(Protocol):
	@property
	def name(self) -> str: ...

	@property
	def query(self) -> str: ...


class AnyTable(Protocol):
	columns: tuple[Column, ...]

	@property
	def query(self) -> str: ...


class TableConnection:
	def __init__(self, path: str | PathLike[Any], table: AnyTable) -> None:
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
		with self.__cursor__() as cur:
			cur.execute(self.table.query)


class Table:
	def __init__(self, name: str, *cols: Column) -> None:
		self.name = name
		self.columns: tuple[Column, ...] = cols

	def connect(self, path: str | PathLike[Any]) -> TableConnection:
		return TableConnection(path, self)

	@property
	def column_queries(self) -> tuple[str, ...]:
		return tuple(col.query for col in self.columns)

	@property
	def query(self) -> str:
		return f"CREATE TABLE {self.name} ({", ".join(self.column_queries)})"
