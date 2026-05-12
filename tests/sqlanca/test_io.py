from typing import Any, Generator

import pytest as pt

from sqlanca.io import Connection


@pt.fixture
def conn() -> Generator[Connection, None, None]:
	with Connection(":memory:") as conn:
		yield conn


@pt.fixture
def example_conn(conn: Connection) -> Generator[Connection, None, None]:
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

	yield conn


def test_conn_create(conn: Connection) -> None:
	class MockCreateable:
		@property
		def create_query(self) -> str:
			return "CREATE TABLE test (name TEXT)"

	conn.create(MockCreateable())

	with conn.__cursor__() as cur:
		cur.execute(
			"""SELECT name FROM sqlite_master
			WHERE type='table' AND name='test'"""
		)

		out = cur.fetchone()[0]

	assert out == "test"


def test_conn_insert(conn: Connection) -> None:
	class MockInsertable:
		def insert_query(
			self, inputs: dict[str, Any]
		) -> tuple[str, tuple[Any, ...]]:
			return (
				"INSERT INTO test (name, surname) VALUES (?, ?)",
				("Linus", "Torvalds"),
			)

	with conn.__cursor__() as cur:
		cur.execute("CREATE TABLE test (name TEXT, surname TEXT)")

		conn.insert(MockInsertable())

		cur.execute("SELECT * FROM test")

		out = cur.fetchone()

	assert out == ("Linus", "Torvalds")


def test_conn_iter_column(example_conn: Connection) -> None:
	out = tuple(example_conn.iter_column("test", "language"))

	assert out == ("C", "Python", "TypeScript")


def test_conn_filter_column(example_conn: Connection) -> None:
	out = tuple(
		example_conn.filter_column("test", "name", lambda n: len(n) <= 5)
	)

	assert out == ("Linus", "Bill")


def test_conn_iter_rows(example_conn: Connection) -> None:
	out = tuple(example_conn.iter_rows("test"))

	assert out == (
		("Linus", "Torvalds", "C"),
		("Anthony", "Gooseling", "Python"),
		("Bill", "Gates", "TypeScript"),
	)


def test_conn_filter_rows(example_conn: Connection) -> None:
	def is_compiled(language: str) -> bool:
		return language in ("Rust", "C", "Go")

	out = tuple(example_conn.filter_rows("test", language=is_compiled))

	assert out == (("Linus", "Torvalds", "C"),)
