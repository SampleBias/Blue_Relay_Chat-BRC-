"""
Input handler for toggle/button keyboard interface.

This module provides input handling for a simple toggle/button interface
optimized for small screen chat applications.
"""

import time
import threading
from typing import Optional, Callable, Dict, Any
from enum import Enum

from ..utils.logging import get_logger


class InputEvent(Enum):
    """Input event types."""
    TOGGLE_PRESS = "toggle_press"
    TOGGLE_RELEASE = "toggle_release"
    BUTTON_PRESS = "button_press"
    BUTTON_RELEASE = "button_release"
    NAVIGATE_UP = "navigate_up"
    NAVIGATE_DOWN = "navigate_down"
    NAVIGATE_LEFT = "navigate_left"
    NAVIGATE_RIGHT = "navigate_right"
    SELECT = "select"
    BACK = "back"
    MODE_CHANGE = "mode_change"


class InputMode(Enum):
    """Input modes for different functionality."""
    NAVIGATION = "navigation"
    TEXT_INPUT = "text_input"
    COMMAND_SELECT = "command_select"


class InputHandler:
    """Input handler for toggle/button interface."""
    
    # GPIO pin configuration for Raspberry Pi Zero 2 W
    DEFAULT_GPIO_CONFIG = {
        "toggle_pin": 17,      # Main toggle/enter button
        "up_pin": 22,          # Up navigation
        "down_pin": 23,         # Down navigation  
        "left_pin": 24,         # Left navigation
        "right_pin": 25,        # Right navigation
        "select_pin": 27,       # Select/confirm button
        "back_pin": 5,          # Back/cancel button
        "mode_pin": 6,          # Mode toggle button
    }
    
    # Character selection grid for text input mode
    CHAR_GRID = [
        ['A', 'B', 'C', 'D', 'E', 'F', 'G'],
        ['H', 'I', 'J', 'K', 'L', 'M', 'N'],
        ['O', 'P', 'Q', 'R', 'S', 'T', 'U'],
        ['V', 'W', 'X', 'Y', 'Z', ' ', '.'],
        ['0', '1', '2', '3', '4', '5', '6'],
        ['7', '8', '9', '-', '_', '.', ','],
    ]
    
    def __init__(self, gpio_config: Optional[Dict[str, int]] = None) -> None:
        """
        Initialize input handler.
        
        Args:
            gpio_config: Custom GPIO pin configuration
        """
        self.logger = get_logger("input_handler")
        self.gpio_config = gpio_config or self.DEFAULT_GPIO_CONFIG
        
        # Input state
        self._running = False
        self._mode = InputMode.NAVIGATION
        self._current_char_pos = (0, 0)  # Row, col in CHAR_GRID
        self._input_text = ""
        self._debounce_time = 0.05  # 50ms debounce
        
        # GPIO state tracking
        self._gpio_state = {}
        self._last_press_time = {}
        
        # Event callbacks
        self._event_callbacks: Dict[str, Callable] = {}
        
        # Threading
        self._lock = threading.Lock()
        self._monitor_thread: Optional[threading.Thread] = None
        
        self.logger.info("Input handler initialized")
    
    def register_callback(self, event_type: InputEvent, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a callback for specific input events.
        
        Args:
            event_type: Type of event to handle
            callback: Callback function to call
        """
        self._event_callbacks[event_type.value] = callback
    
    def start(self) -> None:
        """Start input monitoring."""
        if self._running:
            self.logger.warning("Input handler is already running")
            return
        
        try:
            # Initialize GPIO
            self._initialize_gpio()
            
            # Start monitoring thread
            self._running = True
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()
            
            self.logger.info("Input handler started")
            
        except Exception as e:
            self.logger.error(f"Failed to start input handler: {e}")
    
    def stop(self) -> None:
        """Stop input monitoring."""
        self._running = False
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
        
        self._cleanup_gpio()
        self.logger.info("Input handler stopped")
    
    def _initialize_gpio(self) -> None:
        """Initialize GPIO pins for input."""
        try:
            import RPi.GPIO as GPIO
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Set up all pins as inputs with pull-up resistors
            for pin_name, pin_number in self.gpio_config.items():
                GPIO.setup(pin_number, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                self._gpio_state[pin_name] = GPIO.HIGH  # Pull-up means HIGH when not pressed
                self._last_press_time[pin_name] = 0
            
            self.logger.info("GPIO initialized for input")
            
        except ImportError:
            self.logger.warning("RPi.GPIO not available, using mock input")
            self._setup_mock_gpio()
        except Exception as e:
            self.logger.error(f"Failed to initialize GPIO: {e}")
            raise
    
    def _setup_mock_gpio(self) -> None:
        """Set up mock GPIO for testing without hardware."""
        for pin_name in self.gpio_config:
            self._gpio_state[pin_name] = True  # True = not pressed
            self._last_press_time[pin_name] = 0
    
    def _cleanup_gpio(self) -> None:
        """Clean up GPIO resources."""
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
            self.logger.info("GPIO cleaned up")
        except ImportError:
            pass  # Mock GPIO was used
        except Exception as e:
            self.logger.error(f"Error cleaning up GPIO: {e}")
    
    def _monitor_loop(self) -> None:
        """Main input monitoring loop."""
        try:
            import RPi.GPIO as GPIO
        except ImportError:
            # Mock mode for testing
            GPIO = None
        
        while self._running:
            current_time = time.time()
            
            if GPIO:
                # Read actual GPIO state
                for pin_name, pin_number in self.gpio_config.items():
                    try:
                        current_state = GPIO.input(pin_number)
                        self._process_gpio_change(pin_name, current_state, current_time)
                    except:
                        pass  # Ignore GPIO read errors
            else:
                # Mock mode - simulate some input for testing
                self._simulate_mock_input(current_time)
            
            time.sleep(0.01)  # 10ms polling
    
    def _process_gpio_change(self, pin_name: str, current_state: int, current_time: float) -> None:
        """
        Process GPIO state change with debouncing.
        
        Args:
            pin_name: Name of the GPIO pin
            current_state: Current state of the pin
            current_time: Current timestamp
        """
        with self._lock:
            last_state = self._gpio_state.get(pin_name, True)
            last_time = self._last_press_time.get(pin_name, 0)
            
            # Check for state change with debouncing
            if current_state != last_state:
                if current_state == GPIO.LOW:  # Button pressed (pull-up)
                    if current_time - last_time > self._debounce_time:
                        self._handle_button_press(pin_name, current_time)
                else:
                    self._handle_button_release(pin_name, current_time)
                
                self._gpio_state[pin_name] = current_state
                
                if current_state == GPIO.LOW:
                    self._last_press_time[pin_name] = current_time
    
    def _handle_button_press(self, pin_name: str, press_time: float) -> None:
        """Handle button press based on current mode."""
        if self._mode == InputMode.NAVIGATION:
            self._handle_navigation_press(pin_name)
        elif self._mode == InputMode.TEXT_INPUT:
            self._handle_text_input_press(pin_name)
        elif self._mode == InputMode.COMMAND_SELECT:
            self._handle_command_select_press(pin_name)
        
        # Trigger callback
        self._trigger_callback(InputEvent.BUTTON_PRESS, {
            "pin": pin_name,
            "time": press_time,
            "mode": self._mode.value,
        })
    
    def _handle_button_release(self, pin_name: str, release_time: float) -> None:
        """Handle button release."""
        # Trigger callback
        self._trigger_callback(InputEvent.BUTTON_RELEASE, {
            "pin": pin_name,
            "time": release_time,
            "mode": self._mode.value,
        })
    
    def _handle_navigation_press(self, pin_name: str) -> None:
        """Handle button press in navigation mode."""
        if pin_name == "up_pin":
            self._trigger_callback(InputEvent.NAVIGATE_UP, {})
        elif pin_name == "down_pin":
            self._trigger_callback(InputEvent.NAVIGATE_DOWN, {})
        elif pin_name == "left_pin":
            self._trigger_callback(InputEvent.NAVIGATE_LEFT, {})
        elif pin_name == "right_pin":
            self._trigger_callback(InputEvent.NAVIGATE_RIGHT, {})
        elif pin_name == "select_pin":
            self._trigger_callback(InputEvent.SELECT, {})
        elif pin_name == "back_pin":
            self._trigger_callback(InputEvent.BACK, {})
        elif pin_name == "mode_pin":
            self._cycle_mode()
        elif pin_name == "toggle_pin":
            self._trigger_callback(InputEvent.TOGGLE_PRESS, {})
    
    def _handle_text_input_press(self, pin_name: str) -> None:
        """Handle button press in text input mode."""
        row, col = self._current_char_pos
        
        if pin_name == "up_pin":
            # Move up in character grid
            row = max(0, row - 1)
        elif pin_name == "down_pin":
            # Move down in character grid
            row = min(len(self.CHAR_GRID) - 1, row + 1)
        elif pin_name == "left_pin":
            # Move left in character grid
            col = max(0, col - 1)
        elif pin_name == "right_pin":
            # Move right in character grid
            col = min(len(self.CHAR_GRID[0]) - 1, col + 1)
        elif pin_name == "select_pin":
            # Select current character
            if 0 <= row < len(self.CHAR_GRID) and 0 <= col < len(self.CHAR_GRID[row]):
                char = self.CHAR_GRID[row][col]
                if char == ' ':  # Space character
                    self._input_text += ' '
                elif char == '.':  # Backspace
                    self._input_text = self._input_text[:-1]
                else:
                    self._input_text += char
        elif pin_name == "back_pin":
            # Delete last character
            self._input_text = self._input_text[:-1]
        elif pin_name == "mode_pin":
            # Switch back to navigation mode
            self._mode = InputMode.NAVIGATION
            self._trigger_callback(InputEvent.MODE_CHANGE, {
                "new_mode": self._mode.value,
            })
        
        self._current_char_pos = (row, col)
        
        # Trigger callback with current text
        self._trigger_callback(InputEvent.BUTTON_PRESS, {
            "pin": pin_name,
            "text": self._input_text,
            "cursor_pos": self._current_char_pos,
        })
    
    def _handle_command_select_press(self, pin_name: str) -> None:
        """Handle button press in command select mode."""
        # This would be used for selecting from a menu of commands
        if pin_name == "up_pin":
            self._trigger_callback(InputEvent.NAVIGATE_UP, {})
        elif pin_name == "down_pin":
            self._trigger_callback(InputEvent.NAVIGATE_DOWN, {})
        elif pin_name == "select_pin":
            self._trigger_callback(InputEvent.SELECT, {})
        elif pin_name == "back_pin":
            self._trigger_callback(InputEvent.BACK, {})
        elif pin_name == "mode_pin":
            self._cycle_mode()
    
    def _cycle_mode(self) -> None:
        """Cycle through input modes."""
        modes = list(InputMode)
        current_index = modes.index(self._mode)
        next_index = (current_index + 1) % len(modes)
        self._mode = modes[next_index]
        
        self._trigger_callback(InputEvent.MODE_CHANGE, {
            "new_mode": self._mode.value,
        })
    
    def _simulate_mock_input(self, current_time: float) -> None:
        """Simulate input for testing without hardware."""
        # Simple simulation - cycle through some basic inputs
        import random
        
        if random.random() < 0.01:  # 1% chance per cycle
            simulated_pin = random.choice(list(self.gpio_config.keys()))
            self._handle_button_press(simulated_pin, current_time)
    
    def _trigger_callback(self, event_type: InputEvent, data: Dict[str, Any]) -> None:
        """Trigger registered callback for event type."""
        callback = self._event_callbacks.get(event_type.value)
        if callback:
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"Error in input callback: {e}")
    
    def set_mode(self, mode: InputMode) -> None:
        """
        Set the current input mode.
        
        Args:
            mode: New input mode
        """
        old_mode = self._mode
        self._mode = mode
        
        if old_mode != mode:
            self._trigger_callback(InputEvent.MODE_CHANGE, {
                "old_mode": old_mode.value,
                "new_mode": mode.value,
            })
    
    def get_mode(self) -> InputMode:
        """Get the current input mode."""
        return self._mode
    
    def get_input_text(self) -> str:
        """Get the current input text buffer."""
        return self._input_text
    
    def clear_input_text(self) -> None:
        """Clear the input text buffer."""
        self._input_text = ""
    
    def get_current_char_position(self) -> tuple:
        """Get the current character grid position."""
        return self._current_char_pos
    
    def get_gpio_config(self) -> Dict[str, int]:
        """Get the current GPIO configuration."""
        return self.gpio_config.copy()
    
    def is_running(self) -> bool:
        """Check if input handler is running."""
        return self._running