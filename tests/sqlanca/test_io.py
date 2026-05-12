from typing import Any, Sized

import pytest as pt

from sqlanca.io import Connection


@pt.fixture
def conn() -> Connection:
	return Connection(":memory:")


def test_conn_create(conn: Connection) -> None:
	class MockCreateable:
		@property
		def create_query(self) -> str:
			return "CREATE TABLE test (name TEXT)"

	with conn:
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

	with conn:
		with conn.__cursor__() as cur:
			cur.execute("CREATE TABLE test (name TEXT, surname TEXT)")

		conn.insert(MockInsertable())

		with conn.__cursor__() as cur:
			cur.execute("SELECT * FROM test")

			out = cur.fetchone()

	assert out == ("Linus", "Torvalds")


def test_conn_iter_column(conn: Connection) -> None:
	def len_over_3(x: Sized) -> bool:
		return len(x) > 3

	with conn:
		with conn.__cursor__() as cur:
			cur.execute("CREATE TABLE test (name TEXT)")
			cur.execute("INSERT INTO test (name) VALUES ('Bruh')")
			cur.execute("INSERT INTO test (name) VALUES ('Dude')")
			cur.execute("INSERT INTO test (name) VALUES ('Man')")

		out1 = tuple(conn.iter_column("test", "name"))
		out2 = tuple(conn.iter_column("test", "name", len_over_3))

	assert out1 == ("Bruh", "Dude", "Man")
	assert out2 == ("Bruh", "Dude")


def test_conn_iter_rows(conn: Connection) -> None:
	def is_compiled(language: str) -> bool:
		return language in ("Rust", "C", "Go")

	with conn:
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

		out1 = tuple(conn.iter_rows("test"))
		out2 = tuple(conn.iter_rows("test", language=is_compiled))

	assert out1 == (
		("Linus", "Torvalds", "C"),
		("Anthony", "Gooseling", "Python"),
		("Bill", "Gates", "TypeScript"),
	)
	assert out2 == (("Linus", "Torvalds", "C"),)
