"""
This module contains the custom errors used in the `Promising` part of the library.
"""


class PromisingError(Exception):
    """
    Base class for errors in the `Promising` part of the library.
    """


class FunctionNotProvidedError(PromisingError):
    """
    Raised when a function that was supposed to be provided (most likely as a parameter to a class constructor)
    was not provided.
    """


class AppenderNotOpenError(PromisingError):
    """
    Raised when an `StreamAppender` is not open for appending yet and an attempt is made to append to it.
    """


class AppenderClosedError(PromisingError):
    """
    Raised when an `StreamAppender` has already been closed for appending and an attempt is made to append to it.
    """


class PromisingContextError(PromisingError):
    """
    Base class for errors related to `PromisingContext`.
    """


class NoActiveContextError(PromisingContextError):
    """
    Raised when an operation that requires an active context is attempted without an active context.
    """


class WrongActiveContextError(PromisingContextError):
    """
    Raised when an operation that requires a specific active context is attempted with a different active context.
    """
