import pytest
from ezpubsub import Signal, SignalError


def test_frozen_signal_subscription() -> None:
    """Test that subscription fails when signal is frozen."""
    signal = Signal[str]("frozen_test", require_freeze=True)
    signal.freeze()
    
    with pytest.raises(SignalError, match="Cannot subscribe to frozen signal"):
        signal.subscribe(lambda x: None)


def test_frozen_signal_publishing() -> None:
    """Test that publishing fails when signal is not frozen but requires it."""
    signal = Signal[str]("require_freeze_test", require_freeze=True)
    
    def callback(msg: str) -> None:
        pass
    
    signal.subscribe(callback)
    
    with pytest.raises(
        SignalError, 
        match="Cannot send non-frozen signal - call `freeze` first or set require_freeze=False"
    ):
        signal.publish("should fail")
    
    signal.freeze()
    signal.publish("should pass")  # Should not raise