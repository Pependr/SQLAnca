from dataclasses import dataclass

import pytest as pt

from sqlanca.tables import Table


@dataclass(frozen=True, slots=True)
class MockCol:
	name: str
	primary_key: bool = False
	public_default: str | None = None
	query: str = "query"
	valid: bool = True

	def validate(self, value: str) -> None:
		if not self.valid:
			raise RuntimeError("Invalid value!")


@pt.fixture
def query_cols() -> tuple[MockCol, ...]:
	return tuple(MockCol(f"col_{i}", query=f"query_{i}") for i in range(3))


@pt.fixture
def filter_table() -> Table:
	return Table(
		"filter_table",
		MockCol("value"),
		MockCol("default", public_default="default"),
		MockCol("default_no_value", public_default="default"),
		MockCol("primary_key_value", primary_key=True),
		MockCol("primary_key_no_value", primary_key=True),
	)


def test_table_column_queries(query_cols: tuple[MockCol, ...]) -> None:
	table = Table("test", *query_cols)

	assert table.column_queries == tuple(c.query for c in query_cols)


def test_table_create_query(query_cols: tuple[MockCol, ...]) -> None:
	table = Table("test", *query_cols)

	assert table.create_query == "CREATE TABLE test (query_0, query_1, query_2)"


def test_table_filter_inputs(filter_table: Table) -> None:
	data: dict[str, str] = {
		"value": "bruh",
		"default": "dude",
		"primary_key_value": "man",
	}

	expect: dict[str, str] = {
		"value": "bruh",
		"default": "dude",
		"default_no_value": "default",
		"primary_key_value": "man",
	}

	assert filter_table.filter_inputs(data) == expect


def test_table_insert_query(filter_table: Table) -> None:
	data: dict[str, str] = {
		"value": "bruh",
		"default": "dude",
		"primary_key_value": "man",
	}

	assert filter_table.insert_query(data) == (
		"INSERT INTO filter_table (value, default, default_no_value, primary_key_value) VALUES (?, ?, ?, ?)",
		("bruh", "dude", "default", "man"),
	)
