"""
This module contains the custom errors used in the `Promising` part of the library.
"""


class PromisingError(Exception):
    """
    Base class for errors in the `Promising` part of the library.
    """


class AppendNotOpenError(PromisingError):
    """
    Raised when an `AppendProducer` is not open for appending yet and an attempt is made to append to it.
    """


class AppendClosedError(PromisingError):
    """
    Raised when an `AppendProducer` has already been closed for appending and an attempt is made to append to it.
    """
