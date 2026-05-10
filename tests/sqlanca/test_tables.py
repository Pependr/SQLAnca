from sqlanca.tables import Table
from sqlanca.columns import Column
from sqlanca.constraints import NotNull, Unique, PrimaryKey

import pytest as pt
import sqlite3 as sql


def test_table_create() -> None:
	test_table = Table(
		"test",
		Column("unique_col", "TEXT", constraints=(Unique(), NotNull())),
		Column("id", "INTEGER", constraints=(PrimaryKey(),)),
	)

	with test_table.connect(":memory:") as table:
		table.create()
		with table.__cursor__() as cur:
			cur.execute(
				"INSERT INTO test (unique_col) VALUES ('bruh'), ('dude'), ('man')"
			)
			cur.execute("SELECT * FROM test")
			out = cur.fetchall()

	assert out == [("bruh", 1), ("dude", 2), ("man", 3)]


def test_table_create_error() -> None:
	test_table = Table(
		"test",
		Column("unique_col", "TEXT", constraints=(Unique(), NotNull())),
		Column("id", "INTEGER", constraints=(PrimaryKey(),)),
	)

	with test_table.connect(":memory:") as table:
		table.create()
		with table.__cursor__() as cur:
			cur.execute(
				"INSERT INTO test (unique_col) VALUES ('bruh'), ('dude'), ('man')"
			)

			with pt.raises(sql.IntegrityError):
				cur.execute("INSERT INTO test (unique_col) VALUES ('bruh')")

			with pt.raises(sql.IntegrityError):
				cur.execute("INSERT INTO test (unique_col) VALUES (NULL)")


def test_table_create_collation() -> None:
	def len_collation(a: str, b: str) -> int:
		return (len(a) > len(b)) - (len(a) < len(b))

	test_table = Table(
		"test",
		Column("collated_column", "TEXT", collation=len_collation),
	)

	with test_table.connect(":memory:") as table:
		table.create()
		with table.__cursor__() as cur:
			cur.execute(
				"INSERT INTO test (collated_column) VALUES ('ccccc'), ('aaa'), ('bbbbbbb')"
			)

			cur.execute("SELECT * FROM test")
			out1 = cur.fetchall()

			cur.execute("SELECT * FROM test ORDER BY collated_column")
			out2 = cur.fetchall()

	assert out1 == [("ccccc",), ("aaa",), ("bbbbbbb",)]
	assert out2 == [("aaa",), ("ccccc",), ("bbbbbbb",)]
