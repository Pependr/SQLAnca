from typing import Protocol, Any
from dataclasses import dataclass
from sqlite3 import Connection


class Constraint(Protocol):
    repr: str
    def query(self, conn: Connection) -> str: ...


@dataclass(frozen=True, slots=True)
class Column:
    name: str
    type: str
    constaints: tuple[Constraint, ...] = ()

    def assemble(self, conn: Connection) -> tuple[str, list[Any]]:
        query: list[str] = [self.name, self.type]
        values: list[Any] = []

        for c in self.constaints:
            if "?" in c.repr:
                if hasattr(c, "value"):
                    values.append(getattr(c, "value"))
                else:
                    values.append(self.name)
            query.append(c.query(conn))

        return " ".join(query), values