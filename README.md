# EZPubSub

[![badge](https://img.shields.io/pypi/v/ezpubsub)](https://pypi.org/project/ezpubsub/)
[![badge](https://img.shields.io/github/v/release/edward-jazzhands/ezpubsub)](https://github.com/edward-jazzhands/ezpubsub/releases/latest)
[![badge](https://img.shields.io/badge/Requires_Python->=3.9-blue&logo=python)](https://python.org)
[![badge](https://img.shields.io/badge/Strictly_Typed-MyPy_&_Pyright-blue&logo=python)](https://mypy-lang.org/)
[![badge](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/license/mit)

A tiny, modern alternative to [Blinker](https://github.com/pallets-eco/blinker) – typed, thread-safe, sync or async, and designed for today’s Python.

EZPubSub is a zero-dependency pub/sub library focused on one thing: **making event publishing and subscribing easy, safe, and predictable.** No over-engineered, confusing API. No unnecessary features. Just clean, easy pub/sub that works anywhere.

The core design is inspired by the internal signal system in [Textual](https://textual.textualize.io/), refined into a standalone library built for general use.

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

async_data_signal.asubscribe(on_async_data)
await async_data_signal.apublish("Hello Async World")
# Output: Async Received: Hello Async World
```

That’s it. You create a signal, subscribe to it, and publish events.

## Why Another Pub/Sub Library?

Because pub/sub in Python is either **old and untyped** or **overengineered and async-only**.

Writing a naive pub/sub system is easy. Just keep a list of callbacks and fire them. Writing one that actually works in production is not. You need to handle thread safety, memory management (weak refs for bound methods), error isolation, subscription lifecycles, and type safety. Most libraries get at least one of these wrong.

The last great attempt was Blinker, 15 years ago. It was excellent for its time, but Python has moved on. EZPubSub is what a pub/sub library should look like in 2025: type-safe, thread-safe, ergonomic, and designed for modern Python.

## Features

* **Thread-Safe by Default** – Publish and subscribe safely across threads.
* **Strongly Typed with Generics** – `Signal[str]`, `Signal[MyClass]`, or even TypedDict/dataclasses for structured events. Pyright/MyPy catches mistakes before runtime.
* **Sync or Async** – Works in any environment, including mixed sync/async projects.
* **Automatic Memory Management** – Bound methods are weakly referenced and auto-unsubscribed when their objects are deleted.
* **No Runtime Guesswork** – No `**kwargs`, no stringly-typed namespaces, no dynamic channel lookups. Opinionated design that enforces type safety and clarity.
* **Lightweight & Zero Dependencies** – Only what you need.

## How It Compares

### EZPubSub vs Blinker

Blinker is great for simple, single-threaded Flask-style apps. But:

| Feature           | EZPubSub                            | Blinker                                            |
| ----------------- | ----------------------------------- | -------------------------------------------------- |
| **Design**        | ✅ Instance-based, type-safe        | ⚠️ Channel-based (runtime filtering, string keys) |
| **Weak Refs**     | ✅ Automatic                        | ✅ Automatic                                      |
| **Type Checking** | ✅ Full static typing (`Signal[T]`) | ❌ Untyped (`Any`)                                |
| **Thread Safety** | ✅ Built-in                         | ❌ Single-threaded only                           |

If you’re starting a new project in 2025, you deserve type checking and thread safety out of the box.

### EZPubSub vs AioSignal

[`aiosignal`](https://github.com/aio-libs/aiosignal) is excellent for its niche—managing fixed async callbacks inside `aiohttp`—but unsuitable as a general pub/sub system:

| Feature                  | EZPubSub                             | AioSignal                                                             |
| ------------------------ | ------------------------------------ | --------------------------------------------------------------------- |
| **Sync and Async**       | ✅ Sync and Async friendly           | ❌ Sync publishing not available                                     |
| **Freezing Subscribers** | ✅ Optional in both Sync and Async   | ❌ `freeze()` required to publish; no dynamic add/remove at runtime  |
| **Type Checking**        | ✅ Full static typing (`Signal[T]`)  | ⚠️ Allows arbitrary `**kwargs`, undermining type safety              |
| **Thread Safety**        | ✅ Built-in                          | ❌ Single-threaded only                                              |

`aiosignal` is great if you’re writing an `aiohttp` extension. But being required to use async everywhere just to publish signals is unnecessary for most applications. Synchronous first, with optional async support, is simpler and more predictable. That’s why Blinker, Celery, and Django's internal PubSub (based on PyDispatcher) all share this design.

## Design Philosophy

### Signals vs Channels

EZPubSub uses **one object per signal**, instead of Blinker’s **“one channel, many signals”** model.

**Blinker (channel-based):**

```python
user_signal = Signal()  
user_signal.connect(login_handler, sender=LoginService)
user_signal.send(sender=LoginService, user=user)
```

**EZPubSub (instance-based):**

```python
login_signal = Signal[LoginEvent]("user_login")
login_signal.subscribe(login_handler)
login_signal.publish(LoginEvent(user=user))
```

This matters because:

* **No filtering** – Each signal already represents one event type.
* **No runtime lookups** – You never hunt down signals by string name.
* **Type safety** – Wrong event types are caught by your IDE/type checker.

Fewer magic strings, fewer runtime bugs, and code that reads like what it does.

### Why No `**kwargs`?

Allowing arbitrary keyword arguments is convenient, but it destroys type safety.

```python
# Bad: fragile, stringly typed
signal.publish(user, session_id="abc123", ip="1.2.3.4")

# Good: explicit, type-safe
@dataclass
class UserLoginEvent:
    user: User
    session_id: str
    ip: str

signal.publish(UserLoginEvent(user, "abc123", "1.2.3.4"))
```

This forces better API design and catches mistakes at compile time instead of runtime. EZPubSub is opinionated about this: **no `**kwargs`**. Every signal has a specific type.

It is of course possible to simply not use any type hinting when creating a signal (or use `Any`), as type hints in Python are optional. But the library is designed to encourage type safety by default. As for why you would ever want to create a signal using `Any` or without a type hint, I won't ask any questions ;)

## Installation

```sh
pip install ezpubsub
```

Or with [UV](https://github.com/astral-sh/uv):

```sh
uv add ezpubsub
```

Requires Python 3.10+.

---

## Documentation

Full docs: [**Click here**](https://edward-jazzhands.github.io/libraries/ezpubsub/docs/)

---

## License

MIT License. See [LICENSE](LICENSE) for details.
