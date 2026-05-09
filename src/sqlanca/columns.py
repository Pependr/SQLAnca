from sqlanca.__internals__ import __MISSING__

from typing import Protocol, Callable, Literal
from dataclasses import dataclass, KW_ONLY


type ValidatorFn[T] = Callable[[T], bool]
type CollationFn = Callable[[str, str], int]


class Constraint(Protocol):
	@property
	def query(self) -> str: ...


@dataclass(frozen=True, slots=True)
class Column[T]:
	name: str
	type: str
	_: KW_ONLY
	default: T | Literal["MISSING"] = __MISSING__
	collation: CollationFn | None = None
	constraints: tuple[Constraint, ...] = ()
	validators: tuple[ValidatorFn[T], ...] = ()

	@property
	def query(self) -> str:
		query: list[str] = [self.name, self.type]

		for c in self.constraints:
			query.append(c.query)

		if self.collation is not None:
			query.append(f"COLLATE {self.name}_collation")

		return " ".join(query)
