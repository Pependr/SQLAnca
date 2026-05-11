from typing import Sized

import pytest as pt

from sqlanca.columns import Column, Type, ValidationError


def test_column_validation() -> None:
	def len_over_3(value: Sized) -> bool:
		return len(value) > 3

	col = Column("test", Type.INT, validators=(len_over_3,))

	value = "bruh"

	col.validate(value)


def test_column_validation_error() -> None:
	def len_over_3(value: Sized) -> bool:
		return len(value) > 3

	col = Column("test", Type.INT, validators=(len_over_3,))

	value = "man"

	with pt.raises(ValidationError):
		col.validate(value)
