import sqlite3 as sql
from contextlib import contextmanager
from os import PathLike
from typing import Any, Callable, Generator, Protocol, Self

from sqlanca.__internals__ import __MISSING__

type ValidatorFn[T] = Callable[[T], bool]


class Column[T](Protocol):
	@property
	def name(self) -> str: ...

	@property
	def default(self) -> T: ...

	@property
	def query(self) -> str: ...

	def validate(self, value: T) -> T: ...


class AnyTable(Protocol):
	name: str
	columns: tuple[Column[Any], ...]

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

	def insert(self, **kwargs: Any) -> None:
		inputs: dict[str, Any] = {}

		for col in self.table.columns:
			if col.name not in kwargs:
				if col.default is not __MISSING__:
					inputs[col.name] = col.default
				continue

			inputs[col.name] = col.validate(kwargs[col.name])

		with self.__cursor__() as cur:
			cur.execute(
				f"""INSERT INTO {self.table.name} ({", ".join(inputs.keys())})
				VALUES ({", ".join("?" for _ in inputs)})""".replace("\n", " "),
				tuple(inputs.values()),
			)

	def iter_column(
		self, col_name: str, *conditions: Callable[[Any], bool]
	) -> Generator[Any, None, None]:
		with self.__cursor__() as cur:
			cur.execute(f"SELECT {col_name} FROM {self.table.name}")
			while out := cur.fetchone():
				for condition in conditions:
					if not condition(out[0]):
						break
				else:
					yield out[0]


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
