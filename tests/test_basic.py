from typing import TypedDict
import asyncio
from ezpubsub import Signal

class MyTypedDict(TypedDict):
    name: str
    age: int
    coolness: float
    ready: bool
    

def test_signal() -> None:

    signal = Signal[MyTypedDict]("test_signal")

    def some_callback(data: MyTypedDict) -> None:
        assert data["name"] == "Alice"
        assert data["age"] == 30
        assert data["coolness"] == 9.5
        assert data["ready"] is True

    signal.subscribe(some_callback)
    signal.publish({
        "name": "Alice",
        "age": 30,
        "coolness": 9.5,
        "ready": True
    })


async def test_signal_async() -> None:
    signal = Signal[MyTypedDict]("test_signal_async")

    async def some_callback(data: MyTypedDict) -> None:
        await asyncio.sleep(0.1)
        assert data["name"] == "Bob"
        assert data["age"] == 25
        assert data["coolness"] == 8.0
        assert data["ready"] is False

    signal.subscribe(some_callback)
    await signal.apublish({
        "name": "Bob",
        "age": 25,
        "coolness": 8.0,
        "ready": False
    })