"""
See the docstring of the `Sentinel` class for more information.
"""


class Sentinel:
    """
    A sentinel object that is used indicate things like NO_VALUE (when None is considered a value), DEFAULT, FAILED,
    END_OF_QUEUE, etc.
    """


NO_VALUE = Sentinel()
DEFAULT = Sentinel()
FAILED = Sentinel()
END_OF_QUEUE = Sentinel()
