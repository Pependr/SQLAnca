from typing import Protocol, Any, Self

import sqlite3 as sql


class Column(Protocol):
	name: str
	type: str

	def assemble(self, conn: sql.Connection) -> tuple[str, list[Any]]: ...


class TableConnection:
	def __init__(self, path: str) -> None:
		self.path = path

	def __enter__(self) -> Self:
		self.conn = sql.connect(self.path, autocommit=False)
		return self

	def __exit__(
		self, exc_type: type[Exception] | None, exc: Exception | None, tb: None
	) -> None:
		if exc is not None:
			self.conn.rollback()
		else:
			self.conn.commit()
		self.conn.close()


class Table:
	def __init__(self, name: str) -> None:
		self.name = name
		self.columns: dict[str, Column] = {}

	def add_col(self, col: Column) -> Self:
		self.columns[col.name] = col
		return self

	def connect(self, path: str) -> TableConnection:
		return TableConnection(path)
