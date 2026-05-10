import sqlite3 as sql

import pytest as pt

from sqlanca.columns import Column
from sqlanca.constraints import NotNull, PrimaryKey, Unique
from sqlanca.tables import Table


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
