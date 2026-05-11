from typing import Any, Sized

from sqlanca.io import Connection


def test_conn_create() -> None:
	class MockCreateable:
		@property
		def create_query(self) -> str:
			return "CREATE TABLE test (name TEXT)"

	with Connection(":memory:") as conn:
		conn.create(MockCreateable())

		with conn.__cursor__() as cur:
			cur.execute(
				"""SELECT name FROM sqlite_master
				WHERE type='table' AND name='test'"""
			)

			out = cur.fetchone()[0]

	assert out == "test"


def test_conn_insert() -> None:
	class MockInsertable:
		def insert_query(
			self, inputs: dict[str, Any]
		) -> tuple[str, tuple[Any, ...]]:
			return (
				"INSERT INTO test (name, surname) VALUES (?, ?)",
				("Linus", "Torvalds"),
			)

	with Connection(":memory:") as conn:
		with conn.__cursor__() as cur:
			cur.execute("CREATE TABLE test (name TEXT, surname TEXT)")

		conn.insert(MockInsertable())

		with conn.__cursor__() as cur:
			cur.execute("SELECT * FROM test")

			out = cur.fetchone()

	assert out == ("Linus", "Torvalds")


def test_conn_iter_column() -> None:
	class MockSelectable:
		def get_col_pos(self, col_name: str) -> int:
			return 0

		def select_col(self, col_name: str) -> str:
			return "SELECT name FROM test"

		@property
		def select_all(self) -> str:
			return "SELECT * FROM test"

	def len_over_3(x: Sized) -> bool:
		return len(x) > 3

	with Connection(":memory:") as conn:
		with conn.__cursor__() as cur:
			cur.execute("CREATE TABLE test (name TEXT)")
			cur.execute("INSERT INTO test (name) VALUES ('Bruh')")
			cur.execute("INSERT INTO test (name) VALUES ('Dude')")
			cur.execute("INSERT INTO test (name) VALUES ('Man')")

		out1 = tuple(conn.iter_column(MockSelectable(), "name"))
		out2 = tuple(conn.iter_column(MockSelectable(), "name", len_over_3))

	assert out1 == ("Bruh", "Dude", "Man")
	assert out2 == ("Bruh", "Dude")


def test_conn_iter_rows() -> None:
	class MockSelectable:
		cols: tuple[str, ...] = ("name", "surname", "language")

		def get_col_pos(self, col_name: str) -> int:
			return self.cols.index(col_name)

		def select_col(self, col_name: str) -> str:
			return f"SELECT {col_name} FROM test"

		@property
		def select_all(self) -> str:
			return "SELECT * FROM test"

	def is_compiled(language: str) -> bool:
		return language in ("Rust", "C", "Go")

	with Connection(":memory:") as conn:
		with conn.__cursor__() as cur:
			cur.execute(
				"CREATE TABLE test (name TEXT, surname TEXT, language TEXT)"
			)
			cur.execute(
				"INSERT INTO test (name, surname, language) VALUES (?, ?, ?)",
				("Linus", "Torvalds", "C"),
			)
			cur.execute(
				"INSERT INTO test (name, surname, language) VALUES (?, ?, ?)",
				("Anthony", "Gooseling", "Python"),
			)
			cur.execute(
				"INSERT INTO test (name, surname, language) VALUES (?, ?, ?)",
				("Bill", "Gates", "TypeScript"),
			)

		out1 = tuple(conn.iter_rows(MockSelectable()))
		out2 = tuple(conn.iter_rows(MockSelectable(), language=is_compiled))

	assert out1 == (
		("Linus", "Torvalds", "C"),
		("Anthony", "Gooseling", "Python"),
		("Bill", "Gates", "TypeScript"),
	)
	assert out2 == (("Linus", "Torvalds", "C"),)
