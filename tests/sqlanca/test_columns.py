import itertools as it
from typing import Sized

import pytest as pt

from sqlanca.columns import Column, ColumnError, Type, ValidationError


def test_column_validation() -> None:
	def len_over_3(value: Sized) -> bool:
		return len(value) > 3

	col = Column("test", Type.INT, validators=(len_over_3,))

	col.validate("bruh")

	with pt.raises(ValidationError):
		col.validate("man")


def test_column_query() -> None:
	names = ("name", "surname", "language", "color", "idunno")

	for name, type in it.product(names, Type):
		col = Column(name, type)

		assert col.query == f"{name} {type.value}"


def test_column_query_flags() -> None:
	for not_null, unique, primary_key in it.product((False, True), repeat=3):
		col = Column(
			"test",
			Type.STR,
			not_null=not_null,
			unique=unique,
			primary_key=primary_key,
		)

		if primary_key:
			assert "PRIMARY KEY" in col.query
		if unique:
			assert "UNIQUE" in col.query
		if not_null:
			assert "NOT NULL" in col.query


def test_column_default() -> None:
	default_col = Column("default_col", Type.INT, default=0)
	non_default_col = Column("non_default_col", Type.STR)
	null_default_col = Column("null_default_col", Type.FLOAT, default=None)

	assert default_col.public_default == 0
	assert null_default_col.public_default is None

	with pt.raises(ColumnError):
		non_default_col.public_default
