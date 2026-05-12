import sqlite3 as sql
from contextlib import ExitStack, contextmanager
from os import PathLike
from typing import Any, Callable, Generator, Protocol, Self

type PredicateFn = Callable[[Any], bool]


def compose(*predicates: PredicateFn) -> PredicateFn:
	def predicate(value: Any) -> bool:
		for pr in predicates:
			if not pr(value):
				return False
		return True

	return predicate


class Creatable(Protocol):
	@property
	def create_query(self) -> str: ...


class Insertable(Protocol):
	def insert_query(
		self, inputs: dict[str, Any]
	) -> tuple[str, tuple[Any, ...]]: ...


class Connection:
	def __init__(self, path: str | PathLike[Any]) -> None:
		self.__path__ = path

	def __enter__(self) -> Self:
		self.__conn__ = sql.connect(self.__path__, autocommit=False)
		return self

	def __exit__(
		self,
		exc_type: type[Exception] | None,
		exc: Exception | None,
		tb: Any,
	) -> None:
		if exc is not None:
			self.__conn__.rollback()
		else:
			self.__conn__.commit()
		self.__conn__.close()

	@contextmanager
	def __cursor__(self) -> Generator[sql.Cursor, None, None]:
		cur = self.__conn__.cursor()
		yield cur
		cur.close()

	@contextmanager
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

	def iter_column(
		self,
		table_name: str,
		col_name: str,
		predicate: PredicateFn = lambda _: True,
	) -> Generator[Any, None, None]:
		with self.__func__(predicate, f"{col_name}_pred"):
			with self.__cursor__() as cur:
				cur.execute(
					f"""SELECT {col_name} FROM {table_name}
					WHERE {col_name}_pred({col_name})=1"""
				)

				yield from (i[0] for i in cur.fetchall())

	def iter_rows(
		self, table_name: str, **predicates: PredicateFn
	) -> Generator[tuple[Any, ...], None, None]:
		if predicates == {}:
			with self.__cursor__() as cur:
				cur.execute(f"SELECT * FROM {table_name}")
				yield from cur.fetchall()
				return

		with ExitStack() as stack:
			for col, fn in predicates.items():
				stack.enter_context(self.__func__(fn, f"{col}_pred"))

			with self.__cursor__() as cur:
				cur.execute(
					f"""
					SELECT * FROM {table_name}
					WHERE {" AND ".join(f"{col}_pred({col})" for col in predicates)}
					"""
				)

				yield from cur.fetchall()
