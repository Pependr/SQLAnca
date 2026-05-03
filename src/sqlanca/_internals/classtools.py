from typing import Any, Generator


def get_public_members(obj: object) -> Generator[tuple[str, Any], None, None]:
	for attr in dir(obj):
		if attr.startswith("_"):
			continue
		yield (attr, getattr(obj, attr))
