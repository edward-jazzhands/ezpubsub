# EZPubSub

[![badge](https://img.shields.io/pypi/v/ezpubsub)](https://pypi.org/project/ezpubsub/)
[![badge](https://img.shields.io/github/v/release/edward-jazzhands/ezpubsub)](https://github.com/edward-jazzhands/ezpubsub/releases/latest)
[![badge](https://img.shields.io/badge/Requires_Python->=3.9-blue&logo=python)](https://python.org)
[![badge](https://img.shields.io/badge/Strictly_Typed-MyPy_&_Pyright-blue&logo=python)](https://mypy-lang.org/)
[![badge](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/license/mit)

A tiny, modern alternative to [Blinker](https://github.com/pallets-eco/blinker) – typed, thread-safe, and designed for today’s Python.

EZPubSub is a zero-dependency pub/sub library focused on one thing: **making event publishing and subscribing easy, safe, and predictable.** No async-first complexity, no dynamic runtime magic—just clean, synchronous pub/sub that works anywhere.

The core design is inspired by the internal signal system in [Textual](https://textual.textualize.io/), refined into a standalone library built for general use.

## Quick Start

```python
from ezpubsub import Signal

data_signal = Signal[str]("data_updated")

def on_data(data: str) -> None:
    print("Received:", data)

data_signal.subscribe(on_data)
data_signal.publish("Hello World")
# Output: Received: Hello World
```

That’s it. You create a signal, subscribe to it, and publish events.

## Why Another Pub/Sub Library?

Because pub/sub in Python is either **old and untyped** or **overengineered and async-first**.

Writing a naive pub/sub system is easy—just keep a list of callbacks and fire them. Writing one that actually works in production is not. You need to handle thread safety, memory management (weak refs for bound methods), error isolation, subscription lifecycles, and type safety. Most libraries get at least one of these wrong.

The last great attempt was Blinker—15 years ago. It was excellent for its time, but Python has moved on. EZPubSub is what a pub/sub library should look like in 2025: type-safe, thread-safe, ergonomic, and designed for modern Python.

## Features

* **Thread-Safe by Default** – Publish and subscribe safely across threads.
* **Strongly Typed with Generics** – `Signal[str]`, `Signal[MyClass]`, or even TypedDict/dataclasses for structured events. Pyright/MyPy catches mistakes before runtime.
* **Synchronous First (Async Optional)** – Works in any environment, including mixed sync/async projects.
* **Automatic Memory Management** – Bound methods are weakly referenced and auto-unsubscribed when their objects are deleted.
* **No Runtime Guesswork** – No `**kwargs`, no stringly-typed namespaces, no dynamic channel lookups.
* **Lightweight & Zero Dependencies** – Only what you need, nothing else.

## How It Compares

### EZPubSub vs Blinker

Blinker is great for simple, single-threaded Flask-style apps. But:

| Feature           | EZPubSub                           | Blinker                                           |
| ----------------- | ---------------------------------- | ------------------------------------------------- |
| **Typing**        | ✅ Full static typing (`Signal[T]`) | ❌ Untyped (`Any`)                                 |
| **Thread Safety** | ✅ Built-in                         | ❌ Single-threaded only                            |
| **Design**        | ✅ Instance-based, type-safe        | ⚠️ Channel-based (runtime filtering, string keys) |
| **Weak Refs**     | ✅ Automatic                        | ✅ Automatic                                       |

If you’re starting a new project in 2025, you deserve type checking and thread safety out of the box.

### EZPubSub vs AioSignal

[`aiosignal`](https://github.com/aio-libs/aiosignal) is excellent for its niche—managing fixed async callbacks inside `aiohttp`—but unsuitable as a general pub/sub system:

| Limitation             | Why It Matters                                                         |
| ---------------------- | ---------------------------------------------------------------------- |
| **Async-Only**         | Forces you to rewrite sync code or wrap callbacks in event loop tasks. |
| **Frozen Subscribers** | You must `freeze()` before sending; no dynamic add/remove at runtime.  |
| **No Thread Safety**   | Assumes a single event loop context.                                   |
| **Loose Typing**       | Allows arbitrary `**kwargs`, undermining type safety.                  |

`aiosignal` is great if you’re writing an `aiohttp` extension. But if you need a general-purpose pub/sub system that works in any context, it's not the greatest fit.

### Why Not Async-First Libraries?

Pub/sub is just a dispatch mechanism. Whether you await data before publishing is application logic—not the library’s job. Async-first libraries complicate what should be simple: they force you to juggle tasks, event loops, and weird APIs for no real benefit.

Synchronous first, with optional async support, is simpler and more predictable. That’s why Blinker, Celery, and PyDispatcher all share this design—and why EZPubSub does too.

---

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

Allowing arbitrary keyword arguments is convenient—but it destroys type safety.

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

This forces better API design and catches mistakes at compile time instead of runtime. If you need flexible payloads, use TypedDicts, dataclasses, or even a `Union` of event types.

---

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

---

### Why This Library Exists

Because the Python ecosystem needed a **modern, type-safe, thread-safe pub/sub library that doesn’t suck.**

EZPubSub is {167} deliberate lines of code that exist for one reason: to make event-driven Python sane again.
