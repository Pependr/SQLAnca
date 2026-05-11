from typing import Any, Protocol


class TableError(ValueError): ...


class Column[T](Protocol):
	@property
	def name(self) -> str: ...

	@property
	def primary_key(self) -> bool: ...

	@property
	def public_default(self) -> T: ...

	@property
	def query(self) -> str: ...

	def validate(self, value: T) -> None: ...


class Table:
	def __init__(self, name: str, *cols: Column[Any]) -> None:
		self.name = name
		self.columns: dict[str, Column[Any]] = {}

		for col in cols:
			self.columns[col.name] = col

	@property
	def column_queries(self) -> tuple[str, ...]:
		return tuple(col.query for col in self.columns.values())

	@property
	def create_query(self) -> str:
		return f"CREATE TABLE {self.name} ({", ".join(self.column_queries)})"

	def filter_inputs(self, inputs: dict[str, Any]) -> dict[str, Any]:
		allowed: dict[str, Any] = {}

		for col in self.columns.values():
			if col.name not in inputs:
				if col.primary_key:
					continue
				allowed[col.name] = col.public_default
			else:
				col.validate(inputs[col.name])
				allowed[col.name] = inputs[col.name]

		return allowed

	def insert_query(self, inputs: dict[str, Any]) -> tuple[str, tuple[Any]]:
		f = self.filter_inputs(inputs)
		n = len(f)
		d = ", "
		return (
			f"INSERT INTO {self.name} ({d.join(f)}) VALUES ({d.join("?" * n)})",
			tuple(f.values()),
		)

	def get_col_pos(self, col_name: str) -> int:
		for i, name in enumerate(self.columns):
			if name == col_name:
				break
		else:
			raise TableError(f"Table {self.name} has no column {col_name}")
		return i

	def select_col(self, col_name: str) -> str:
		return f"SELECT {col_name} FROM {self.name}"

	@property
	def select_all(self) -> str:
		return f"SELECT * FROM {self.name}"
