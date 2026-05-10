from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class NotNull:
	@property
	def query(self) -> str:
		return "NOT NULL"


@dataclass(frozen=True, slots=True, kw_only=True)
class Unique:
	@property
	def query(self) -> str:
		return "UNIQUE"


@dataclass(frozen=True, slots=True, kw_only=True)
class PrimaryKey:
	descending: bool = False
	autoincrement: bool = False

	@property
	def query(self) -> str:
		q: list[str] = ["PRIMARY", "KEY"]

		if self.descending:
			q.append("DESC")
		else:
			q.append("ASC")

		if self.autoincrement:
			q.append("AUTOINCREMENT")

		return " ".join(q)
