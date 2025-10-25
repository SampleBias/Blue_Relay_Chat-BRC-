"""
Input panel component for Blue Relay Chat laptop client.

This module provides text input field with send functionality
and channel management for the chat interface.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable

from ...config.manager import ConfigManager
from ...utils.logging import get_logger


class InputPanel:
    """Component for message input and controls."""
    
    def __init__(self, parent, config_manager: ConfigManager, send_callback: Optional[Callable] = None):
        """
        Initialize the input panel component.
        
        Args:
            parent: Parent Tkinter widget
            config_manager: Configuration manager instance
            send_callback: Callback function for sending messages
        """
        self.parent = parent
        self.config = config_manager
        self.send_callback = send_callback
        self.logger = get_logger("input_panel")
        
        # Input widgets
        self.input_field: Optional[ttk.Entry] = None
        self.send_button: Optional[ttk.Button] = None
        self.join_button: Optional[ttk.Button] = None
        self.channel_var: Optional[tk.StringVar] = None
        
        # Configuration
        self.font_family = config_manager.get("laptop_gui.font_family", "TkDefaultFont")
        self.font_size = config_manager.get("laptop_gui.font_size", 10)
        
        # Current channel
        self.current_channel = config_manager.get("channels.default_channel", "mesh #bluetooth")
        
        # Setup widget
        self.setup_input_panel()
    
    def setup_input_panel(self) -> None:
        """Set up the input panel widgets."""
        try:
            # Create main frame
            main_frame = ttk.Frame(self.parent)
            main_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Channel selection frame
            channel_frame = ttk.Frame(main_frame)
            channel_frame.pack(fill=tk.X, pady=(0, 5))
            
            # Channel dropdown
            ttk.Label(channel_frame, text="Channel:").pack(side=tk.LEFT, padx=(0, 5))
            
            self.channel_var = tk.StringVar(value=self.current_channel)
            channel_dropdown = ttk.Combobox(
                channel_frame,
                textvariable=self.channel_var,
                values=["mesh #bluetooth", "#local", "#general", "#private"],
                state="readonly",
                font=(self.font_family, self.font_size),
                width=20
            )
            channel_dropdown.pack(side=tk.LEFT, padx=(0, 5))
            
            # Join channel button
            self.join_button = ttk.Button(
                channel_frame,
                text="Join",
                command=self._on_join_channel,
                width=8
            )
            self.join_button.pack(side=tk.LEFT)
            
            # Input frame
            input_frame = ttk.Frame(main_frame)
            input_frame.pack(fill=tk.X)
            
            # Text input field
            self.input_field = ttk.Entry(
                input_frame,
                font=(self.font_family, self.font_size)
            )
            self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
            
            # Send button
            self.send_button = ttk.Button(
                input_frame,
                text="Send",
                command=self._on_send_message,
                width=10
            )
            self.send_button.pack(side=tk.RIGHT)
            
            # Bind keyboard events
            self.input_field.bind("<Return>", self._on_enter_key)
            self.input_field.bind("<Control-Return>", self._on_send_message)
            self.input_field.bind("<Control-l>", self._on_clear_input)
            self.input_field.bind("<Tab>", self._on_tab_complete)
            
            # Set focus to input field
            self.input_field.focus_set()
            
            self.logger.debug("Input panel component initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to setup input panel: {e}")
            raise
    
    def _on_send_message(self) -> None:
        """Handle send button click."""
        try:
            text = self.input_field.get().strip()
            
            if text:
                # Call send callback if provided
                if self.send_callback:
                    self.send_callback(text)
                
                # Clear input field
                self.input_field.delete(0, tk.END)
                
                # Keep focus
                self.input_field.focus_set()
                
                self.logger.debug(f"Message sent: {text[:50]}...")
            else:
                self.logger.debug("Empty message, not sending")
                
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
    
    def _on_enter_key(self, event) -> None:
        """Handle Enter key press in input field."""
        # Prevent default behavior
        return ""
    
    def _on_clear_input(self, event) -> None:
        """Clear the input field."""
        try:
            self.input_field.delete(0, tk.END)
            self.logger.debug("Input field cleared")
        except Exception as e:
            self.logger.error(f"Failed to clear input: {e}")
    
    def _on_tab_complete(self, event) -> None:
        """Handle tab completion for commands or usernames."""
        try:
            current_text = self.input_field.get()
            cursor_pos = self.input_field.index(tk.INSERT)
            
            # Simple tab completion for commands
            if current_text.startswith('/'):
                commands = ['/help', '/join', '/leave', '/msg', '/who', '/status', '/quit']
                
                for cmd in commands:
                    if cmd.startswith(current_text):
                        completion = cmd
                        self.input_field.delete(0, tk.END)
                        self.input_field.insert(0, completion)
                        return
            
            # Prevent default tab behavior
            return "break"
            
        except Exception as e:
            self.logger.error(f"Failed tab completion: {e}")
    
    def _on_join_channel(self) -> None:
        """Handle join channel button click."""
        try:
            selected_channel = self.channel_var.get()
            
            if selected_channel != self.current_channel:
                self.current_channel = selected_channel
                self.logger.info(f"Joining channel: {selected_channel}")
                
                # In a full implementation, this would trigger a channel join event
                # For now, just update the display
                print(f"TODO: Join channel {selected_channel}")
                
                # Update channel dropdown
                self.channel_var.set(selected_channel)
                
        except Exception as e:
            self.logger.error(f"Failed to join channel: {e}")
    
    def get_text(self) -> str:
        """Get the current text from the input field."""
        if self.input_field:
            return self.input_field.get()
        return ""
    
    def set_text(self, text: str) -> None:
        """Set the text in the input field."""
        try:
            if self.input_field:
                self.input_field.delete(0, tk.END)
                self.input_field.insert(0, text)
        except Exception as e:
            self.logger.error(f"Failed to set input text: {e}")
    
    def clear(self) -> None:
        """Clear the input field."""
        try:
            if self.input_field:
                self.input_field.delete(0, tk.END)
        except Exception as e:
            self.logger.error(f"Failed to clear input: {e}")
    
    def focus(self) -> None:
        """Set focus to the input field."""
        try:
            if self.input_field:
                self.input_field.focus_set()
        except Exception as e:
            self.logger.error(f"Failed to focus input field: {e}")
    
    def set_channel(self, channel: str) -> None:
        """Set the current channel."""
        try:
            self.current_channel = channel
            if self.channel_var:
                self.channel_var.set(channel)
        except Exception as e:
            self.logger.error(f"Failed to set channel: {e}")
    
    def get_channel(self) -> str:
        """Get the current channel."""
        return self.current_channel
    
    def set_send_callback(self, callback: Callable) -> None:
        """Set the send message callback function."""
        self.send_callback = callback
    
    def enable(self) -> None:
        """Enable the input panel."""
        try:
            if self.input_field:
                self.input_field.config(state=tk.NORMAL)
            if self.send_button:
                self.send_button.config(state=tk.NORMAL)
            if self.join_button:
                self.join_button.config(state=tk.NORMAL)
        except Exception as e:
            self.logger.error(f"Failed to enable input panel: {e}")
    
    def disable(self) -> None:
        """Disable the input panel."""
        try:
            if self.input_field:
                self.input_field.config(state=tk.DISABLED)
            if self.send_button:
                self.send_button.config(state=tk.DISABLED)
            if self.join_button:
                self.join_button.config(state=tk.DISABLED)
        except Exception as e:
            self.logger.error(f"Failed to disable input panel: {e}")
    
    def get_widgets(self) -> dict:
        """Get all input panel widgets."""
        return {
            "input_field": self.input_field,
            "send_button": self.send_button,
            "join_button": self.join_button,
            "channel_var": self.channel_var
        }