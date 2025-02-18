# tests/unit/test_in_memory_event_bus.py
from typing import List
from dataclasses import dataclass
import pytest

from src.infrastructure.event_bus.in_memory_event_bus import InMemoryEventBus
from src.application.events.event import Event


@dataclass(frozen=True)
class TestEvent(Event):
    """Test event for testing purposes"""
    message: str


@dataclass(frozen=True)
class AnotherTestEvent(Event):
    """Another test event for testing purposes"""
    value: int


class TestEventHandler:
    """Test handler that records received events"""

    def __init__(self):
        self.received_events: List[Event] = []

    async def handle(self, event: TestEvent) -> None:
        """Handle test event"""
        self.received_events.append(event)


class AnotherTestEventHandler:
    """Test handler for another type of event"""

    def __init__(self):
        self.received_events: List[Event] = []

    async def handle(self, event: AnotherTestEvent) -> None:
        """Handle another test event"""
        self.received_events.append(event)


class FailingEventHandler:
    """Test handler that throws an exception"""

    def __init__(self):
        self.called = False

    async def handle(self, event: TestEvent) -> None:
        """Handle that throws an exception"""
        self.called = True
        raise ValueError("Handler error")

class TestInMemoryEventBus:
    """Test cases for InMemoryEventBus"""

    @pytest.fixture
    def event_bus(self) -> InMemoryEventBus:
        """Create a new event bus instance"""
        return InMemoryEventBus()

    @pytest.fixture
    def test_event(self) -> TestEvent:
        """Create a test event"""
        return TestEvent(message="test message")

    @pytest.fixture
    def another_test_event(self) -> AnotherTestEvent:
        """Create another test event"""
        return AnotherTestEvent(value=42)

    @pytest.fixture
    def test_handler(self) -> TestEventHandler:
        """Create a test event handler"""
        return TestEventHandler()

    @pytest.fixture
    def another_test_handler(self) -> AnotherTestEventHandler:
        """Create another test event handler"""
        return AnotherTestEventHandler()

    @pytest.fixture
    def failing_handler(self) -> FailingEventHandler:
        """Create a handler that throws an exception"""
        return FailingEventHandler()

    @pytest.mark.asyncio
    async def test_subscribe_registers_handler(
            self,
            event_bus: InMemoryEventBus,
            test_handler: TestEventHandler
    ):
        """Test that handler is correctly registered"""
        event_bus.subscribe(TestEvent, test_handler.handle)

        assert TestEvent in event_bus._handlers
        assert test_handler.handle in event_bus._handlers[TestEvent]

    @pytest.mark.asyncio
    async def test_subscribe_and_publish_event(
            self,
            event_bus: InMemoryEventBus,
            test_event: TestEvent,
            test_handler: TestEventHandler
    ):
        """Should deliver event to subscribed handler"""
        event_bus.subscribe(TestEvent, test_handler.handle)

        await event_bus.publish(test_event)

        assert len(test_handler.received_events) == 1
        assert test_handler.received_events[0] == test_event

    @pytest.mark.asyncio
    async def test_multiple_handlers_same_event(
            self,
            event_bus: InMemoryEventBus,
            test_event: TestEvent
    ):
        """Should deliver event to multiple handlers"""
        first_handler = TestEventHandler()
        second_handler = TestEventHandler()
        event_bus.subscribe(TestEvent, first_handler.handle)
        event_bus.subscribe(TestEvent, second_handler.handle)

        await event_bus.publish(test_event)

        assert len(first_handler.received_events) == 1
        assert len(second_handler.received_events) == 1
        assert first_handler.received_events[0] == test_event
        assert second_handler.received_events[0] == test_event

    @pytest.mark.asyncio
    async def test_multiple_event_types(
            self,
            event_bus: InMemoryEventBus,
            test_event: TestEvent,
            another_test_event: AnotherTestEvent,
            test_handler: TestEventHandler,
            another_test_handler: AnotherTestEventHandler
    ):
        """Should handle different event types correctly"""
        event_bus.subscribe(TestEvent, test_handler.handle)
        event_bus.subscribe(AnotherTestEvent, another_test_handler.handle)

        await event_bus.publish(test_event)
        await event_bus.publish(another_test_event)

        assert len(test_handler.received_events) == 1
        assert len(another_test_handler.received_events) == 1
        assert test_handler.received_events[0] == test_event
        assert another_test_handler.received_events[0] == another_test_event

    @pytest.mark.asyncio
    async def test_unsubscribe_handler(
            self,
            event_bus: InMemoryEventBus,
            test_event: TestEvent,
            test_handler: TestEventHandler
    ):
        """Should not deliver events after unsubscribing"""
        event_bus.subscribe(TestEvent, test_handler.handle)
        await event_bus.publish(test_event)
        assert len(test_handler.received_events) == 1

        event_bus.unsubscribe(TestEvent, test_handler.handle)
        await event_bus.publish(test_event)

        assert len(test_handler.received_events) == 1  # Count should not increase

    @pytest.mark.asyncio
    async def test_publish_with_no_handlers(
            self,
            event_bus: InMemoryEventBus,
            test_event: TestEvent
    ):
        """Should handle publishing event with no subscribers"""
        # When/Then - Should not raise any exception
        await event_bus.publish(test_event)

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_handler(
            self,
            event_bus: InMemoryEventBus,
            test_handler: TestEventHandler
    ):
        """Should handle unsubscribing non-existent handler"""
        # When/Then - Should not raise any exception
        event_bus.unsubscribe(TestEvent, test_handler.handle)

    @pytest.mark.asyncio
    async def test_handler_exception_does_not_affect_other_handlers(
            self,
            event_bus: InMemoryEventBus,
            test_event: TestEvent,
            test_handler: TestEventHandler,
            failing_handler: FailingEventHandler
    ):
        """Should continue processing handlers even if one fails"""
        event_bus.subscribe(TestEvent, failing_handler.handle)
        event_bus.subscribe(TestEvent, test_handler.handle)

        await event_bus.publish(test_event)

        assert failing_handler.called  # Handler was called
        assert len(test_handler.received_events) == 1  # Other handler still processed
        assert test_handler.received_events[0] == test_event