"""signal.py - EZPubSub Signal Implementation"""

from __future__ import annotations
import logging
import threading
from typing import Any, Callable, Generic, TypeVar
from weakref import WeakKeyDictionary

logger = logging.getLogger("ezpubsub")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

SignalT = TypeVar("SignalT")


class SignalError(Exception):
    """Raised for Signal errors."""


class Signal(Generic[SignalT]):
    """A simple synchronous pub/sub signal."""

    def __init__(self, name: str = "unnamed") -> None:
        self._name = name
        self._weak_subs: WeakKeyDictionary[Any, Callable[[SignalT], None]] = WeakKeyDictionary()
        self._strong_subs: dict[Any, Callable[[SignalT], None]] = {}
        self._lock = threading.RLock()
        self._logging_enabled = False
        self._error_raising = False

    def __repr__(self) -> str:
        return f"Signal(name='{self._name}', subscribers={self.subscriber_count})"

    def __len__(self) -> int:
        """Return self.subscriber_count using len() for convenience."""
        return self.subscriber_count

    @property
    def subscriber_count(self) -> int:
        """Return the total number of subscribers (both weak and strong)."""
        return len(self._weak_subs) + len(self._strong_subs)

    @property
    def logging_enabled(self) -> bool:
        """Check if logging is enabled."""
        return self._logging_enabled

    @property
    def error_raising(self) -> bool:
        """Check if error raising is enabled."""

        return self._error_raising

    def toggle_logging(self, enabled: bool = True) -> None:
        """Toggle logging for this signal.

        Note that you can also override the `log` method to customize logging behavior, which would
        also override this flag unless you chose to incorporate it."""

        with self._lock:
            self._logging_enabled = enabled

    def toggle_error_raising(self, enabled: bool = True) -> None:
        """Toggle whether to raise exceptions in subscriber callbacks which are passed to `on_error`.

        Note that you can also override the `on_error` method to customize error handling, which would
        also override this flag unless you chose to incorporate it."""

        with self._lock:
            self._error_raising = enabled

    def subscribe(self, callback: Callable[[SignalT], None]) -> None:
        """Subscribe to the signal with a callback.

        Args:
            callback: A callable that accepts a single argument of type SignalT.
        Raises:
            SignalError: If the callback is not callable.
        """

        if not callable(callback):
            raise SignalError(f"Callback must be callable, got {type(callback)}")

        with self._lock:
            # Determine if subscriber is a class method or a regular function:
            subscriber = getattr(callback, "__self__", None) or callback

            # Remove old subscription if it exists
            self.unsubscribe(subscriber)

            try:
                # Weak refs for class methods
                self._weak_subs[subscriber] = callback
            except TypeError:
                # Strong refs for regular functions
                self._strong_subs[subscriber] = callback

    def unsubscribe(self, subscriber: Any) -> bool:
        """Unsubscribe a subscriber from the signal.

        Args:
            subscriber: The subscriber to remove, which can be a class instance or a function.
        Returns:
            bool: True if the subscriber was removed, False if it was not found.
        """
        with self._lock:
            removed = False
            if subscriber in self._weak_subs:
                del self._weak_subs[subscriber]
                removed = True
            if subscriber in self._strong_subs:
                del self._strong_subs[subscriber]
                removed = True
            if removed:
                self.log(f"Unsubscribed {subscriber}")
            return removed

    def publish(self, data: SignalT) -> None:
        """Publish data to all subscribers. If any subscriber raises an exception,
        it will be caught and passed to the `on_error` method (which just logs by default,
        but can be overridden for custom error handling).

        Args:
            data: The data to send to subscribers.
        Raises:
            (Optional) Exception: If a subscriber's callback raises an exception, and `error_raising`
            is True, it will be raised after calling `on_error`.
        """

        with self._lock:
            # Snapshot current subscribers to avoid mutation issues
            current = list(self._weak_subs.items()) + list(self._strong_subs.items())

        for subscriber, callback in current:
            try:
                callback(data)
            except Exception as e:
                self.on_error(subscriber, callback, e)

    emit = publish  # alias

    def clear(self) -> None:
        """Clear all subscribers."""

        with self._lock:
            self._weak_subs.clear()
            self._strong_subs.clear()

    def on_error(self, subscriber: Any, callback: Callable[[SignalT], None], error: Exception) -> None:
        """Override this to handle errors differently. This will also override the `error_raising` flag.

        Args:
            subscriber: The subscriber that raised the error.
            callback: The callback that raised the error.
            error: The exception that was raised.
        """

        self.log(f"Error in callback for {subscriber}: {error}")
        if self._error_raising:
            raise SignalError(f"Error in callback {callback} for subscriber {subscriber}: {error}") from error

    def log(self, message: str) -> None:
        """Override this to customize logging behavior. This will also override the `logging_enabled` flag.

        Args:
            message: The message to log.
        """
        if self._logging_enabled:
            logger.info(f"[{self._name}] {message}")
