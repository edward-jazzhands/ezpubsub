"""signal.py - EZPubSub Signal Implementation"""

from __future__ import annotations
import asyncio
import logging
import threading
from enum import Enum
from typing import Any, Awaitable, Callable, Generic, TypeVar, Union
from weakref import WeakKeyDictionary

logger = logging.getLogger("ezpubsub")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

SignalT = TypeVar("SignalT")


class SignalError(Exception):
    """Raised for Signal errors."""


class Signal(Generic[SignalT]):
    """A simple synchronous and asynchronous pub/sub signal."""

    class SignalMode(Enum):
        SYNC = "sync"
        ASYNC = "async"
        BOTH = "both"


    def __init__(self, name: str = "unnamed", require_freeze: bool = False) -> None:
        self._name = name
        self._weak_subs: WeakKeyDictionary[
            Any, Union[Callable[[SignalT], None], Callable[[SignalT], Awaitable[Any]]]
        ] = WeakKeyDictionary()
        self._strong_subs: dict[
            Any, Union[Callable[[SignalT], None], Callable[[SignalT], Awaitable[Any]]]
        ] = {}
        self._lock = threading.RLock()
        self._logging_enabled = False
        self._error_raising = False
        self._frozen = False
        self._require_freeze = require_freeze

    def __repr__(self) -> str:
        return f"Signal(name='{self._name}', subscribers={self.subscriber_count}, frozen={self._frozen})"

    def __len__(self) -> int:
        """Return self.subscriber_count using `len` for convenience."""
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

    @property
    def frozen(self) -> bool:
        """Check if the signal is frozen."""
        return self._frozen

    @property
    def require_freeze(self) -> bool:
        """Check if freeze is required before publishing."""
        return self._require_freeze

    def freeze(self) -> None:
        """Freeze the signal to prevent new subscriptions."""
        with self._lock:
            self._frozen = True
            self.log(f"Signal [{self._name}] frozen")

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

    def subscribe(
        self, callback: Union[Callable[[SignalT], None], Callable[[SignalT], Awaitable[Any]]]
    ) -> None:
        """Subscribe to the signal with a callback (sync or async).

        Args:
            callback: A callable that accepts a single argument of type SignalT.
        Raises:
            SignalError: If the callback is not callable or signal is frozen.
        """

        if not callable(callback):
            raise SignalError(f"Callback must be callable, got {type(callback)}")

        with self._lock:
            if self._frozen:
                raise SignalError("Cannot subscribe to frozen signal")

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

            callback_type = "async" if asyncio.iscoroutinefunction(callback) else "sync"
            self.log(f"Subscribed {subscriber} ({callback_type})", level=logging.DEBUG)

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
                self.log(f"Unsubscribed {subscriber}", level=logging.DEBUG)
            return removed

    def publish(self, data: SignalT) -> None:
        """Publish data to all synchronous subscribers (Async subscribers will be skipped).
        
        If any subscriber raises an exception,
        it will be caught and passed to the `on_error` method (which just logs by default,
        but can be overridden for custom error handling).

        Args:
            data: The data to send to subscribers.
        Raises:
            (Optional) Exception: If a subscriber's callback raises an exception, and `error_raising`
            is True, it will be raised after calling `on_error`.
        """

        if self._require_freeze and not self._frozen:
            raise SignalError(
                "Cannot send non-frozen signal - call `freeze` first or set require_freeze=False"
            )

        with self._lock:
            # It's possible that during the async publish, a subscriber
            # might unsubscribe, so we take a snapshot of the current subscribers.
            current = list(self._weak_subs.items()) + list(self._strong_subs.items())

        for subscriber, callback in current:
            if asyncio.iscoroutinefunction(callback):
                continue

            try:
                callback(data)
            except Exception as e:
                self.on_error(subscriber, callback, e)

    async def apublish(self, data: SignalT, also_sync: bool = False) -> None:
        """Publish data to all async subscribers. Additionally use the `also_sync` flag to
        include all sync subscribers.
        
        If any subscriber raises an exception, it will be caught and passed to the `on_error`
        method (which just logs by default, but can be overridden for custom error handling).

        Args:
            data: The data to send to subscribers.
            also_sync: If True, all sync subscribers will also be called in the current thread.
        Raises:
            SignalError: If signal requires freeze and is not frozen.
            (Optional) Exception: If a subscriber's callback raises an exception, and `error_raising`
            is True, it will be raised after calling `aon_error`.
        """

        if self._require_freeze and not self._frozen:
            raise SignalError(
                "Cannot send non-frozen signal - call `freeze` first or set require_freeze=False"
            )

        with self._lock:
            # It's possible that during the async publish, a subscriber
            # might unsubscribe, so we take a snapshot of the current subscribers.
            current = list(self._weak_subs.items()) + list(self._strong_subs.items())

        for subscriber, callback in current:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    if also_sync:
                        # Run sync callbacks in the current thread
                        callback(data)
            except Exception as e:
                await self.aon_error(subscriber, callback, e)

    # Aliases for compatibility
    emit = publish
    send = apublish

    def clear(self) -> None:
        """Clear all subscribers."""

        with self._lock:
            self._weak_subs.clear()
            self._strong_subs.clear()
            self.log("Cleared all subscribers")

    def on_error(
        self,
        subscriber: Any,
        callback: Union[Callable[[SignalT], None], Callable[[SignalT], Awaitable[Any]]],
        error: Exception,
    ) -> None:
        """Override this to handle errors differently. This will also override the `error_raising` flag.

        Args:
            subscriber: The subscriber that raised the error.
            callback: The callback that raised the error.
            error: The exception that was raised.
        """

        self.log(f"Error in callback for {subscriber}: {error}", level=logging.ERROR)
        if self._error_raising:
            raise SignalError(f"Error in callback {callback} for subscriber {subscriber}: {error}") from error

    async def aon_error(
        self,
        subscriber: Any,
        callback: Union[Callable[[SignalT], None], Callable[[SignalT], Awaitable[Any]]],
        error: Exception,
    ) -> None:
        """Async version of on_error. Override this to handle async errors differently.

        Args:
            subscriber: The subscriber that raised the error.
            callback: The callback that raised the error.
            error: The exception that was raised.
        """

        self.log(f"Error in async callback for {subscriber}: {error}", level=logging.ERROR)
        if self._error_raising:
            raise SignalError(f"Error in callback {callback} for subscriber {subscriber}: {error}") from error

    def log(self, message: str, level: int = logging.INFO) -> None:
        """Override this to customize logging behavior. This will also override the `logging_enabled` flag.

        Args:
            message: The message to log.
        """
        if self._logging_enabled:
            logger.log(level=level, msg=f"[{self._name}] {message}")

    def __call__(
        self, func: Union[Callable[[SignalT], None], Callable[[SignalT], Awaitable[Any]]]
    ) -> Union[Callable[[SignalT], None], Callable[[SignalT], Awaitable[Any]]]:
        """Decorator interface for subscribing functions.

        Args:
            func: The function to subscribe.
        Returns:
            The same function (for decorator chaining).

        Usage example:
        ```
        @signal
        def my_handler(data):
            print(f"Received data: {data}")
        """
        self.subscribe(func)
        return func
