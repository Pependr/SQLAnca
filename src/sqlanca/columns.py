from sqlanca.__internals__ import __MISSING__

from typing import Protocol, Callable, Literal
from dataclasses import dataclass, KW_ONLY


type ValidatorFn[T] = Callable[[T], bool]


class Constraint(Protocol):
	@property
	def query(self) -> str: ...


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
