from dataclasses import KW_ONLY, dataclass
from typing import Callable, Literal

from sqlanca.__internals__ import __MISSING__

type ValidatorFn[T] = Callable[[T], bool]


class ValidationError[T](ValueError):
	def __init__(
		self, value: T, validator: ValidatorFn[T], message: str
	) -> None:
		self.value = value
		self.validator = validator
		self.message = message
		super().__init__(message)


@dataclass(frozen=True, slots=True)
class Column[T]:
	name: str
	type: str
	_: KW_ONLY
	default: T | Literal["MISSING"] = __MISSING__
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

	def validate(self, value: T) -> None:
		for validator in self.validators:
			if not validator(value):
				raise ValidationError(
					value,
					validator,
					f"{value} failed {validator.__name__} of col {self.name}",
				)
