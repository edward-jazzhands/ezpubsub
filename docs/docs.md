# EZPubSub<br>Documentation and Guide

## Requirements

- Python 3.10 or higher
- Optional: Enable type checking with [Pyright](http://pyright.org), [MyPy](http://mypy-lang.org), or your checker of choice to get the full benefits of static typing and generics.

## Installation

```sh
pip install ezpubsub
```

Or, with [UV](https://github.com/astral-sh/uv):

```sh
uv add ezpubsub
```

## Quick Start

Synchronous signal:

```python
from ezpubsub import Signal

data_signal = Signal[str]()

def on_data(data: str) -> None:
    print("Received:", data)

data_signal.subscribe(on_data)
data_signal.publish("Hello World")
# Output: Received: Hello World
```

Asynchronous signal with callback:

```python
from ezpubsub import Signal

async_data_signal = Signal[str]("My Database Update")

async def on_async_data(data: str) -> None:
    await asyncio.sleep(1)  # Simulate async work
    print("Async Received:", data)

async_data_signal.subscribe(on_async_data)
await async_data_signal.apublish("Hello Async World")
# Output: Async Received: Hello Async World
```

## Basic Usage Example

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

## Methods or Functions

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

## Using in Threads / Thread Safety

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

## Using Typed Objects for Signal Types

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

## Overriding Logging and Error Handling

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

## Global Signal / Bridging Frameworks

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

## Memory Management

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