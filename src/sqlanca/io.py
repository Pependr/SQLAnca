import sqlite3 as sql
from contextlib import contextmanager
from os import PathLike
from typing import Any, Callable, Generator, Protocol, Self


class AnyTable(Protocol):
	name: str

	@property
	def create_query(self) -> str: ...

	def insert_query(
		self, inputs: dict[str, Any]
	) -> tuple[str, tuple[Any]]: ...

	def get_col_pos(self, col_name: str) -> int: ...

	def select_col(self, col_name: str) -> str: ...

	@property
	def select_all(self) -> str: ...


class Connection:
	def __init__(self, path: str | PathLike[Any]) -> None:
		self.path = path

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

	def create(self, table: AnyTable) -> None:
		with self.__cursor__() as cur:
			cur.execute(table.create_query)

	def insert(self, table: AnyTable, **kwargs: Any) -> None:
		with self.__cursor__() as cur:
			cur.execute(*table.insert_query(kwargs))

	def iter_column(
		self, table: AnyTable, col_name: str, *conditions: Callable[[Any], bool]
	) -> Generator[Any, None, None]:
		with self.__cursor__() as cur:
			cur.execute(table.select_col(col_name))
			while out := cur.fetchone():
				for condition in conditions:
					if not condition(out[0]):
						break
				else:
					yield out[0]

	def iter_rows(
		self, table: AnyTable, **col_conditions: Callable[[Any], bool]
	) -> Generator[tuple[Any, ...], None, None]:
		with self.__cursor__() as cur:
			cur.execute(table.select_all)
			while out := cur.fetchone():
				for col, cond in col_conditions.items():
					i = table.get_col_pos(col)
					if not cond(out[i]):
						break
				else:
					yield out
