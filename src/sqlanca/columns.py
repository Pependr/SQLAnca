from enum import StrEnum
from dataclasses import KW_ONLY, dataclass

import types as ts

from typing import Callable


type ValidatorFn[T] = Callable[[T], bool]


class ColumnError(AttributeError): ...


class ValidationError[T](ValueError):
	def __init__(
		self, value: T, validator: ValidatorFn[T], message: str
	) -> None:
		self.value = value
		self.validator = validator
		super().__init__(message)


class Type(StrEnum):
	STR = "TEXT"
	INT = "INTEGER"
	FLOAT = "REAL"
	NONE = "NULL"
	BYTES = "BLOB"


@dataclass(frozen=True, slots=True)
class Column[T]:
	name: str
	type: Type
	_: KW_ONLY
	default: T | ts.EllipsisType = ...
	not_null: bool = False
	unique: bool = False
	primary_key: bool = False
	validators: tuple[ValidatorFn[T], ...] = ()

	@property
	def query(self) -> str:
		query: list[str] = [self.name, self.type]

		if self.not_null:
			query.extend(("NOT", "NULL"))

		if self.unique:
			query.append("UNIQUE")

		if self.primary_key:
			query.extend(("PRIMARY", "KEY"))

		return " ".join(query)

	@property
	def public_default(self) -> T:
		if self.default is ...:
			raise ColumnError(f"Column {self.name} has no default value")
		return self.default

	def validate(self, value: T) -> None:
		for validator in self.validators:
			if not validator(value):
				raise ValidationError(
					value,
					validator,
					f"{value} failed {validator.__name__} of col {self.name}",
				)
