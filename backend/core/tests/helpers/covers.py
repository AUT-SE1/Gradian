"""`@covers("SYS-AUTH-02")` ties a test to requirements (test plan 2.5).

It adds the Django test tag `req-SYS-AUTH-02`, so one requirement's tests run with
`manage.py test --tag=req-SYS-AUTH-02`, and `scripts/req_coverage.py` reads the same ids.
"""

import re
from collections.abc import Callable
from typing import TypeVar

from django.test import tag

_C = TypeVar("_C", bound=Callable[..., object] | type)
_ID = re.compile(r"^(SYS|CON)-[A-Z]+(-\d{2})?$")


def covers(*requirement_ids: str) -> Callable[[_C], _C]:
    for requirement_id in requirement_ids:
        if not _ID.match(requirement_id):
            raise ValueError(f"not a requirement id: {requirement_id!r}")
    return tag(*(f"req-{requirement_id}" for requirement_id in requirement_ids))
