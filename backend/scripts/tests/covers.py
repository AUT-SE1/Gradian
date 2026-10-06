"""Same idea as core/tests/helpers/covers.py, without Django: records requirement ids on a test."""

import re
from collections.abc import Callable
from typing import TypeVar

_C = TypeVar("_C", bound=Callable[..., object] | type)
_ID = re.compile(r"^SYS-[A-Z]+-\d{2}$")


def covers(*requirement_ids: str) -> Callable[[_C], _C]:
    for requirement_id in requirement_ids:
        if not _ID.match(requirement_id):
            raise ValueError(f"not a requirement id: {requirement_id!r}")

    def decorate(target: _C) -> _C:
        target.tags = {f"req-{r}" for r in requirement_ids}  # type: ignore[union-attr]  # plain marker attribute
        return target

    return decorate
