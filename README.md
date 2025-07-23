# EZPubSub

![badge](https://img.shields.io/badge/linted-Ruff-blue?style=for-the-badge&logo=ruff)
![badge](https://img.shields.io/badge/formatted-black-black?style=for-the-badge)
![badge](https://img.shields.io/badge/type_checked-MyPy_(strict)-blue?style=for-the-badge&logo=python)
![badge](https://img.shields.io/badge/type_checked-Pyright_(strict)-blue?style=for-the-badge&logo=python)
![badge](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)

A tiny, modern alternative to [Blinker](https://github.com/pallets-eco/blinker) – typed, thread-safe, and built for today’s Python.

ezpubsub is an ultra-simple pub/sub library for Python. Its only goal is to make publishing and subscribing to events as easy and as safe as possible. No async complexity, no extra features, no dependencies. Just clean, synchronous pub/sub that works anywhere

## Features

- Thread-Safe by Default – Safe to publish and subscribe across threads.
- Strongly Typed with Generics – Signals are fully generic (Signal[str], Signal[MyClass]), letting Pyright/MyPy catch mistakes before runtime. This also unlocks powerful combinations with Typed Objects as signal types.
- Synchronous by Design – 100% sync to keep things predictable. Works fine in async projects.
- Automatic Memory Management – Bound methods are weakly referenced and automatically unsubscribed when their objects are deleted. Normal functions are strongly referenced and must be manually unsubscribed.
- Lightweight & Zero Dependencies – Minimal API, no legacy baggage, designed for 2025-era Python.

## Why ezpubsub / Project philosophy

### Why Build Another Pub/Sub Library?

Pub/sub is one of those deceptively simple patterns that suffers from "everyone should just roll their own" syndrome. It's easy to write a basic working version in 20 lines – just maintain a list of callbacks and call them when something happens. This apparent simplicity has led to dozens of half-baked implementations across the Python ecosystem.

The problem is that building a good pub/sub library requires handling a surprising number of edge cases that only surface with experience: thread safety, memory management, error isolation, subscription lifecycle, weak references, exception handling, and type safety. These aren't obvious when you're sketching out the basic concept.

ezpubsub may be only 167 lines, but every line is deliberate. It's the result of encountering all the ways simpler implementations break in production: memory leaks from orphaned bound methods, race conditions in threaded applications, cascading failures when one subscriber throws an exception, and the endless debugging sessions that come with untyped event data.

The real tragedy is that nobody has seriously attempted to build the right tool. Blinker was the last good effort, but it's 15 years old and shows its age. Everything else falls into two categories: either thrown-together weekend projects that clearly weren't meant to be production-ready, or horrifically over-engineered monstrosities that have a very complex and confusing API, the vast majority of which is unrelated to the core goal of just subscribing to an event.

So I thought, hey I build libraries, why not build a pub/sub library that actually works well in 2025? One that is simple, modern, and designed for the way we write Python today. ezpubsub is that library.

### Why not just use Blinker?

Blinker is an excellent, battle-tested library. If you’re writing a simple, single-threaded, synchronous app (e.g., Flask extensions), Blinker is still a great choice.

However, ezpubsub was designed as a modern alternative:

1. **Full Static Typing with Generics**  
    Blinker’s signals are effectively untyped (Any everywhere). ezpubsub’s Signal[T] lets Pyright/MyPy enforce that subscribers receive the correct data type at development time, as well as unlocks powerful combinations with Typed Objects as signal types. This makes it much easier to catch mistakes before they happen, rather than at runtime.
2. **Thread-Safe by Default**  
    Blinker assumes single-threaded execution. ezpubsub uses proper locking, making it safe in threaded or mixed sync/async environments.
3. **Type Safety Over Dynamic Namespaces**  
    Blinker’s string-based namespaces allow arbitrary signal creation (ns.signal("user_created")), but at the cost of type safety—there’s nothing stopping you from accidentally publishing the wrong object type. ezpubsub treats each signal as an explicitly typed object (Signal[User]), making such mistakes enforced at compile time instead of runtime.

### Why not use an "async-native" pub/sub library?

There are dozens of tiny “AIO pub/sub” libraries on GitHub. I was personally not satisfied with any of them for these reasons:

1. **Async should not be the core mechanism**  
    Pub/sub is just a dispatch mechanism. Whether you call a subscriber directly or schedule it on an event loop is application logic. Some people might say this is a hot take, but I believe in it. It's not terrible to include async support as an option, but it should not be the primary focus of a pub/sub library.
2. **Async-First Usually Means Bad Ergonomics**  
    These libraries often force you into awkward patterns: creating tasks for every subscription, manual event loop juggling, weird API naming. No benefit, more pain.

There is a reason that the most popular pub/sub libraries in the Python ecosystem (blinker, Celery, PyDispatcher, etc) are all synchronous. It’s the simplest, most predictable way to do pub/sub. Async-first versions, in my opinion, are [reinventing the square wheel](https://exceptionnotfound.net/reinventing-the-square-wheel-the-daily-software-anti-pattern/).

I would certainly be open to implementing some very simple async support in future versions (As of writing this it's only 0.1.0!), but it would be an optional feature, and need to follow the same principles of simplicity and ergonomics as the rest of the library.

### Comparison table - ezpubsub vs Blinker

| Feature                   | ezpubsub                 | blinker         | Category        |
| ------------------------- | ------------------------ | --------------- | --------------- |
| Thread-Safe by Default    | ✅ Yes                    | ❌ No            | Core Philosophy |
| Generically Typed Payload | ✅ Yes (Signal[T])        | ❌ No (**kwargs, Any) | Core Philosophy |
| Weak-Reference Support    | ✅ Yes                    | ✅ Yes           | Core Philosophy |
| Sender-Specific Filtering | ❌ No (Not planned)       | ✅ Yes           | Core (Blinker)  |
| Namespacing               | ❌ No (Not planned)       | ✅ Yes           | Core (Blinker)  |
| Async Support             | ❌ Possible future update | ✅ Yes           | Nice-to-have    |
| Decorator API             | ❌ Possible future update | ✅ Yes           | Nice-to-have    |
| Context Managers          | ❌ Possible future update | ✅ Yes           | Nice-to-have    |
| Metasignals (on connect)  | ❌ Possible future update | ✅ Yes           | Nice-to-have    |

## Requirements

- Python 3.10 or higher
- Optional: Enable type checking with [Pyright](http://pyright.org), [MyPy](http://mypy-lang.org), or your checker of choice to get the full benefits of static typing and generics.

## Installation

Install from PyPI:

```sh
pip install ezpubsub
```

Or, with [UV](https://github.com/astral-sh/uv):

```sh
uv add ezpubsub
```

---

## Quick Start

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

## Documentation

### [Click here for full documentation](https://edward-jazzhands.github.io/libraries/ezpubsub/docs/)

---

## Questions, Issues, Suggestions?

Use the [issues](https://github.com/edward-jazzhands/ezpubsub/issues) section for bugs or problems, and post ideas or feature requests on the [discussion board](https://github.com/edward-jazzhands/ezpubsub/discussions).

## License

MIT License. See [LICENSE](LICENSE) for details.
