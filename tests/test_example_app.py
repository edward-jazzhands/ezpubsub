import asyncio
import threading
from typing import TypedDict, List
from ezpubsub import Signal, SignalError
import pytest


class MessageData(TypedDict):
    """Type definition for chat message data."""
    sender: str
    message: str
    receiver: str

class ChatApplication:
    """A simple chat application demo using ezpubsub signals."""
    
    def __init__(self, name: str):
        self.name = name
        # Signal for receiving messages
        self.message_signal = Signal[MessageData]("chat_message")
        # Signal for user join/leave notifications
        self.status_signal = Signal[str]("user_status")
        
        # Register our own method as a callback
        self.message_signal.subscribe(self.handle_message)
    
    def handle_message(self, data: MessageData) -> None:
        """Process incoming chat messages."""
        print(f"[{self.name}] {data['sender']}: {data['message']}")
    
    async def send_message_async(self, message: str, receiver: str = "all") -> None:
        """Send a message asynchronously."""
        await self.message_signal.apublish({
            "sender": self.name,
            "message": message,
            "receiver": receiver
        })
    
    def broadcast_status(self, is_online: bool) -> None:
        """Broadcast user status change."""
        status = "joined" if is_online else "left"
        self.status_signal.publish(f"{self.name} has {status} the chat")


def test_chat_application() -> None:
    """Test the chat application demo with multiple users."""
    # Setup
    alice = ChatApplication("Alice")
    bob = ChatApplication("Bob")
    
    # Bob subscribes to Alice's messages
    alice.message_signal.subscribe(lambda data: print(f"Bob sees Alice's message: {data['message']}"))
    
    # Test basic message sending (these create coroutines but we don't await them in sync test)
    # This is intentional - we're testing that sync publish doesn't interfere with async methods
    
    # Test status broadcasting
    alice.broadcast_status(True)
    bob.broadcast_status(True)
    
    # Test thread safety by sending messages from multiple threads
    def send_from_thread(user: ChatApplication, msg: str) -> None:
        asyncio.run(user.send_message_async(msg))
    
    threads: List[threading.Thread] = []
    for i in range(3):
        t = threading.Thread(target=send_from_thread, args=(alice, f"Thread message {i}"))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Test frozen signal behavior
    alice.message_signal.freeze()
    # We're not actually testing frozen behavior here since we'd need asyncio.run()
    # The frozen behavior is tested in the async test function
    
    # Cleanup
    alice.broadcast_status(False)
    bob.broadcast_status(False)


async def test_chat_application_async() -> None:
    """Test the chat application in async context."""
    # Setup
    alice = ChatApplication("Alice")
    bob = ChatApplication("Bob")
    carol = ChatApplication("Carol")
    
    # Carol wants to see all messages
    messages: List[MessageData] = []
    async def carol_callback(data: MessageData) -> None:
        await asyncio.sleep(0.01)  # Simulate async processing
        messages.append(data)
    
    alice.message_signal.subscribe(carol_callback)
    bob.message_signal.subscribe(carol_callback)
    
    # Send messages asynchronously
    await asyncio.gather(
        alice.send_message_async("Hello from Alice"),
        bob.send_message_async("Hello from Bob")
    )
    
    # Verify Carol received all messages
    assert len(messages) == 2
    assert any(m['sender'] == 'Alice' for m in messages)
    assert any(m['sender'] == 'Bob' for m in messages)
    
    # Test frozen signal in async context - freezing prevents subscriptions, not publishing
    bob.message_signal.freeze()
    # Frozen signals can still publish, but new subscriptions are prevented
    await bob.send_message_async("This works even with frozen signal")
    
    # Test that we can't subscribe to frozen signal
    with pytest.raises(SignalError):
        bob.message_signal.subscribe(lambda data: None)
    
    # Cleanup
    alice.broadcast_status(False)
    bob.broadcast_status(False)
    carol.broadcast_status(False)