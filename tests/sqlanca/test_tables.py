import sqlite3 as sql

import pytest as pt

from sqlanca.columns import Column, Type, ValidationError
from sqlanca.io import Connection
from sqlanca.tables import Table


def test_table_create() -> None:
	test_table = Table(
		"test",
		Column("unique_col", Type.STR, not_null=True, unique=True),
		Column("id", Type.INT, primary_key=True),
	)

	with Connection(":memory:") as conn:
		conn.create(test_table)
		with conn.__cursor__() as cur:
			cur.execute(
				"INSERT INTO test (unique_col) VALUES ('bruh'), ('dude'), ('man')"
			)
			cur.execute("SELECT * FROM test")
			out = cur.fetchall()

	assert out == [("bruh", 1), ("dude", 2), ("man", 3)]


def test_table_constraints() -> None:
	test_table = Table(
		"test",
		Column("unique_col", Type.STR, not_null=True, unique=True),
	)

	with Connection(":memory:") as conn:
		conn.create(test_table)
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
		Column("name", Type.STR, not_null=True),
		Column("age", Type.INT, default=None),
	)

	with Connection(":memory:") as conn:
		conn.create(test_table)

		conn.insert(test_table, name="Bob", age=18)
		conn.insert(test_table, name="Alice")

		with conn.__cursor__() as cur:
			cur.execute("SELECT * FROM test")
			out = cur.fetchall()

	assert out == [("Bob", 18), ("Alice", None)]


def test_table_insert_validation_error() -> None:
	def valid_age(x: int) -> bool:
		return x >= 18

	test_table = Table(
		"test",
		Column("name", Type.STR, not_null=True),
		Column("age", Type.INT, validators=(valid_age,)),
	)

	with Connection(":memory:") as conn:
		conn.create(test_table)

		with pt.raises(ValidationError):
			conn.insert(test_table, name="Alice", age=16)


def test_table_iter_column() -> None:
	test_table = Table(
		"test",
		Column("name", Type.STR),
	)

	with Connection(":memory:") as conn:
		conn.create(test_table)

		conn.insert(test_table, name="Bob")
		conn.insert(test_table, name="Alice")

		out1 = tuple(conn.iter_column(test_table, "name"))
		out2 = tuple(
			conn.iter_column(test_table, "name", lambda s: len(s) == 3)
		)

	assert out1 == ("Bob", "Alice")
	assert out2 == ("Bob",)


def test_table_iter_rows() -> None:
	test_table = Table(
		"test",
		Column("id", Type.INT, primary_key=True),
		Column("name", Type.STR),
	)

	with Connection(":memory:") as conn:
		conn.create(test_table)

		conn.insert(test_table, name="Bob")
		conn.insert(test_table, name="Alice")

		out1 = tuple(conn.iter_rows(test_table))
		out2 = tuple(conn.iter_rows(test_table, id=lambda x: x % 2 == 0))

	assert out1 == ((1, "Bob"), (2, "Alice"))
	assert out2 == ((2, "Alice"),)
