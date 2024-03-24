"""
"Sentinels" of the PromiseGraph library. See the docstring of the `Sentinel` class for more information.
"""


class Sentinel:
    """
    A sentinel object that is used indicate things like "no value" (because None is a value), "failed" etc.
    """


NO_VALUE = Sentinel()
FAILED = Sentinel()
