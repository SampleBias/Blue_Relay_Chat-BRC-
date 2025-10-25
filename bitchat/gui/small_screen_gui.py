"""
Small screen GUI for 1.44-inch LCD display.

This module provides a simple chat interface optimized for
small screens with toggle/button input.
"""

import asyncio
import time
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..config.manager import ConfigManager
from ..utils.logging import get_logger
from ..core.events import EventBus, Event, EventTypes
from .display_driver import DisplayDriver, DisplayColor
from .input_handler import InputHandler, InputMode, InputEvent


class SmallScreenGUI:
    """Simple GUI for 1.44-inch LCD screen."""
    
    # Screen layout dimensions
    STATUS_HEIGHT = 12
    INPUT_HEIGHT = 12
    CONTENT_HEIGHT = 104  # 128 - STATUS_HEIGHT - INPUT_HEIGHT
    
    # Navigation and UI state
    UI_MODE_CHAT = "chat"
    UI_MODE_MENU = "menu"
    UI_MODE_STATUS = "status"
    
    def __init__(self, config_manager: ConfigManager, event_bus: EventBus) -> None:
        """
        Initialize small screen GUI.
        
        Args:
            config_manager: Configuration manager instance
            event_bus: Event bus for component communication
        """
        self.config = config_manager
        self.event_bus = event_bus
        self.logger = get_logger("small_screen_gui")
        
        # Display and input components
        self.display: Optional[DisplayDriver] = None
        self.input_handler: Optional[InputHandler] = None
        
        # UI state
        self._running = False
        self._current_mode = self.UI_MODE_CHAT
        self._current_channel = config_manager.get("channels.default_channel", "mesh #bluetooth")
        self._message_history: List[Dict[str, Any]] = []
        self._menu_index = 0
        self._status_page = 0
        
        # Status information
        self._status_info = {
            "connected_peers": 0,
            "transport_status": {"mesh": "offline", "nostr": "offline"},
            "current_channel": self._current_channel,
            "identity_id": None,
            "battery_level": 100,
            "signal_strength": 0,
        }
        
        # Menu options
        self._menu_options = [
            "Send Message",
            "View Status",
            "Change Channel",
            "Settings",
            "Exit",
        ]
        
        # Status pages
        self._status_pages = [
            "Peers & Transport",
            "Network Info",
            "System Info",
            "Battery & Signal",
        ]
        
        # Input text buffer
        self._input_text = ""
        self._input_cursor_pos = 0
        
        self.logger.info("Small screen GUI initialized")
    
    async def initialize(self) -> None:
        """Initialize the GUI components."""
        try:
            # Initialize display driver
            self.display = DisplayDriver()
            if not self.display.connect():
                raise Exception("Failed to connect to display")
            
            # Initialize input handler
            self.input_handler = InputHandler()
            self.input_handler.register_callback(InputEvent.BUTTON_PRESS, self._on_button_press)
            self.input_handler.register_callback(InputEvent.MODE_CHANGE, self._on_mode_change)
            self.input_handler.register_callback(InputEvent.NAVIGATE_UP, self._on_navigate_up)
            self.input_handler.register_callback(InputEvent.NAVIGATE_DOWN, self._on_navigate_down)
            self.input_handler.register_callback(InputEvent.NAVIGATE_LEFT, self._on_navigate_left)
            self.input_handler.register_callback(InputEvent.NAVIGATE_RIGHT, self._on_navigate_right)
            self.input_handler.register_callback(InputEvent.SELECT, self._on_select)
            self.input_handler.register_callback(InputEvent.BACK, self._on_back)
            
            # Start input handler
            self.input_handler.start()
            
            # Subscribe to events
            self._setup_event_subscriptions()
            
            # Clear display and show welcome
            self.display.clear()
            self._show_welcome_screen()
            self.display.refresh()
            
            self.logger.info("Small screen GUI initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize GUI: {e}")
            raise
    
    def _setup_event_subscriptions(self) -> None:
        """Set up event subscriptions for the GUI."""
        self.event_bus.subscribe(EventTypes.MESSAGE_RECEIVED, self._on_message_received)
        self.event_bus.subscribe(EventTypes.MESSAGE_SENT, self._on_message_sent)
        self.event_bus.subscribe(EventTypes.CHANNEL_JOINED, self._on_channel_joined)
        self.event_bus.subscribe(EventTypes.PEER_CONNECTED, self._on_peer_connected)
        self.event_bus.subscribe(EventTypes.PEER_DISCONNECTED, self._on_peer_disconnected)
        self.event_bus.subscribe(EventTypes.TRANSPORT_CONNECTED, self._on_transport_connected)
        self.event_bus.subscribe(EventTypes.TRANSPORT_DISCONNECTED, self._on_transport_disconnected)
    
    async def start(self) -> None:
        """Start the GUI main loop."""
        if self._running:
            self.logger.warning("GUI is already running")
            return
        
        self._running = True
        self.logger.info("Starting small screen GUI")
        
        try:
            # Start the main loop
            await self._main_loop()
            
        except Exception as e:
            self.logger.error(f"GUI error: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the GUI."""
        self._running = False
        self.logger.info("Stopping small screen GUI")
        
        # Stop input handler
        if self.input_handler:
            self.input_handler.stop()
        
        # Disconnect display
        if self.display:
            self.display.disconnect()
    
    async def _main_loop(self) -> None:
        """Main GUI loop."""
        self.logger.debug("Starting GUI main loop")
        
        while self._running:
            try:
                # Update display based on current mode
                if self._current_mode == self.UI_MODE_CHAT:
                    await self._draw_chat_screen()
                elif self._current_mode == self.UI_MODE_MENU:
                    await self._draw_menu_screen()
                elif self._current_mode == self.UI_MODE_STATUS:
                    await self._draw_status_screen()
                
                # Refresh display
                self.display.refresh()
                
                # Small delay to prevent excessive CPU usage
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in GUI main loop: {e}")
                await asyncio.sleep(0.5)
        
        self.logger.debug("GUI main loop ended")
    
    async def _draw_chat_screen(self) -> None:
        """Draw the chat interface."""
        # Clear screen
        self.display.clear()
        
        # Draw status bar
        self._draw_status_bar()
        
        # Draw content area (messages)
        await self._draw_chat_content()
        
        # Draw input area
        self._draw_input_area()
    
    async def _draw_menu_screen(self) -> None:
        """Draw the menu interface."""
        # Clear screen
        self.display.clear()
        
        # Draw title
        self.display.draw_text(2, 2, "Blue Relay Chat", DisplayColor.WHITE)
        
        # Draw menu options
        y_start = 20
        for i, option in enumerate(self._menu_options):
            y_pos = y_start + (i * 12)
            prefix = "> " if i == self._menu_index else " "
            self.display.draw_text(10, y_pos, f"{prefix}{option}", DisplayColor.WHITE)
        
        # Draw navigation hint
        self.display.draw_text(2, 110, "UP/DOWN: Navigate", DisplayColor.WHITE)
        self.display.draw_text(2, 118, "SELECT: Choose", DisplayColor.WHITE)
    
    async def _draw_status_screen(self) -> None:
        """Draw the status interface."""
        # Clear screen
        self.display.clear()
        
        # Draw title
        self.display.draw_text(2, 2, "System Status", DisplayColor.WHITE)
        
        # Draw status content based on current page
        if self._status_page == 0:  # Peers & Transport
            self._draw_peer_transport_status()
        elif self._status_page == 1:  # Network Info
            self._draw_network_status()
        elif self._status_page == 2:  # System Info
            self._draw_system_status()
        elif self._status_page == 3:  # Battery & Signal
            self._draw_battery_signal_status()
        
        # Draw navigation hint
        self.display.draw_text(2, 110, "LEFT/RIGHT: Page", DisplayColor.WHITE)
        self.display.draw_text(2, 118, "SELECT: Refresh", DisplayColor.WHITE)
        self.display.draw_text(2, 126, "BACK: Menu", DisplayColor.WHITE)
    
    def _draw_status_bar(self) -> None:
        """Draw the status bar at the top."""
        # Clear status area
        self.display.draw_rectangle(0, 0, 128, self.STATUS_HEIGHT, DisplayColor.BLACK, True)
        
        # Draw border
        self.display.draw_rectangle(0, 0, 128, self.STATUS_HEIGHT, DisplayColor.WHITE, False)
        
        # Draw status text (abbreviated for small screen)
        status_text = f"Ch:{self._current_channel[-8:]} P:{self._status_info['connected_peers']} "
        status_text += f"M:{self._status_info['transport_status']['mesh'][0]} "
        status_text += f"N:{self._status_info['transport_status']['nostr'][0]}"
        
        self.display.draw_text(2, 3, status_text, DisplayColor.WHITE)
    
    async def _draw_chat_content(self) -> None:
        """Draw the chat messages."""
        # Show last few messages that fit in content area
        max_messages = self.CONTENT_HEIGHT // 9  # Approximate lines per message
        start_idx = max(0, len(self._message_history) - max_messages)
        
        y_pos = self.STATUS_HEIGHT + 2
        for i, message in enumerate(self._message_history[start_idx:]):
            if y_pos + 8 > self.STATUS_HEIGHT + self.CONTENT_HEIGHT:
                break
            
            # Draw message with timestamp (abbreviated)
            timestamp = message.get("timestamp", datetime.now())
            if isinstance(timestamp, datetime):
                time_str = timestamp.strftime("%H:%M")
            else:
                time_str = "??"
            
            sender = message.get("sender", "sys")
            content = message.get("content", "")
            msg_type = message.get("type", "text")
            
            # Truncate content for small screen
            max_content_len = 15
            if len(content) > max_content_len:
                content = content[:max_content_len-2] + ".."
            
            # Format message line
            if msg_type == "sent":
                line = f"{time_str} >:{content[:max_content_len]}"
            elif msg_type == "received":
                line = f"{time_str} {sender[:3]}:{content[:max_content_len]}"
            else:  # system
                line = f"{time_str} {content[:max_content_len]}"
            
            self.display.draw_text(2, y_pos, line, DisplayColor.WHITE)
            y_pos += 9
    
    def _draw_input_area(self) -> None:
        """Draw the input area at the bottom."""
        y_start = 128 - self.INPUT_HEIGHT
        
        # Clear input area
        self.display.draw_rectangle(0, y_start, 128, self.INPUT_HEIGHT, DisplayColor.BLACK, True)
        
        # Draw border
        self.display.draw_rectangle(0, y_start, 128, self.INPUT_HEIGHT, DisplayColor.WHITE, False)
        
        # Draw input text
        if self.input_handler and self.input_handler.get_mode() == InputMode.TEXT_INPUT:
            # Show text input mode indicator
            self.display.draw_text(2, y_start + 2, "TEXT:", DisplayColor.WHITE)
            
            # Show input text
            input_text = self.input_handler.get_input_text()
            if len(input_text) > 15:
                input_text = input_text[:12] + ".."
            
            self.display.draw_text(2, y_start + 10, input_text, DisplayColor.WHITE)
            
            # Show cursor
            cursor_pos = self.input_handler.get_current_char_position()
            if cursor_pos:
                cursor_text = "_" if len(input_text) < 15 else ""
                self.display.draw_text(2 + len(input_text), y_start + 10, cursor_text, DisplayColor.WHITE)
        else:
            # Show navigation mode
            self.display.draw_text(2, y_start + 2, "NAV MODE", DisplayColor.WHITE)
            self.display.draw_text(2, y_start + 10, "SELECT: Text Input", DisplayColor.WHITE)
    
    def _draw_peer_transport_status(self) -> None:
        """Draw peer and transport status."""
        y_start = 20
        
        # Title
        self.display.draw_text(2, y_start, "Peers & Transport", DisplayColor.WHITE)
        
        # Peer count
        self.display.draw_text(2, y_start + 12, f"Peers: {self._status_info['connected_peers']}", DisplayColor.WHITE)
        
        # Transport status
        y_pos = y_start + 24
        for transport, status in self._status_info['transport_status'].items():
            status_text = f"{transport.upper()}: {status}"
            self.display.draw_text(2, y_pos, status_text, DisplayColor.WHITE)
            y_pos += 8
    
    def _draw_network_status(self) -> None:
        """Draw network information."""
        y_start = 20
        
        # Title
        self.display.draw_text(2, y_start, "Network Info", DisplayColor.WHITE)
        
        # Current channel
        self.display.draw_text(2, y_start + 12, f"Channel: {self._current_channel}", DisplayColor.WHITE)
        
        # Transport status summary
        mesh_status = self._status_info['transport_status']['mesh']
        nostr_status = self._status_info['transport_status']['nostr']
        
        self.display.draw_text(2, y_start + 24, f"Mesh: {mesh_status}", DisplayColor.WHITE)
        self.display.draw_text(2, y_start + 32, f"Nostr: {nostr_status}", DisplayColor.WHITE)
    
    def _draw_system_status(self) -> None:
        """Draw system information."""
        y_start = 20
        
        # Title
        self.display.draw_text(2, y_start, "System Info", DisplayColor.WHITE)
        
        # Hardware info
        hw_info = self.config.get_hardware_info()
        if hw_info.get("profile_name"):
            self.display.draw_text(2, y_start + 12, f"HW: {hw_info['profile_name']}", DisplayColor.WHITE)
        
        # Memory usage
        if hw_info.get("total_memory_mb"):
            self.display.draw_text(2, y_start + 24, f"RAM: {hw_info['total_memory_mb']}MB", DisplayColor.WHITE)
        
        # CPU cores
        if hw_info.get("cpu_cores"):
            self.display.draw_text(2, y_start + 32, f"Cores: {hw_info['cpu_cores']}", DisplayColor.WHITE)
    
    def _draw_battery_signal_status(self) -> None:
        """Draw battery and signal status."""
        y_start = 20
        
        # Title
        self.display.draw_text(2, y_start, "Battery & Signal", DisplayColor.WHITE)
        
        # Battery level (simulated)
        battery_level = self._status_info.get("battery_level", 100)
        battery_text = f"Battery: {battery_level}%"
        self.display.draw_text(2, y_start + 12, battery_text, DisplayColor.WHITE)
        
        # Signal strength (simulated)
        signal_strength = self._status_info.get("signal_strength", 0)
        signal_bars = min(5, signal_strength // 20)
        signal_text = "Signal: " + ("█" * signal_bars + "░" * (5 - signal_bars))
        self.display.draw_text(2, y_start + 24, signal_text, DisplayColor.WHITE)
    
    def _show_welcome_screen(self) -> None:
        """Show welcome screen on startup."""
        self.display.clear()
        
        # Draw welcome message
        self.display.draw_text(2, 30, "Blue Relay Chat", DisplayColor.WHITE)
        self.display.draw_text(2, 45, "for Small Screens", DisplayColor.WHITE)
        self.display.draw_text(2, 70, "Starting...", DisplayColor.WHITE)
    
    # Event handlers
    def _on_button_press(self, data: Dict[str, Any]) -> None:
        """Handle button press events."""
        pin = data.get("pin", "")
        mode = data.get("mode", "")
        
        self.logger.debug(f"Button pressed: {pin} in mode {mode}")
        
        # Mode-specific handling is done by input handler
        # We just need to update the display based on mode changes
    
    def _on_mode_change(self, data: Dict[str, Any]) -> None:
        """Handle input mode change events."""
        new_mode = data.get("new_mode", "")
        self.logger.debug(f"Input mode changed to: {new_mode}")
        
        # Update display based on new mode
        if new_mode == InputMode.TEXT_INPUT.value:
            # Switch to text input mode in chat interface
            pass  # Display will update in next loop
        elif new_mode == InputMode.NAVIGATION.value:
            # Switch to navigation mode
            pass  # Display will update in next loop
    
    def _on_navigate_up(self, data: Dict[str, Any]) -> None:
        """Handle up navigation."""
        if self._current_mode == self.UI_MODE_MENU:
            self._menu_index = (self._menu_index - 1) % len(self._menu_options)
        elif self._current_mode == self.UI_MODE_STATUS:
            self._status_page = (self._status_page - 1) % len(self._status_pages)
    
    def _on_navigate_down(self, data: Dict[str, Any]) -> None:
        """Handle down navigation."""
        if self._current_mode == self.UI_MODE_MENU:
            self._menu_index = (self._menu_index + 1) % len(self._menu_options)
        elif self._current_mode == self.UI_MODE_STATUS:
            self._status_page = (self._status_page + 1) % len(self._status_pages)
    
    def _on_navigate_left(self, data: Dict[str, Any]) -> None:
        """Handle left navigation."""
        if self._current_mode == self.UI_MODE_CHAT and self.input_handler:
            if self.input_handler.get_mode() == InputMode.TEXT_INPUT:
                # Left navigation in text input mode
                pass  # Handled by input handler
    
    def _on_navigate_right(self, data: Dict[str, Any]) -> None:
        """Handle right navigation."""
        if self._current_mode == self.UI_MODE_CHAT and self.input_handler:
            if self.input_handler.get_mode() == InputMode.TEXT_INPUT:
                # Right navigation in text input mode
                pass  # Handled by input handler
    
    def _on_select(self, data: Dict[str, Any]) -> None:
        """Handle select/confirm button."""
        if self._current_mode == self.UI_MODE_MENU:
            selected_option = self._menu_options[self._menu_index]
            self._handle_menu_selection(selected_option)
        elif self._current_mode == self.UI_MODE_CHAT:
            if self.input_handler and self.input_handler.get_mode() == InputMode.TEXT_INPUT:
                # Send message
                self._send_message()
        elif self._current_mode == self.UI_MODE_STATUS:
            # Refresh status page
            pass  # Status is already current
    
    def _on_back(self, data: Dict[str, Any]) -> None:
        """Handle back/cancel button."""
        if self._current_mode == self.UI_MODE_CHAT:
            # Switch to menu
            self._current_mode = self.UI_MODE_MENU
        elif self._current_mode == self.UI_MODE_STATUS:
            # Switch to menu
            self._current_mode = self.UI_MODE_MENU
    
    def _handle_menu_selection(self, option: str) -> None:
        """Handle menu option selection."""
        if option == "Send Message":
            self._current_mode = self.UI_MODE_CHAT
            if self.input_handler:
                self.input_handler.set_mode(InputMode.TEXT_INPUT)
        elif option == "View Status":
            self._current_mode = self.UI_MODE_STATUS
            self._status_page = 0
        elif option == "Change Channel":
            # Could implement channel selection
            self._current_mode = self.UI_MODE_CHAT
        elif option == "Settings":
            # Could implement settings menu
            self._current_mode = self.UI_MODE_CHAT
        elif option == "Exit":
            # Trigger shutdown
            asyncio.create_task(self._shutdown())
    
    def _send_message(self) -> None:
        """Send the current input text as a message."""
        if self.input_handler:
            text = self.input_handler.get_input_text()
            if text.strip():
                # Add to message history
                self._message_history.append({
                    "type": "sent",
                    "content": text.strip(),
                    "timestamp": datetime.now(),
                })
                
                # Limit history size
                if len(self._message_history) > 50:
                    self._message_history.pop(0)
                
                # Clear input
                self.input_handler.clear_input_text()
                
                # Publish message sent event
                asyncio.create_task(self.event_bus.publish(Event(
                    type=EventTypes.MESSAGE_SENT,
                    data={"message": {"content": text.strip()}},
                    source="gui"
                )))
    
    async def _shutdown(self) -> None:
        """Shutdown the application."""
        self.logger.info("Shutting down from GUI")
        
        # Publish shutdown event
        await self.event_bus.publish(Event(
            type=EventTypes.SYSTEM_SHUTDOWN,
            data={"source": "gui"},
            source="gui"
        ))
    
    # Event handlers for system events
    async def _on_message_received(self, event: Event) -> None:
        """Handle message received event."""
        message_data = event.data.get("message", {})
        self._message_history.append({
            "type": "received",
            "sender": message_data.get("sender_id", "unknown"),
            "content": message_data.get("content", ""),
            "timestamp": datetime.now(),
        })
        
        # Limit history size
        if len(self._message_history) > 50:
            self._message_history.pop(0)
    
    async def _on_message_sent(self, event: Event) -> None:
        """Handle message sent event."""
        # Message is already in history from _send_message
        pass
    
    async def _on_channel_joined(self, event: Event) -> None:
        """Handle channel joined event."""
        channel_id = event.data.get("channel_id", "unknown")
        self._current_channel = channel_id
        self._status_info["current_channel"] = channel_id
    
    async def _on_peer_connected(self, event: Event) -> None:
        """Handle peer connected event."""
        self._status_info["connected_peers"] += 1
    
    async def _on_peer_disconnected(self, event: Event) -> None:
        """Handle peer disconnected event."""
        self._status_info["connected_peers"] = max(0, self._status_info["connected_peers"] - 1)
    
    async def _on_transport_connected(self, event: Event) -> None:
        """Handle transport connected event."""
        transport_type = event.data.get("transport_type", "unknown")
        self._status_info["transport_status"][transport_type] = "online"
    
    async def _on_transport_disconnected(self, event: Event) -> None:
        """Handle transport disconnected event."""
        transport_type = event.data.get("transport_type", "unknown")
        self._status_info["transport_status"][transport_type] = "offline"