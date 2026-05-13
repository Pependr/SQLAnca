import os
import sqlite3 as sql
import contextlib as cl

import types as ts

from typing import Any, Self, Callable, Protocol, Generator


type PredicateFn = Callable[[Any], bool]


class Creatable(Protocol):
	@property
	def create_query(self) -> str: ...


class Insertable(Protocol):
	def insert_query(
		self, inputs: dict[str, Any]
	) -> tuple[str, tuple[Any, ...]]: ...


class Connection:
	def __init__(self, path: str | os.PathLike[Any]) -> None:
		self.__path__ = path

	def __enter__(self) -> Self:
		self.__conn__ = sql.connect(self.__path__, autocommit=False)
		return self

	def __exit__(
		self,
		exc_type: type[BaseException] | None,
		exc_value: BaseException | None,
		traceback: ts.TracebackType | None,
		/,
	) -> None:
		if exc_value is not None:
			self.__conn__.rollback()
		else:
			self.__conn__.commit()
		self.__conn__.close()

	@cl.contextmanager
	def __cursor__(self) -> Generator[sql.Cursor, None, None]:
		cur = self.__conn__.cursor()
		yield cur
		cur.close()

	@cl.contextmanager
	def __func__(
		self, fn: Callable[[Any], Any], name: str
	) -> Generator[None, None, None]:
		self.__conn__.create_function(name, 1, fn)
		yield
		self.__conn__.create_function(name, 1, None)

	def create(self, table: Creatable) -> None:
		with self.__cursor__() as cur:
			cur.execute(table.create_query)

	def insert(self, table: Insertable, **kwargs: Any) -> None:
		with self.__cursor__() as cur:
			cur.execute(*table.insert_query(kwargs))

	def iter_column(self, table_name: str, col_name: str) -> tuple[Any, ...]:
		with self.__cursor__() as cur:
			cur.execute(f"SELECT {col_name} FROM {table_name}")
			return tuple(i[0] for i in cur.fetchall())

	def filter_column(
		self, table_name: str, col_name: str, predicate: PredicateFn
	) -> tuple[Any, ...]:
		with cl.ExitStack() as stack:
			stack.enter_context(self.__func__(predicate, f"{col_name}_pred"))

			cur = stack.enter_context(self.__cursor__())

			cur.execute(
				f"""SELECT {col_name} FROM {table_name}
				WHERE {col_name}_pred({col_name})=1"""
			)

			return tuple(i[0] for i in cur.fetchall())

	def iter_rows(self, table_name: str) -> tuple[tuple[Any, ...], ...]:
		with self.__cursor__() as cur:
			cur.execute(f"SELECT * FROM {table_name}")
			return tuple(cur.fetchall())

	def filter_rows(
		self, table_name: str, **predicates: PredicateFn
	) -> tuple[tuple[Any, ...], ...]:
		if predicates == {}:
			raise ValueError("No filters provided")

		with cl.ExitStack() as stack:
			for col, fn in predicates.items():
				stack.enter_context(self.__func__(fn, f"{col}_pred"))

			cur = stack.enter_context(self.__cursor__())

			cur.execute(
				f"""
				SELECT * FROM {table_name}
				WHERE {" AND ".join(f"{col}_pred({col})" for col in predicates)}
				"""
			)

			return tuple(cur.fetchall())
