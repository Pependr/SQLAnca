from dataclasses import KW_ONLY, dataclass
from typing import Callable, Literal, Protocol

from sqlanca.__internals__ import __MISSING__

type ValidatorFn[T] = Callable[[T], bool]


class Constraint(Protocol):
	@property
	def query(self) -> str: ...


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
	constraints: tuple[Constraint, ...] = ()
	validators: tuple[ValidatorFn[T], ...] = ()

	@property
	def query(self) -> str:
		query: list[str] = [self.name, self.type]

		for c in self.constraints:
			query.append(c.query)

		return " ".join(query)

	def validate(self, value: T) -> T:
		for validator in self.validators:
			if not validator(value):
				raise ValidationError(
					value,
					validator,
					f"{value} failed {validator.__name__} of col {self.name}",
				)

		return value
