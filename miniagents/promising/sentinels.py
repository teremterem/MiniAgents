"""
See the docstring of the `Sentinel` class for more information.
"""


class Sentinel:
    """
    A sentinel object that is used indicate things like NO_VALUE (when None is considered a value), END_OF_QUEUE etc.
    """

    def __bool__(self) -> bool:
        raise RuntimeError("Sentinels should not be used in boolean expressions.")


NO_VALUE = Sentinel()
FAILED = Sentinel()
END_OF_QUEUE = Sentinel()
