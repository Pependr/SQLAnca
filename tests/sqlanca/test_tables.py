from sqlanca.tables import ColumnError, Column, ColType, Table, validates

import pytest


DEFAULT_ERROR = "A column cannot have both 'default' and 'default_factory' specified at the same time"
PRIMARY_KEY_ERROR = "A primary key column must be of type INT"


def test_column_errors(subtests: pytest.Subtests) -> None:
	with subtests.test("test_default_error"):
		with pytest.raises(ColumnError, match=DEFAULT_ERROR):
			Column(
				type=ColType.BLOB,
				default=b"bruh",
				default_factory=lambda: b"bruh",
			)

	with subtests.test("test_primary_key_error"):
		with pytest.raises(ColumnError, match=PRIMARY_KEY_ERROR):
			Column(type=ColType.REAL, primary_key=True)


def test_table(subtests: pytest.Subtests) -> None:
	class DataBase(Table):
		id: Column[int] = Column(type=ColType.INT, primary_key=True)
		name: Column[str] = Column(type=ColType.TEXT)
		data: Column[bytes | None] = Column(type=ColType.BLOB, not_null=False)

		@validates("name")
		def validate_name(name: str) -> str:
			assert len(name) > 0
			assert name.strip()
			return name.strip().title()

	with subtests.test("test_table_columns"):
		assert DataBase.__columns__ == {
			"id": Column(type=ColType.INT, primary_key=True),
			"name": Column(type=ColType.TEXT),
			"data": Column(type=ColType.BLOB, not_null=False),
		}

	with subtests.test("test_table_validators"):
		assert DataBase.__validators__ == {
			"name": [DataBase.validate_name],
		}
		assert DataBase.validate_name("   alice     ") == "Alice"
