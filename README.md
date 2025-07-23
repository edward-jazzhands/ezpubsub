# ezpubsub

![badge](https://img.shields.io/badge/linted-Ruff-blue?style=for-the-badge&logo=ruff)
![badge](https://img.shields.io/badge/formatted-black-black?style=for-the-badge)
![badge](https://img.shields.io/badge/type_checked-MyPy_(strict)-blue?style=for-the-badge&logo=python)
![badge](https://img.shields.io/badge/type_checked-Pyright_(strict)-blue?style=for-the-badge&logo=python)
![badge](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)

A tiny, modern alternative to Blinker – typed, thread-safe, and built for today’s Python.

ezpubsub is an ultra-simple pub/sub library for Python. Its only goal is to make publishing and subscribing to events as easy as possible. No async complexity, no extra features, no dependencies—just clean, synchronous pub/sub that works anywhere.

## Features

- Thread-Safe by Default – Safe to publish and subscribe across threads.
- Strongly Typed with Generics – Signals are fully generic (Signal[str], Signal[MyClass]), letting Pyright/MyPy catch mistakes before runtime. This also unlocks powerful combinations with Typed Objects as signal types.
- Synchronous by Design – 100% sync to keep things predictable. Works fine in async projects—you control when/where to schedule tasks.
- Automatic Memory Management – Bound methods are weakly referenced and automatically unsubscribed when their objects are deleted. Normal functions are strongly referenced and must be manually unsubscribed.
- Lightweight & Zero Dependencies – Minimal API, no legacy baggage, designed for 2025-era Python.

## Why ezpubsub / Project philosophy

### Why not just use Blinker?

Blinker is an excellent, battle-tested library. If you’re writing a simple, single-threaded, synchronous app (e.g., Flask extensions), Blinker is still a great choice.

However, ezpubsub was designed as a modern alternative:

1. Full Static Typing with Generics
    Blinker’s signals are effectively untyped (Any everywhere). ezpubsub’s Signal[T] lets Pyright/MyPy enforce that subscribers receive the correct data type at development time, as well as unlocks powerful combinations with Typed Objects as signal types. This makes it much easier to catch mistakes before they happen, rather than at runtime.
2. Thread-Safe by Default
    Blinker assumes single-threaded execution. ezpubsub uses proper locking, making it safe in threaded or mixed sync/async environments.
3. Type Safety Over Dynamic Namespaces
    Blinker’s string-based namespaces allow arbitrary signal creation (ns.signal("user_created")), but at the cost of type safety—there’s nothing stopping you from accidentally publishing the wrong object type. ezpubsub treats each signal as an explicitly typed object (Signal[User]), making such mistakes enforced at compile time instead of runtime.

### Why not use an "async-native" pub/sub library?

There are dozens of tiny “AIO pub/sub” libraries on GitHub. I was personally not satisfied with any of them for these reasons:

1. Async should not be the core mechanism
    Pub/sub is just a dispatch mechanism. Whether you call a subscriber directly or schedule it on an event loop is application logic. Some people might say this is a hot take, but I believe in it. It's not terrible to include async support as an option, but it should not be the primary focus of a pub/sub library.
2. Async-First Usually Means Bad Ergonomics
    These libraries often force you into awkward patterns: creating tasks for every subscription, manual event loop juggling, weird API naming. No benefit, more pain.

There is a reason that the most popular pub/sub libraries in the Python ecosystem (blinker, Celery, PyDispatcher, etc) are all synchronous. It’s the simplest, most predictable way to do pub/sub. Async-first versions, in my opinion, are [reinventing the square wheel](https://exceptionnotfound.net/reinventing-the-square-wheel-the-daily-software-anti-pattern/).

I would certainly be open to implementing some very simple async support in future versions (As of writing this it's only 0.1.0!), but it would be an optional feature, and need to follow the same principles of simplicity and ergonomics as the rest of the library.

---

### Comparison table - ezpubsub vs Blinker

|                           |                          |                 |                 |
| ------------------------- | ------------------------ | --------------- | --------------- |
| Feature                   | ezpubsub                 | blinker         | Category        |
| Thread-Safe by Default    | ✅ Yes                    | ❌ No            | Core Philosophy |
| Generically Typed Payload | ✅ Yes (Signal[T])        | ❌ No (**kwargs) | Core Philosophy |
| Weak-Reference Support    | ✅ Yes                    | ✅ Yes           | Core Philosophy |
| Sender-Specific Filtering | ❌ No (Not planned)       | ✅ Yes           | Core (Blinker)  |
| Namespacing               | ❌ No (Not planned)       | ✅ Yes           | Core (Blinker)  |
| Async Support             | ❌ Possible future update | ✅ Yes           | Nice-to-have    |
| Decorator API             | ❌ Possible future update | ✅ Yes           | Nice-to-have    |
| Context Managers          | ❌ Possible future update | ✅ Yes           | Nice-to-have    |
| Metasignals (on connect)  | ❌ Possible future update | ✅ Yes           | Nice-to-have    |
|                           |                          |                 |                 |

## Documentation

### Requirements

- Python 3.10 or higher
- Optional: Enable type checking with [Pyright](http://pyright.org), [MyPy](http://mypy-lang.org), or your checker of choice to get the full benefits of static typing and generics.

### Installation

Install from PyPI:

```sh
pip install ezpubsub
```

Or, with [UV](https://github.com/astral-sh/uv):

```sh
uv add ezpubsub
```

---

### Quick Start

Create a `Signal` instance, subscribe to it, and publish data:

```py
from ezpubsub import Signal

data_signal = Signal[str](name="data_updated")

def my_callback(data: str) -> None:
    print("Received data:", data)

data_signal.subscribe(my_callback)
data_signal.publish("Hello World")
# Output: Received data: Hello World
```

### Basic Usage Example

```py
from ezpubsub import Signal

class DataSender:
    def __init__(self):
        # Type hint the signal with the type of data it will send to subscribers:
        self.data_signal = Signal[str](name="data_updated")

    def fetch_some_data(self) -> None:
        data = imaginary_work()
        self.data_signal.publish(data)  # Publish data to all subscribers

data_sender = DataSender()

class DataProcessor:

    def subscribe_to_signal(self, data_sender: DataSender) -> None:
        data_sender.data_signal.subscribe(self.process_data)

    # Callback must take one argument which matches the signal's type.
    def process_data(self, data: str) -> None:
        print(f"Processing: {data}")

data_processor = DataProcessor()
data_processor.subscribe_to_signal(data_sender)

data_sender.fetch_some_data()

# If the DataProcessor instance is deleted, it will automatically
# unsubscribe from the signal.
del data_processor
```

### Methods or Functions

Both bound instance methods and functions can be used as callbacks.

- **Bound methods** are weakly referenced and automatically unsubscribed when their instances are deleted (example above in Basic Usage)
- **Functions** (or other permanent objects) are strongly referenced and must be manually unsubscribed if no longer needed.

Example using a normal function:

```py
def my_callback(data: str) -> None:
    print("Got:", data)

sender.data_signal.subscribe(my_callback)
sender.data_signal.unsubscribe(my_callback)
```

### Using in Threads / Thread Safety

The library is thread-safe. You can safely publish and subscribe from multiple threads. However, be cautious with the data you pass to subscribers, as they will run in the thread that calls publish.

Key considerations:

- Subscribers execute synchronously in the publishing thread
- If a subscriber blocks or takes a long time, it will delay other subscribers and the publisher
- Mutable data passed to subscribers should be thread-safe or immutable
- Consider using copy.deepcopy() for complex mutable objects if subscribers might modify them

Ultra simple threading example:

```py
# Simple thread safety example
signal = Signal[str]()
signal.subscribe(lambda msg: print(f"Received: {msg}"))

# Safe to call from any thread
threading.Thread(target=lambda: signal.publish("Hello from thread")).start()
```

More thorough threading example:

```py
import threading
import time
from ezpubsub import Signal

# Create a signal that will be shared across threads
message_signal = Signal[str](name="cross_thread_messages")

def worker_subscriber(worker_id: int):
    def handle_message(data: str):
        print(f"Worker {worker_id} received: {data}")
    
    message_signal.subscribe(handle_message)
    # Keep thread alive to receive messages
    time.sleep(2)

# Start subscriber threads
threads = []
for i in range(3):
    thread = threading.Thread(target=worker_subscriber, args=(i,))
    thread.start()
    threads.append(thread)

# Give threads time to subscribe
time.sleep(0.1)

# Publish from main thread
message_signal.publish("Hello from main thread!")
message_signal.publish("Another message!")

# Wait for threads to complete
for thread in threads:
    thread.join()
```

Some examples of best practices for thread safety:

```py
import copy
from ezpubsub import Signal

# For mutable data, consider copying to avoid race conditions
user_signal = Signal[dict](name="user_updates")

def safe_publish(user_data: dict):
    # Deep copy to prevent concurrent modification issues
    user_signal.publish(copy.deepcopy(user_data))

# Or use immutable data types like namedtuples or dataclasses with frozen=True
from dataclasses import dataclass

@dataclass(frozen=True)
class UserEvent:
    user_id: int
    action: str
    timestamp: float

user_events = Signal[UserEvent](name="user_events")
# UserEvent is immutable, so safe to pass between threads
```

### Global Signal / Bridging Frameworks

```py
# Useful when you have multiple systems that need to communicate
from ezpubsub import Signal

# Global signal that both systems can use
system_events = Signal[dict](name="cross_system")

# Flask app publishes events
@app.route('/trigger')
def trigger_event():
    system_events.publish({"event": "flask_trigger", "data": "hello"})
    return "triggered"

# Separate background service subscribes
class BackgroundService:
    def __init__(self):
        system_events.subscribe(self.handle_system_event)
    
    def handle_system_event(self, event_data: dict):
        print(f"Background service received: {event_data}")

# Now Flask and your background service can communicate
# without tight coupling
```

### Integrating with Async Code

ezpubsub is synchronous at its core. You control when and how to schedule async work, which keeps the library predictable and compatible with any async framework:

```py
import asyncio      # if you're using asyncio directly
from ezpubsub import Signal

loop = asyncio.get_event_loop()
data_signal = Signal[str]()

async def async_process(data: str):
    await asyncio.sleep(0.1)
    print("Async processed:", data)

def sync_callback(data: str):
    loop.create_task(async_process(data))

data_signal.subscribe(sync_callback)
data_signal.publish("Hello World")
await asyncio.sleep(0.2)
```

This keeps the library simple and leaves control in your hands. Async helper wrappers may possibly be added in the future if there is high enough demand for them. But I personally do not think there's any real benefit. You control when the publisher emits data. If you need your publisher to await some IO, you can do that before calling `publish`. If you need to schedule the subscriber to run later, you can do that in the callback itself. Here synchronous code is flexible and does not force you into any specific async patterns.

### Using Typed Objects for Signal Types

One of the coolest benefits of modern Python type hinting is the ability to create "Typed Objects" that can be used as signal types. This allows you to define a class that represents the data your signal will carry, and then use that class as the type parameter for your Signal.

```py
from dataclasses import dataclass
from typing import Optional
from ezpubsub import Signal

@dataclass
class UserRegistered:
    user_id: int
    email: str
    username: str
    referral_code: Optional[str] = None

@dataclass 
class OrderPlaced:
    order_id: str
    user_id: int
    total_amount: float
    items: list[str]

# Create signals with specific typed objects
user_events = Signal[UserRegistered](name="user_registered")
order_events = Signal[OrderPlaced](name="order_placed")

# Type-safe subscribers - your IDE and type checker will catch mistakes!
def send_welcome_email(event: UserRegistered) -> None:
    print(f"Sending welcome email to {event.email}")
    # Your IDE knows 'event' has .email, .username, etc.
    # Type checker will catch if you try to access .nonexistent_field

def process_order(event: OrderPlaced) -> None:
    print(f"Processing order {event.order_id} for ${event.total_amount}")
    # Your IDE knows 'event' has .order_id, .total_amount, etc.

user_events.subscribe(send_welcome_email)
order_events.subscribe(process_order)

# Publishing with type safety
user_events.publish(UserRegistered(
    user_id=123,
    email="user@example.com", 
    username="newuser",
    referral_code="FRIEND123"
))

# This would be caught by type checker:
# user_events.publish("just a string")  # Type error!
# user_events.publish(OrderPlaced(...))  # Type error!

# Benefits:
# 1. IDE autocomplete for event data fields
# 2. Compile-time type checking catches bugs early  
# 3. Self-documenting - signal type tells you exactly what data to expect
# 4. Refactoring safety - rename a field and find all usages automatically
# 5. Easy to evolve - add new fields with defaults without breaking existing code
```

Pro tip: Use dataclasses with `frozen=True` for immutable events that are safe to pass between threads (See [Using in Threads / Thread Safety](#using-in-threads--thread-safety))

### Overriding Logging and Error Handling

You can override the `log` and `on_error` methods in your `Signal` subclass to customize logging and error handling behavior.

By default, `on_error` just logs the exception using the `log` method, and the `log` method uses Python's built-in logging module. You can change this to raise exceptions, use a different logger, or handle errors in any way you prefer.

```py
from ezpubsub import Signal
from loguru import logger as loguru_logger

# Custom logger setup
custom_logger = logging.getLogger("my_app.signals")
custom_logger.setLevel(logging.DEBUG)

class CustomSignal(Signal[str]):
    def log(self, message: str) -> None:
        # Use your own logger instead of the default
        custom_logger.debug(f"[SIGNAL:{self._name}] {message}")
    
    def on_error(self, subscriber, callback, error: Exception) -> None:

        # Potential 1: Swap in standard logger with a different one
        loguru_logger.info(f"Callback error from {subscriber}: {error}")
        
        # Potential 2: Re-raise the exception (stops execution)
        # Catch this by wrapping the publish call in a try-except block.
        raise error
        
        # Potential 3: Use your own error handling logic
        sentry.capture_exception(error)
    
# Usage
signal = CustomSignal(name="my_signal")
signal.toggle_logging(True)  # Enable logging to see the custom behavior

def problematic_callback(data: str):
    raise ValueError("Something went wrong!")

signal.subscribe(problematic_callback)

# If you've raised the error you can now catch it when you call publish
try:
    signal.publish("test")  # Will trigger custom error handling
except Exception as e:
    print(f"Caught an error during publish: {e}")
```

### Memory Management

ezpubsub will handle the memory management differently depending on whether the subscriber is a bound method or a normal function:

- **Bound methods** are weakly referenced and automatically unsubscribed when their instances are deleted. This means you don't have to worry about memory leaks from subscribers that are no longer needed. If the class instance is deleted, the subscriber will be automatically unsubscribed from the signal.
- **Functions** (or other permanent objects) are strongly referenced and must be manually unsubscribed if no longer needed. This is useful for long-lived subscribers that you want to keep around, but you need to remember to unsubscribe them when they are no longer needed to avoid memory leaks.

Bound methods:

```py
class DataProcessor:
    def process(self, data: str):
        print(f"Processing: {data}")

signal = Signal[str]()
processor = DataProcessor()
signal.subscribe(processor.process)  # Weakly referenced

print(f"Subscribers: {signal.subscriber_count}")  # 1
del processor  # Object is deleted
print(f"Subscribers: {signal.subscriber_count}")  # 0 (automatically cleaned up)
```

Functions:

```py
def process_data(data: str):
    print(f"Processing: {data}")

signal = Signal[str]()
signal.subscribe(process_data)  # Strongly referenced

print(f"Subscribers: {signal.subscriber_count}")  # 1
del process_data  # This doesn't remove it from the signal!
print(f"Subscribers: {signal.subscriber_count}")  # Still 1

# You must manually unsubscribe functions:
signal.unsubscribe(process_data)
```

Why This Design?

- Instance methods are usually tied to object lifecycles - when the object is gone, you probably don't want the callbacks anymore
- Functions are often module-level and meant to persist - they need explicit management
- This prevents memory leaks while keeping the API simple

### API Reference

```py
@property
subscriber_count(self) -> int:
    """Return the total number of subscribers (both weak and strong)."""

@property
logging_enabled(self) -> bool:
    """Check if logging is enabled."""

@property
error_raising(self) -> bool:
    """Check if error raising is enabled."""

toggle_logging(self, enabled: bool = True) -> None:
    """Toggle logging for this signal.
    
    Note that you can also override the `log` method to customize logging behavior, which would
    also override this flag unless you chose to incorporate it."""            

toggle_error_raising(self, enabled: bool = True) -> None:
    """Toggle whether to raise exceptions in subscriber callbacks which are passed to `on_error`.
    
    Note that you can also override the `on_error` method to customize error handling, which would
    also override this flag unless you chose to incorporate it."""

subscribe(self, callback: Callable[[SignalT], None]) -> None:
    """Subscribe to the signal with a callback.

    Args:
        callback: A callable that accepts a single argument of type SignalT.
    Raises:
        SignalError: If the callback is not callable.
    """

unsubscribe(self, subscriber: Any) -> bool:
    """Unsubscribe a subscriber from the signal.
    
    Args:
        subscriber: The subscriber to remove, which can be a class instance or a function.
    Returns:
        bool: True if the subscriber was removed, False if it was not found.
    """

publish(self, data: SignalT) -> None:
    """Publish data to all subscribers. If any subscriber raises an exception,
    it will be caught and passed to the `on_error` method (which just logs by default,
    but can be overridden for custom error handling).
    
    Args:
        data: The data to send to subscribers.
    Raises:
        (Optional) Exception: If a subscriber's callback raises an exception, and `error_raising`
        is True, it will be raised after calling `on_error`.
    """

emit = alias for publish

clear(self) -> None:
    """Clear all subscribers."""

on_error(self, subscriber: Any, callback: Callable[[SignalT], None], error: Exception) -> None:
    """Override this to handle errors differently. This will also override the `error_raising` flag.
    
    Args:
        subscriber: The subscriber that raised the error.
        callback: The callback that raised the error.
        error: The exception that was raised.
    """

log(self, message: str) -> None:
    """Override this to customize logging behavior. This will also override the `logging_enabled` flag.
    
    Args:
        message: The message to log.
    """
```

---

## Questions, Issues, Suggestions?

Use the [issues](https://github.com/edward-jazzhands/ezpubsub/issues) section for bugs or problems, and post ideas or feature requests on the [discussion board](https://github.com/edward-jazzhands/ezpubsub/discussions).

## License

MIT License. See [LICENSE](LICENSE) for details.
