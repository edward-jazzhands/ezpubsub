import threading
from functools import partial
import asyncio
from ezpubsub import Signal

def test_signal_in_threads() -> None:
    """Test signal usage across multiple threads."""

    signal = Signal[str]("thread_test")
    results: list[str] = []
    
    def callback(msg: str) -> None:
        results.append(msg)
    
    signal.subscribe(callback)
    
    threads: list[threading.Thread] = []
    for i in range(3):
        t = threading.Thread(
            target=lambda: signal.publish(f"Message from thread {i}")
        )
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    assert len(results) == 3
    assert any("Message from thread 0" in r for r in results)
    assert any("Message from thread 1" in r for r in results)
    assert any("Message from thread 2" in r for r in results)

async def test_async_signal_in_threads() -> None:
    """Test async signal usage with threads."""

    signal = Signal[str]("async_thread_test")
    results: list[str] = []
    
    async def callback(msg: str) -> None:
        await asyncio.sleep(0.01)
        results.append(msg)
    
    signal.subscribe(callback)
    
    # Create a new event loop for each thread
    async def thread_worker(msg: str) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            await signal.apublish(msg)
        finally:
            loop.close()

    def thread_target(msg: str) -> None:
        asyncio.run(thread_worker(msg))
    
    threads: list[threading.Thread] = []
    for i in range(3):
        t = threading.Thread(
            target=partial(thread_target, f"Async message {i}")
        )
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    assert len(results) == 3
    assert any("Async message 0" in r for r in results)
    assert any("Async message 1" in r for r in results)
    assert any("Async message 2" in r for r in results)

async def test_async_and_sync_in_threads() -> None:
    """Test sending both async and sync signals at the same time, in threads."""

    signal = Signal[str]("async_thread_test")
    results: list[str] = []
    
    async def callback(msg: str) -> None:
        await asyncio.sleep(0.01)
        results.append(f"{msg} (async)")

    def sync_callback(msg: str) -> None:
        results.append(f"{msg} (sync)")
    
    signal.subscribe(callback)
    signal.subscribe(sync_callback)
    
    # Create a new event loop for each thread
    async def thread_worker(msg: str) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            await signal.apublish(msg, also_sync=True)
        finally:
            loop.close()

    def thread_target(msg: str) -> None:
        asyncio.run(thread_worker(msg))
    
    t = threading.Thread(
        target=partial(thread_target, "Message from thread")
    )
    t.start()
    t.join()
    
    assert len(results) == 2
    assert results[0] == "Message from thread (async)"
    assert results[1] == "Message from thread (sync)"


async def test_apublish_also_sync_arg() -> None:
    """Test that the `also_sync` argument works correctly with async signals in threads."""

    signal = Signal[str]("async_thread_test")
    results: list[str] = []
    
    async def callback(msg: str) -> None:
        await asyncio.sleep(0.01)
        results.append(f"{msg} (async)")

    # The sync callback will NOT be called if `also_sync=False`
    def sync_callback(msg: str) -> None:
        results.append(f"{msg} (sync)")
    
    signal.subscribe(callback)
    signal.subscribe(sync_callback)
    
    # `also_sync` is False by default. So this will only call the async callback.
    await signal.apublish("Message from thread")
    assert len(results) == 1
    assert results[0] == "Message from thread (async)"
