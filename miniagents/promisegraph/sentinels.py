"""
See the docstring of the `Sentinel` class for more information.
"""


class Sentinel:
    """
    A sentinel object that is used indicate things like NO_VALUE (when None is considered a value), FAILED etc.
    """


NO_VALUE = Sentinel()
FAILED = Sentinel()
