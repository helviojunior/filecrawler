from typing import Any, Tuple


class IntegrationError(Exception):
    """Generic exception for the 'integration error' package.

    For the 'errors' attribute, errors are ordered from
    most recently raised (index=0) to least recently raised (index=N)
    """

    def __init__(self, message: Any, errors: Tuple[Exception, ...] = ()):
        super().__init__(message)
        self.errors = tuple(errors)
        self.message = message

    def __repr__(self) -> str:
        parts = [repr(self.message)]
        if self.errors:
            parts.append(f"errors={self.errors!r}")
        return "{}({})".format(self.__class__.__name__, ", ".join(parts))

    def __str__(self) -> str:
        return str(self.message)


class FalsePositiveError(Exception):
    """Generic exception for the 'integration error' package.

    For the 'errors' attribute, errors are ordered from
    most recently raised (index=0) to least recently raised (index=N)
    """
    pass

