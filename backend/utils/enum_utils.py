"""
SQLAlchemy's Enum column type (even with native_enum=False) returns the
Python enum member on read, not a plain string — despite the ORM model's
`Mapped[str]` type hint, which only affects static typing. Interpolating
such a value directly into an f-string prints "BookingStatus.CONFIRMED"
instead of "CONFIRMED". This helper normalizes either case to the plain
string value for user-facing messages.
"""


def status_label(value) -> str:
    return getattr(value, "value", value)
