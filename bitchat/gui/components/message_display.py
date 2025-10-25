"""
Message display component for Blue Relay Chat laptop client.

This module provides a scrollable text area for displaying chat messages
with proper formatting and message type handling.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Dict, Any, Optional
from datetime import datetime

from ...config.manager import ConfigManager
from ...utils.logging import get_logger


class MessageDisplay:
    """Component for displaying chat messages."""
    
    def __init__(self, parent, config_manager: ConfigManager):
        """
        Initialize the message display component.
        
        Args:
            parent: Parent Tkinter widget
            config_manager: Configuration manager instance
        """
        self.parent = parent
        self.config = config_manager
        self.logger = get_logger("message_display")
        
        # Display widget
        self.display: Optional[scrolledtext.ScrolledText] = None
        
        # Configuration
        self.font_family = config_manager.get("laptop_gui.font_family", "TkDefaultFont")
        self.font_size = config_manager.get("laptop_gui.font_size", 10)
        self.show_timestamps = config_manager.get("laptop_gui.show_timestamps", True)
        self.max_history = config_manager.get("laptop_gui.max_message_history", 1000)
        
        # Message history
        self.message_history: list = []
        
        # Setup display
        self.setup_display()
    
    def setup_display(self) -> None:
        """Set up the message display widget."""
        try:
            # Create scrolled text widget
            self.display = scrolledtext.ScrolledText(
                self.parent,
                wrap=tk.WORD,
                state=tk.DISABLED,
                font=(self.font_family, self.font_size),
                height=15,
                width=50
            )
            
            # Configure text tags for different message types
            self.setup_tags()
            
            # Pack the widget
            self.display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            self.logger.debug("Message display component initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to setup message display: {e}")
            raise
    
    def setup_tags(self) -> None:
        """Configure text tags for different message types."""
        try:
            # Timestamp formatting
            self.display.tag_configure("timestamp", 
                                 foreground="gray", 
                                 font=(self.font_family, self.font_size - 1))
            
            # Message type formatting
            self.display.tag_configure("sent", 
                                 foreground="green", 
                                 font=(self.font_family, self.font_size))
            
            self.display.tag_configure("received", 
                                 foreground="black", 
                                 font=(self.font_family, self.font_size))
            
            self.display.tag_configure("system", 
                                 foreground="blue", 
                                 font=(self.font_family, self.font_size, "italic"))
            
            self.display.tag_configure("error", 
                                 foreground="red", 
                                 font=(self.font_family, self.font_size, "bold"))
            
            self.display.tag_configure("private", 
                                 foreground="purple", 
                                 font=(self.font_family, self.font_size))
            
            # User name formatting
            self.display.tag_configure("username", 
                                 foreground="darkblue", 
                                 font=(self.font_family, self.font_size, "bold"))
            
            self.logger.debug("Message display tags configured")
            
        except Exception as e:
            self.logger.error(f"Failed to setup display tags: {e}")
    
    def add_message(self, message: Dict[str, Any]) -> None:
        """
        Add a message to the display.
        
        Args:
            message: Message dictionary containing sender, content, type, etc.
        """
        try:
            # Enable text widget for editing
            self.display.config(state=tk.NORMAL)
            
            # Get message components
            sender = message.get("sender", "Unknown")
            content = message.get("content", "")
            msg_type = message.get("type", "received")
            timestamp = message.get("timestamp", datetime.now())
            
            # Format timestamp
            if self.show_timestamps:
                if isinstance(timestamp, datetime):
                    time_str = timestamp.strftime("%H:%M:%S")
                else:
                    time_str = str(timestamp)
                self.display.insert(tk.END, f"[{time_str}] ", "timestamp")
            
            # Format message based on type
            if msg_type == "sent":
                self._add_sent_message(sender, content)
            elif msg_type == "received":
                self._add_received_message(sender, content)
            elif msg_type == "system":
                self._add_system_message(content)
            elif msg_type == "error":
                self._add_error_message(content)
            elif msg_type == "private":
                self._add_private_message(sender, content)
            else:
                # Default to received message
                self._add_received_message(sender, content)
            
            # Add newline
            self.display.insert(tk.END, "\n")
            
            # Disable text widget
            self.display.config(state=tk.DISABLED)
            
            # Auto-scroll to bottom
            if self.config.get("laptop_gui.auto_scroll", True):
                self.display.see(tk.END)
            
            # Add to history
            self._add_to_history(message)
            
            self.logger.debug(f"Added {msg_type} message from {sender}")
            
        except Exception as e:
            self.logger.error(f"Failed to add message: {e}")
    
    def _add_sent_message(self, sender: str, content: str) -> None:
        """Add a sent message to the display."""
        self.display.insert(tk.END, "You: ", "username")
        self.display.insert(tk.END, content, "sent")
    
    def _add_received_message(self, sender: str, content: str) -> None:
        """Add a received message to the display."""
        self.display.insert(tk.END, f"{sender}: ", "username")
        self.display.insert(tk.END, content, "received")
    
    def _add_system_message(self, content: str) -> None:
        """Add a system message to the display."""
        self.display.insert(tk.END, "System: ", "system")
        self.display.insert(tk.END, content, "system")
    
    def _add_error_message(self, content: str) -> None:
        """Add an error message to the display."""
        self.display.insert(tk.END, "Error: ", "error")
        self.display.insert(tk.END, content, "error")
    
    def _add_private_message(self, sender: str, content: str) -> None:
        """Add a private message to the display."""
        self.display.insert(tk.END, f"[Private] {sender}: ", "private")
        self.display.insert(tk.END, content, "private")
    
    def _add_to_history(self, message: Dict[str, Any]) -> None:
        """Add message to history and maintain size limit."""
        self.message_history.append(message)
        
        # Maintain history size limit
        if len(self.message_history) > self.max_history:
            # Remove oldest messages
            excess = len(self.message_history) - self.max_history
            self.message_history = self.message_history[excess:]
    
    def clear(self) -> None:
        """Clear all messages from the display."""
        try:
            self.display.config(state=tk.NORMAL)
            self.display.delete(1.0, tk.END)
            self.display.config(state=tk.DISABLED)
            
            # Clear history
            self.message_history.clear()
            
            self.logger.debug("Message display cleared")
            
        except Exception as e:
            self.logger.error(f"Failed to clear message display: {e}")
    
    def get_content(self) -> str:
        """Get all content from the display."""
        if self.display:
            return self.display.get(1.0, tk.END)
        return ""
    
    def get_history(self) -> list:
        """Get the message history."""
        return self.message_history.copy()
    
    def set_font(self, font_family: str, font_size: int) -> None:
        """Update the font settings."""
        try:
            self.font_family = font_family
            self.font_size = font_size
            
            if self.display:
                self.display.config(font=(font_family, font_size))
            
            self.logger.debug(f"Updated font to {font_family} {font_size}")
            
        except Exception as e:
            self.logger.error(f"Failed to update font: {e}")
    
    def set_timestamps(self, show: bool) -> None:
        """Enable or disable timestamp display."""
        self.show_timestamps = show
        self.logger.debug(f"Timestamp display set to {show}")
    
    def scroll_to_bottom(self) -> None:
        """Scroll the display to the bottom."""
        if self.display:
            self.display.see(tk.END)
    
    def get_widget(self) -> Optional[scrolledtext.ScrolledText]:
        """Get the underlying Tkinter widget."""
        return self.display