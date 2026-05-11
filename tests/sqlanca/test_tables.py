import sqlite3 as sql

import pytest as pt

from sqlanca.columns import Column, ValidationError
from sqlanca.tables import Table


def test_table_create() -> None:
	test_table = Table(
		"test",
		Column("unique_col", "TEXT", not_null=True, unique=True),
		Column("id", "INTEGER", primary_key=True),
	)

	with test_table.connect(":memory:") as conn:
		conn.create()
		with conn.__cursor__() as cur:
			cur.execute(
				"INSERT INTO test (unique_col) VALUES ('bruh'), ('dude'), ('man')"
			)
			cur.execute("SELECT * FROM test")
			out = cur.fetchall()

	assert out == [("bruh", 1), ("dude", 2), ("man", 3)]


def test_table_create_error() -> None:
	test_table = Table(
		"test",
		Column("unique_col", "TEXT", not_null=True, unique=True),
		Column("id", "INTEGER", primary_key=True),
	)

	with test_table.connect(":memory:") as conn:
		conn.create()
		with conn.__cursor__() as cur:
			cur.execute(
				"INSERT INTO test (unique_col) VALUES ('bruh'), ('dude'), ('man')"
			)

			with pt.raises(sql.IntegrityError):
				cur.execute("INSERT INTO test (unique_col) VALUES ('bruh')")

			with pt.raises(sql.IntegrityError):
				cur.execute("INSERT INTO test (unique_col) VALUES (NULL)")


def test_table_insert() -> None:
	test_table = Table(
		"test",
		Column("name", "TEXT", not_null=True),
	)

	with test_table.connect(":memory:") as conn:
		conn.create()

		conn.insert(name="Bob")
		conn.insert(name="Alice")

		with conn.__cursor__() as cur:
			cur.execute("SELECT * FROM test")
			out = cur.fetchall()

	assert out == [("Bob",), ("Alice",)]


def test_table_insert_default() -> None:
	test_table = Table(
		"test",
		Column("name", "TEXT", not_null=True),
		Column("age", "INTEGER", default=None),
	)

	with test_table.connect(":memory:") as conn:
		conn.create()

		conn.insert(name="Bob", age=18)
		conn.insert(name="Alice")

		with conn.__cursor__() as cur:
			cur.execute("SELECT * FROM test")
			out = cur.fetchall()

	assert out == [("Bob", 18), ("Alice", None)]


def test_table_insert_validation_error() -> None:
	def valid_age(x: int) -> bool:
		return x >= 18

	test_table = Table(
		"test",
		Column("name", "TEXT", not_null=True),
		Column("age", "INTEGER", validators=(valid_age,)),
	)

	with test_table.connect(":memory:") as conn:
		conn.create()

		with pt.raises(ValidationError):
			conn.insert(name="Alice", age=16)


def test_table_iter_column() -> None:
	test_table = Table(
		"test",
		Column("id", "INTEGER", primary_key=True),
		Column("name", "TEXT"),
	)

	with test_table.connect(":memory:") as conn:
		conn.create()

		conn.insert(name="Bob")
		conn.insert(name="Alice")

		out1 = tuple(conn.iter_column("name"))
		out2 = tuple(conn.iter_column("id"))

	assert out1 == ("Bob", "Alice")
	assert out2 == (1, 2)


def test_table_iter_column_condition() -> None:
	test_table = Table(
		"test",
		Column("id", "INTEGER", primary_key=True),
		Column("name", "TEXT"),
	)

	with test_table.connect(":memory:") as conn:
		conn.create()

		conn.insert(name="Bob")
		conn.insert(name="Alice")

		out1 = tuple(conn.iter_column("name", lambda s: len(s) == 3))
		out2 = tuple(conn.iter_column("id", lambda x: x % 2 == 0))

	assert out1 == ("Bob",)
	assert out2 == (2,)


def test_table_iter_rows() -> None:
	test_table = Table(
		"test",
		Column("id", "INTEGER", primary_key=True),
		Column("name", "TEXT"),
	)

	with test_table.connect(":memory:") as conn:
		conn.create()

		conn.insert(name="Bob")
		conn.insert(name="Alice")

		out1, out2 = tuple(conn.iter_rows())

	assert out1 == (1, "Bob")
	assert out2 == (2, "Alice")


def test_table_iter_rows_conditions() -> None:
	test_table = Table(
		"test",
		Column("id", "INTEGER", primary_key=True),
		Column("name", "TEXT"),
	)

	with test_table.connect(":memory:") as conn:
		conn.create()

		conn.insert(name="Bob")
		conn.insert(name="Alice")

		out = tuple(conn.iter_rows(id=lambda x: x % 2 == 0))

	assert out[0] == (2, "Alice")
	assert len(out) == 1
