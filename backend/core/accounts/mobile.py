"""Mobile-number normalization (DES-ID-06, SYS-ID-04).

One function used by the API, the sync command and the seed generator. The canonical form is
`09XXXXXXXXX`.
"""

import re

_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_CANONICAL = re.compile(r"09\d{9}")

MOBILE_PATTERN = r"^09\d{9}$"


class InvalidMobileError(ValueError):
    """The value cannot be turned into a valid mobile number."""


def normalize_mobile(raw: str) -> str:
    value = raw.strip().translate(_DIGITS)
    if value.startswith("+98"):
        value = "0" + value[3:]
    elif value.startswith("0098"):
        value = "0" + value[4:]
    if not _CANONICAL.fullmatch(value):
        raise InvalidMobileError("not a valid Iranian mobile number")
    return value
