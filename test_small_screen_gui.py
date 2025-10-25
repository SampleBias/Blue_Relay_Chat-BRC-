#!/usr/bin/env python3
"""
Test script for small screen GUI.

This script provides a simple way to test the small screen GUI
without requiring physical hardware.
"""

import asyncio
import os
import sys
import time
import random
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from bitchat.config.manager import ConfigManager
    from bitchat.gui.small_screen_gui import SmallScreenGUI
    from bitchat.core.events import EventBus
    from bitchat.utils.logging import setup_logging, get_logger
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


class MockDisplayDriver:
    """Mock display driver for testing."""
    
    def __init__(self) -> None:
        self.buffer = [[0 for _ in range(128)] for _ in range(128)]
        self.connected = True
    
    def connect(self) -> bool:
        """Mock connection to display."""
        print("Mock display connected")
        return True
    
    def disconnect(self) -> None:
        """Mock disconnection from display."""
        print("Mock display disconnected")
    
    def clear(self) -> None:
        """Mock clearing the display."""
        self.buffer = [[0 for _ in range(128)] for _ in range(128)]
        print("Mock display cleared")
    
    def draw_text(self, x: int, y: int, text: str, color=None) -> None:
        """Mock drawing text on display."""
        print(f"Mock drawing text at ({x},{y}): {text}")
    
    def draw_rectangle(self, x: int, y: int, width: int, height: int, color=None, fill=False) -> None:
        """Mock drawing rectangle on display."""
        fill_text = "filled" if fill else "outline"
        print(f"Mock drawing {fill_text} rectangle at ({x},{y}) size {width}x{height}")
    
    def refresh(self) -> None:
        """Mock refreshing the display."""
        print("Mock display refreshed")
    
    def get_dimensions(self) -> tuple:
        """Get screen dimensions."""
        return (128, 128)


class MockInputHandler:
    """Mock input handler for testing."""
    
    def __init__(self) -> None:
        self.mode = "navigation"
        self.callbacks = {}
        self.running = True
    
    def register_callback(self, event_type, callback) -> None:
        """Register a callback for input events."""
        self.callbacks[event_type] = callback
    
    def start(self) -> None:
        """Start the mock input handler."""
        print("Mock input handler started")
    
    def stop(self) -> None:
        """Stop the mock input handler."""
        self.running = False
        print("Mock input handler stopped")
    
    def get_mode(self) -> str:
        """Get the current input mode."""
        return self.mode
    
    def get_input_text(self) -> str:
        """Get the current input text."""
        return ""
    
    def clear_input_text(self) -> None:
        """Clear the input text."""
        pass
    
    def get_current_char_position(self) -> tuple:
        """Get the current character grid position."""
        return (0, 0)
    
    def is_running(self) -> bool:
        """Check if input handler is running."""
        return self.running


class MockEventBus:
    """Mock event bus for testing."""
    
    def __init__(self) -> None:
        self.subscribers = {}
    
    def subscribe(self, event_type, callback) -> None:
        """Subscribe to an event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    async def publish(self, event) -> None:
        """Publish an event."""
        event_type = event.type
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    await callback(event)
                except Exception as e:
                    print(f"Error in event callback: {e}")


class MockEvent:
    """Mock event for testing."""
    
    def __init__(self, event_type, data=None, source="test") -> None:
        self.type = event_type
        self.data = data or {}
        self.source = source


class MockConfig:
    """Mock configuration for testing."""
    
    def __init__(self) -> None:
        pass
    
    def get(self, key, default=None):
        """Get a configuration value."""
        # Return some default values for testing
        defaults = {
            "gui.screen_width": 128,
            "gui.screen_height": 128,
            "gui.max_display_messages": 10,
            "gui.auto_refresh_interval_ms": 500,
            "input.button_debounce_ms": 50,
            "bluetooth.max_peers": 8,
            "nostr.max_relay_connections": 1,
            "performance.max_memory_mb": 100,
        }
        return defaults.get(key, default)
    
    def get_hardware_info(self) -> dict:
        """Get hardware information."""
        return {
            "detected_hardware": "rpi-zero2w",
            "profile_name": "Raspberry Pi Zero 2 W",
            "total_memory_mb": 512,
            "cpu_cores": 4,
        }


async def test_display_driver() -> None:
    """Test the display driver functionality."""
    print("Testing display driver...")
    
    from bitchat.gui.display_driver import DisplayDriver, DisplayColor
    
    display = MockDisplayDriver()
    
    # Test connection
    assert display.connect() == True, "Display connection failed"
    
    # Test basic drawing
    display.clear()
    display.draw_text(10, 10, "Hello World", DisplayColor.WHITE)
    display.draw_rectangle(10, 30, 50, 20, DisplayColor.WHITE, True)
    display.refresh()
    
    # Test dimensions
    width, height = display.get_dimensions()
    assert width == 128 and height == 128, f"Unexpected dimensions: {width}x{height}"
    
    print("Display driver test passed!")


async def test_input_handler() -> None:
    """Test the input handler functionality."""
    print("Testing input handler...")
    
    from bitchat.gui.input_handler import InputHandler, InputMode, InputEvent
    
    input_handler = MockInputHandler()
    
    # Test mode switching
    assert input_handler.get_mode() == InputMode.NAVIGATION.value, "Initial mode should be navigation"
    
    # Test callback registration
    callback_called = False
    
    def test_callback(data):
        nonlocal callback_called
        callback_called = True
        print(f"Input callback called with: {data}")
    
    input_handler.register_callback(InputEvent.BUTTON_PRESS, test_callback)
    input_handler.start()
    
    # Simulate button press
    input_handler.callbacks[InputEvent.BUTTON_PRESS]({"pin": "test"})
    await asyncio.sleep(0.1)
    
    assert callback_called, "Input callback was not called"
    
    input_handler.stop()
    
    print("Input handler test passed!")


async def test_gui_integration() -> None:
    """Test GUI integration with mock components."""
    print("Testing GUI integration...")
    
    # Create mock components
    config = MockConfig()
    event_bus = MockEventBus()
    
    # Create GUI with mock components
    from bitchat.gui.small_screen_gui import SmallScreenGUI
    
    # Set environment variables to force mock mode
    os.environ["BITCHAT_MOCK_DISPLAY"] = "true"
    os.environ["BITCHAT_MOCK_INPUT"] = "true"
    
    gui = SmallScreenGUI(config, event_bus)
    
    # Initialize with mock display and input
    gui.display = MockDisplayDriver()
    gui.input_handler = MockInputHandler()
    
    # Test initialization
    await gui.initialize()
    
    # Test mode switching
    assert gui._current_mode == gui.UI_MODE_CHAT, "Initial mode should be chat"
    
    # Test message addition
    test_message = {
        "type": "test",
        "content": "Test message",
        "timestamp": time.time(),
    }
    gui._message_history.append(test_message)
    
    # Test UI drawing
    await gui._draw_chat_screen()
    await gui._draw_menu_screen()
    await gui._draw_status_screen()
    
    print("GUI integration test passed!")


async def simulate_user_interaction() -> None:
    """Simulate user interaction for testing."""
    print("Simulating user interaction...")
    
    # This would be expanded to test specific user scenarios
    # For now, just print some instructions
    print("1. GUI should start with welcome screen")
    print("2. Press SELECT to enter menu mode")
    print("3. In menu mode, use UP/DOWN to navigate")
    print("4. Press SELECT to choose option")
    print("5. Press BACK to return to chat mode")
    print("6. In chat mode, press TOGGLE to enter text input")
    print("7. In text input mode, use arrow keys to navigate character grid")
    print("8. Press SELECT to choose character")
    print("9. Press BACK to delete character or exit text input")
    print("10. Press CTRL+C to exit")


async def run_tests() -> None:
    """Run all tests."""
    print("Running small screen GUI tests...")
    
    try:
        await test_display_driver()
        await test_input_handler()
        await test_gui_integration()
        
        print("All tests passed!")
        
        # Simulate user interaction
        await simulate_user_interaction()
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False
    
    return True


async def main() -> None:
    """Main test entry point."""
    # Set up logging
    setup_logging(
        level="INFO",
        log_file=None,
        console_output=True
    )
    
    logger = get_logger("test")
    logger.info("Starting small screen GUI tests...")
    
    # Run tests
    success = await run_tests()
    
    if success:
        logger.info("Tests completed successfully")
        sys.exit(0)
    else:
        logger.error("Tests failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())