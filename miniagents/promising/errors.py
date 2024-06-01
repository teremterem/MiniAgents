"""
This module contains the custom errors used in the `Promising` part of the library.
"""


class PromisingError(Exception):
    """
    Base class for errors in the `Promising` part of the library.
    """


class FunctionNotProvidedError(PromisingError):
    """
    TODO Oleksandr: docstring
    """


class AppenderNotOpenError(PromisingError):
    """
    Raised when an `StreamAppender` is not open for appending yet and an attempt is made to append to it.
    """


class AppenderClosedError(PromisingError):
    """
    Raised when an `StreamAppender` has already been closed for appending and an attempt is made to append to it.
    """
