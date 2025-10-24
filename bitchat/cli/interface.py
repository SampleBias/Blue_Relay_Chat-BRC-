"""
Main CLI interface for Blue Relay Chat RPi 4 client.

This module provides the main command-line interface using curses
for interactive messaging and system control.
"""

import asyncio
import curses
import curses.ascii
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..config.manager import ConfigManager
from ..utils.logging import get_logger
from ..exceptions import CLIError
from ..core.events import EventBus, Event, EventTypes
from .commands import CommandProcessor
from .display import DisplayManager
from .widgets import WidgetManager


class CLIInterface:
    """Main CLI interface for the application."""
    
    def __init__(self, config_manager: ConfigManager, event_bus: EventBus) -> None:
        """
        Initialize the CLI interface.
        
        Args:
            config_manager: Configuration manager instance
            event_bus: Event bus for component communication
        """
        self.config = config_manager
        self.event_bus = event_bus
        self.logger = get_logger("cli")
        
        # Interface configuration
        self.refresh_rate = config_manager.get("cli.refresh_rate_ms", 100)
        self.max_display_lines = config_manager.get("cli.max_display_lines", 1000)
        self.timestamp_format = config_manager.get("cli.timestamp_format", "%H:%M:%S")
        self.show_system_messages = config_manager.get("cli.show_system_messages", True)
        self.auto_scroll = config_manager.get("cli.auto_scroll", True)
        
        # Interface state
        self._running = False
        self._screen: Optional[curses.window] = None
        self._input_buffer = ""
        self._cursor_position = 0
        self._current_channel = config_manager.get("channels.default_channel", "mesh #bluetooth")
        
        # Component managers
        self.command_processor = CommandProcessor(config_manager, event_bus)
        self.display_manager: Optional[DisplayManager] = None
        self.widget_manager: Optional[WidgetManager] = None
        
        # Message history
        self._message_history: List[Dict[str, Any]] = []
        self._command_history: List[str] = []
        self._history_position = -1
        
        # Status information
        self._status_info = {
            "connected_peers": 0,
            "transport_status": {"mesh": "offline", "nostr": "offline"},
            "current_channel": self._current_channel,
            "identity_id": None,
        }
    
    async def initialize(self) -> None:
        """Initialize the CLI interface."""
        try:
            # Initialize curses
            self._screen = curses.initscr()
            curses.noecho()
            curses.cbreak()
            curses.curs_set(1)
            self._screen.keypad(True)
            
            # Set up colors
            curses.start_color()
            curses.use_default_colors()
            self._setup_colors()
            
            # Initialize component managers
            self.display_manager = DisplayManager(self._screen, self.config)
            self.widget_manager = WidgetManager(self._screen, self.config)
            
            # Subscribe to events
            self._setup_event_subscriptions()
            
            self.logger.info("CLI interface initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize CLI interface: {e}")
            await self.cleanup()
            raise CLIError(f"CLI initialization failed: {e}")
    
    def _setup_colors(self) -> None:
        """Set up color pairs for the interface."""
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)   # Default
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)    # System messages
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Success messages
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Warning messages
        curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)     # Error messages
        curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_BLACK)    # User messages
        curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Channel info
        curses.init_pair(8, curses.COLOR_WHITE, curses.COLOR_BLUE)    # Status bar
    
    def _setup_event_subscriptions(self) -> None:
        """Set up event subscriptions for the CLI."""
        self.event_bus.subscribe(EventTypes.MESSAGE_RECEIVED, self._on_message_received)
        self.event_bus.subscribe(EventTypes.MESSAGE_SENT, self._on_message_sent)
        self.event_bus.subscribe(EventTypes.CHANNEL_JOINED, self._on_channel_joined)
        self.event_bus.subscribe(EventTypes.PEER_CONNECTED, self._on_peer_connected)
        self.event_bus.subscribe(EventTypes.PEER_DISCONNECTED, self._on_peer_disconnected)
        self.event_bus.subscribe(EventTypes.TRANSPORT_CONNECTED, self._on_transport_connected)
        self.event_bus.subscribe(EventTypes.TRANSPORT_DISCONNECTED, self._on_transport_disconnected)
        self.event_bus.subscribe(EventTypes.SYSTEM_ERROR, self._on_system_error)
    
    async def start(self) -> None:
        """Start the CLI interface."""
        if self._running:
            self.logger.warning("CLI interface is already running")
            return
        
        self._running = True
        
        try:
            # Start the main loop
            await self._main_loop()
            
        except Exception as e:
            self.logger.error(f"CLI interface error: {e}")
            raise CLIError(f"CLI interface error: {e}")
        finally:
            await self.cleanup()
    
    async def stop(self) -> None:
        """Stop the CLI interface."""
        self._running = False
        self.logger.info("CLI interface stopped")
    
    async def cleanup(self) -> None:
        """Clean up resources and restore terminal."""
        try:
            if self._screen:
                curses.nocbreak()
                self._screen.keypad(False)
                curses.echo()
                curses.endwin()
                self._screen = None
            
            self.logger.debug("CLI interface cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during CLI cleanup: {e}")
    
    async def _main_loop(self) -> None:
        """Main CLI loop."""
        self.logger.debug("Starting CLI main loop")
        
        while self._running:
            try:
                # Get screen dimensions
                height, width = self._screen.getmaxyx()
                
                # Clear screen
                self._screen.clear()
                
                # Draw interface
                await self._draw_interface(height, width)
                
                # Handle input
                await self._handle_input()
                
                # Refresh screen
                self._screen.refresh()
                
                # Control refresh rate
                await asyncio.sleep(self.refresh_rate / 1000.0)
                
            except curses.resizeterm:
                # Handle terminal resize
                continue
            except Exception as e:
                self.logger.error(f"Error in CLI main loop: {e}")
                await asyncio.sleep(0.1)
        
        self.logger.debug("CLI main loop ended")
    
    async def _draw_interface(self, height: int, width: int) -> None:
        """Draw the complete interface."""
        if not self.display_manager or not self.widget_manager:
            return
        
        # Calculate layout
        status_height = 1
        input_height = 1
        content_height = height - status_height - input_height
        
        # Draw status bar
        await self._draw_status_bar(0, width)
        
        # Draw content area
        await self._draw_content_area(1, content_height, width)
        
        # Draw input line
        await self._draw_input_line(height - 1, width)
    
    async def _draw_status_bar(self, y: int, width: int) -> None:
        """Draw the status bar."""
        status_text = f"Blue Relay Chat | Channel: {self._current_channel} | "
        status_text += f"Peers: {self._status_info['connected_peers']} | "
        status_text += f"Mesh: {self._status_info['transport_status']['mesh']} | "
        status_text += f"Nostr: {self._status_info['transport_status']['nostr']}"
        
        # Truncate if too long
        if len(status_text) > width:
            status_text = status_text[:width-3] + "..."
        
        # Draw status bar
        self._screen.attron(curses.color_pair(8) | curses.A_REVERSE)
        self._screen.addstr(y, 0, status_text.ljust(width))
        self._screen.attroff(curses.color_pair(8) | curses.A_REVERSE)
    
    async def _draw_content_area(self, y: int, height: int, width: int) -> None:
        """Draw the main content area with messages."""
        if not self.display_manager:
            return
        
        # Get visible messages
        visible_messages = self._get_visible_messages(height)
        
        # Draw messages
        for i, message in enumerate(visible_messages):
            if y + i < y + height:
                await self.display_manager.draw_message(y + i, width, message, self.timestamp_format)
    
    async def _draw_input_line(self, y: int, width: int) -> None:
        """Draw the input line."""
        # Draw prompt
        prompt = "> "
        self._screen.addstr(y, 0, prompt)
        
        # Draw input buffer
        input_text = self._input_buffer
        if len(input_text) > width - len(prompt) - 1:
            # Truncate input if too long
            start_pos = len(input_text) - (width - len(prompt) - 1)
            input_text = input_text[start_pos:]
            cursor_pos = len(input_text)
        else:
            cursor_pos = self._cursor_position
        
        # Draw input text
        self._screen.addstr(y, len(prompt), input_text)
        
        # Position cursor
        self._screen.move(y, len(prompt) + cursor_pos)
    
    def _get_visible_messages(self, height: int) -> List[Dict[str, Any]]:
        """Get messages visible in the current view."""
        if not self.auto_scroll:
            # Show last N messages
            start_idx = max(0, len(self._message_history) - height)
            return self._message_history[start_idx:]
        else:
            # Show recent messages that fit in view
            return self._message_history[-height:]
    
    async def _handle_input(self) -> None:
        """Handle keyboard input."""
        try:
            # Non-blocking input check
            self._screen.nodelay(True)
            key = self._screen.getch()
            self._screen.nodelay(False)
            
            if key == curses.ERR:
                return  # No input available
            
            # Handle special keys
            if key == curses.KEY_ENTER or key == 10:  # Enter key
                await self._process_command()
            elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace
                self._handle_backspace()
            elif key == curses.KEY_LEFT:
                self._handle_cursor_left()
            elif key == curses.KEY_RIGHT:
                self._handle_cursor_right()
            elif key == curses.KEY_UP:
                self._handle_history_up()
            elif key == curses.KEY_DOWN:
                self._handle_history_down()
            elif key == curses.KEY_HOME:
                self._cursor_position = 0
            elif key == curses.KEY_END:
                self._cursor_position = len(self._input_buffer)
            elif key == 3:  # Ctrl+C
                await self._handle_interrupt()
            elif key == 4:  # Ctrl+D
                await self._handle_eof()
            elif curses.ascii.isprint(key):
                self._handle_character(key)
            
        except curses.error:
            pass  # Ignore curses errors
    
    def _handle_character(self, key: int) -> None:
        """Handle printable character input."""
        char = chr(key)
        self._input_buffer = (
            self._input_buffer[:self._cursor_position] + 
            char + 
            self._input_buffer[self._cursor_position:]
        )
        self._cursor_position += 1
    
    def _handle_backspace(self) -> None:
        """Handle backspace key."""
        if self._cursor_position > 0:
            self._input_buffer = (
                self._input_buffer[:self._cursor_position-1] + 
                self._input_buffer[self._cursor_position:]
            )
            self._cursor_position -= 1
    
    def _handle_cursor_left(self) -> None:
        """Handle left arrow key."""
        if self._cursor_position > 0:
            self._cursor_position -= 1
    
    def _handle_cursor_right(self) -> None:
        """Handle right arrow key."""
        if self._cursor_position < len(self._input_buffer):
            self._cursor_position += 1
    
    def _handle_history_up(self) -> None:
        """Handle up arrow key (command history)."""
        if self._command_history:
            if self._history_position == -1:
                # Save current input
                self._current_input = self._input_buffer
                self._history_position = len(self._command_history) - 1
            elif self._history_position > 0:
                self._history_position -= 1
            
            self._input_buffer = self._command_history[self._history_position]
            self._cursor_position = len(self._input_buffer)
    
    def _handle_history_down(self) -> None:
        """Handle down arrow key (command history)."""
        if self._history_position != -1:
            if self._history_position < len(self._command_history) - 1:
                self._history_position += 1
                self._input_buffer = self._command_history[self._history_position]
            else:
                # Return to current input
                self._history_position = -1
                self._input_buffer = getattr(self, '_current_input', '')
            
            self._cursor_position = len(self._input_buffer)
    
    async def _process_command(self) -> None:
        """Process the current command."""
        command = self._input_buffer.strip()
        
        if not command:
            return
        
        # Add to command history
        if not self._command_history or self._command_history[-1] != command:
            self._command_history.append(command)
            # Limit history size
            if len(self._command_history) > 100:
                self._command_history.pop(0)
        
        # Reset history position
        self._history_position = -1
        
        # Clear input
        self._input_buffer = ""
        self._cursor_position = 0
        
        # Process command
        try:
            result = await self.command_processor.process_command(command, self._current_channel)
            
            if result:
                # Display result
                await self._add_message({
                    "type": "system",
                    "content": result,
                    "timestamp": datetime.now(),
                })
        
        except Exception as e:
            await self._add_message({
                "type": "error",
                "content": f"Command error: {e}",
                "timestamp": datetime.now(),
            })
    
    async def _handle_interrupt(self) -> None:
        """Handle Ctrl+C interrupt."""
        # Clear current input
        self._input_buffer = ""
        self._cursor_position = 0
        
        # Add interrupt message
        await self._add_message({
            "type": "system",
            "content": "Use /quit to exit",
            "timestamp": datetime.now(),
        })
    
    async def _handle_eof(self) -> None:
        """Handle Ctrl+D (EOF)."""
        # Signal shutdown
        await self.event_bus.publish(Event(
            type=EventTypes.SYSTEM_SHUTDOWN,
            data={"source": "cli"},
            source="cli"
        ))
    
    async def _add_message(self, message: Dict[str, Any]) -> None:
        """Add a message to the display."""
        self._message_history.append(message)
        
        # Limit message history
        if len(self._message_history) > self.max_display_lines:
            self._message_history.pop(0)
    
    # Event handlers
    async def _on_message_received(self, event: Event) -> None:
        """Handle message received event."""
        message_data = event.data.get("message", {})
        await self._add_message({
            "type": "received",
            "sender": message_data.get("sender_id", "unknown"),
            "content": message_data.get("content", ""),
            "timestamp": datetime.now(),
        })
    
    async def _on_message_sent(self, event: Event) -> None:
        """Handle message sent event."""
        message_data = event.data.get("message", {})
        await self._add_message({
            "type": "sent",
            "content": message_data.get("content", ""),
            "timestamp": datetime.now(),
        })
    
    async def _on_channel_joined(self, event: Event) -> None:
        """Handle channel joined event."""
        channel_id = event.data.get("channel_id", "unknown")
        self._current_channel = channel_id
        self._status_info["current_channel"] = channel_id
        
        await self._add_message({
            "type": "system",
            "content": f"Joined channel: {channel_id}",
            "timestamp": datetime.now(),
        })
    
    async def _on_peer_connected(self, event: Event) -> None:
        """Handle peer connected event."""
        self._status_info["connected_peers"] += 1
        
        if self.show_system_messages:
            peer_id = event.data.get("peer_id", "unknown")
            await self._add_message({
                "type": "system",
                "content": f"Peer connected: {peer_id}",
                "timestamp": datetime.now(),
            })
    
    async def _on_peer_disconnected(self, event: Event) -> None:
        """Handle peer disconnected event."""
        self._status_info["connected_peers"] = max(0, self._status_info["connected_peers"] - 1)
        
        if self.show_system_messages:
            peer_id = event.data.get("peer_id", "unknown")
            await self._add_message({
                "type": "system",
                "content": f"Peer disconnected: {peer_id}",
                "timestamp": datetime.now(),
            })
    
    async def _on_transport_connected(self, event: Event) -> None:
        """Handle transport connected event."""
        transport_type = event.data.get("transport_type", "unknown")
        self._status_info["transport_status"][transport_type] = "online"
        
        if self.show_system_messages:
            await self._add_message({
                "type": "system",
                "content": f"Transport connected: {transport_type}",
                "timestamp": datetime.now(),
            })
    
    async def _on_transport_disconnected(self, event: Event) -> None:
        """Handle transport disconnected event."""
        transport_type = event.data.get("transport_type", "unknown")
        self._status_info["transport_status"][transport_type] = "offline"
        
        if self.show_system_messages:
            await self._add_message({
                "type": "system",
                "content": f"Transport disconnected: {transport_type}",
                "timestamp": datetime.now(),
            })
    
    async def _on_system_error(self, event: Event) -> None:
        """Handle system error event."""
        error_message = event.data.get("error", "Unknown error")
        await self._add_message({
            "type": "error",
            "content": f"System error: {error_message}",
            "timestamp": datetime.now(),
        })
    
    def get_interface_info(self) -> Dict[str, Any]:
        """Get information about the CLI interface."""
        return {
            "running": self._running,
            "current_channel": self._current_channel,
            "message_count": len(self._message_history),
            "command_history_size": len(self._command_history),
            "status_info": self._status_info.copy(),
            "config": {
                "refresh_rate": self.refresh_rate,
                "max_display_lines": self.max_display_lines,
                "timestamp_format": self.timestamp_format,
                "show_system_messages": self.show_system_messages,
                "auto_scroll": self.auto_scroll,
            }
        }