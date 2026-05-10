from typing import Sized

import pytest as pt

from sqlanca.columns import Column, ValidationError


def test_column_validation() -> None:
	def len_over_3(value: Sized) -> bool:
		return len(value) > 3

	col = Column("test", "INT", validators=(len_over_3,))

	value = "bruh"

	assert col.validate(value) is value


def test_column_validation_error() -> None:
	def len_over_3(value: Sized) -> bool:
		return len(value) > 3

	col = Column("test", "INT", validators=(len_over_3,))

	value = "man"

	with pt.raises(ValidationError):
		col.validate(value)
