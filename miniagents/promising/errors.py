"""
This module contains the custom errors used in the `PromiseGraph` part of the library.
"""


class PromiseGraphError(Exception):
    """
    Base class for errors in the `PromiseGraph` part of the library.
    """


class AppendNotOpenError(PromiseGraphError):
    """
    Raised when an `AppendProducer` is not open for appending yet and an attempt is made to append to it.
    """


class AppendClosedError(PromiseGraphError):
    """
    Raised when an `AppendProducer` has already been closed for appending and an attempt is made to append to it.
    """
