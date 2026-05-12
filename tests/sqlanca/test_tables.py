import sqlite3 as sql

import pytest as pt

from sqlanca.columns import Column, Type, ValidationError
from sqlanca.io import Connection
from sqlanca.tables import Table


@pt.fixture
def unique_table() -> Table:
	return Table(
		"test",
		Column("unique_col", Type.STR, not_null=True, unique=True),
		Column("id", Type.INT, primary_key=True),
	)


@pt.fixture
def default_table() -> Table:
	return Table(
		"test",
		Column("name", Type.STR, not_null=True),
		Column("age", Type.INT, default=None),
	)


@pt.fixture
def valid_table() -> Table:
	def valid_age(x: int) -> bool:
		return x >= 18

	return Table(
		"test",
		Column("name", Type.STR, not_null=True),
		Column("age", Type.INT, validators=(valid_age,)),
	)


@pt.fixture
def iter_table() -> Table:
	return Table(
		"test",
		Column("id", Type.INT, primary_key=True),
		Column("name", Type.STR),
	)


@pt.fixture
def conn() -> Connection:
	return Connection(":memory:")


def test_table_create(unique_table: Table, conn: Connection) -> None:
	with conn:
		conn.create(unique_table)
		with conn.__cursor__() as cur:
			cur.execute(
				"INSERT INTO test (unique_col) VALUES ('bruh'), ('dude'), ('man')"
			)
			cur.execute("SELECT * FROM test")
			out = cur.fetchall()

	assert out == [("bruh", 1), ("dude", 2), ("man", 3)]


def test_table_constraints(unique_table: Table, conn: Connection) -> None:
	with conn:
		conn.create(unique_table)
		with conn.__cursor__() as cur:
			cur.execute(
				"INSERT INTO test (unique_col) VALUES ('bruh'), ('dude'), ('man')"
			)

			with pt.raises(sql.IntegrityError):
				cur.execute("INSERT INTO test (unique_col) VALUES ('bruh')")

			with pt.raises(sql.IntegrityError):
				cur.execute("INSERT INTO test (unique_col) VALUES (NULL)")


def test_table_insert(default_table: Table, conn: Connection) -> None:
	with conn:
		conn.create(default_table)

		conn.insert(default_table, name="Bob", age=18)
		conn.insert(default_table, name="Alice")

		with conn.__cursor__() as cur:
			cur.execute("SELECT * FROM test")
			out = cur.fetchall()

	assert out == [("Bob", 18), ("Alice", None)]


def test_table_insert_validation_error(
	valid_table: Table, conn: Connection
) -> None:
	with conn:
		conn.create(valid_table)

		with pt.raises(ValidationError):
			conn.insert(valid_table, name="Alice", age=16)


def test_table_iter_column(iter_table: Table, conn: Connection) -> None:
	with conn:
		conn.create(iter_table)

		conn.insert(iter_table, name="Bob")
		conn.insert(iter_table, name="Alice")

		out1 = tuple(conn.iter_column("test", "name"))
		out2 = tuple(conn.iter_column("test", "name", lambda s: len(s) == 3))

	assert out1 == ("Bob", "Alice")
	assert out2 == ("Bob",)


def test_table_iter_rows(iter_table: Table, conn: Connection) -> None:
	def even_id(id: int) -> bool:
		return id % 2 == 0

	with conn:
		conn.create(iter_table)

		conn.insert(iter_table, name="Bob")
		conn.insert(iter_table, name="Alice")

		out1 = tuple(conn.iter_rows("test"))
		out2 = tuple(conn.iter_rows("test", id=even_id))

	assert out1 == ((1, "Bob"), (2, "Alice"))
	assert out2 == ((2, "Alice"),)
