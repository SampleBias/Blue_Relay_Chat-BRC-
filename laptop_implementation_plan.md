# Laptop Client Implementation Plan

## Configuration File (config_laptop.ini)

```ini
# Blue Relay Chat - Laptop Client Configuration
# This file contains settings specific to the laptop client implementation

[application]
name = "Blue Relay Chat - Laptop Client"
version = "1.0.0"
debug = false
log_level = "INFO"

[laptop_gui]
window_width = 600
window_height = 400
min_window_width = 400
min_window_height = 300
auto_scroll = true
max_message_history = 1000
font_family = "TkDefaultFont"
font_size = 10
theme = "light"
show_timestamps = true
compact_mode = false

[bluetooth]
adapter_name = "auto"
scan_interval_seconds = 30
max_peers = 20
auto_reconnect = true
connection_timeout_seconds = 10
discovery_timeout_seconds = 30
power_save_mode = false

[messages]
timestamp_format = "%H:%M:%S"
show_system_messages = true
compact_display = false
sound_notifications = false
notification_sound = "default"
max_message_size = 4096
history_retention_days = 7

[channels]
default_channel = "mesh #bluetooth"
auto_join_default = true
show_channel_list = true
max_channel_name_length = 32

[performance]
gui_update_interval_ms = 100
message_queue_size = 500
max_concurrent_connections = 10
memory_limit_mb = 200
cpu_limit_percent = 30

[security]
require_encryption = true
verify_peer_identity = true
auto_trust_known_peers = false
key_rotation_interval_hours = 24

[storage]
data_dir = "~/.local/share/blue-relay-chat"
database_file = "laptop_client.db"
message_history_file = "messages.db"
config_backup = true

[network]
mesh_ttl = 7
retry_attempts = 3
retry_delay_seconds = 5
keepalive_interval_seconds = 60
compression_threshold = 100
```

## Basic Tkinter GUI Structure

### Main GUI Components

#### 1. Main Window Class (`bitchat/gui/laptop_gui.py`)

```python
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..config.manager import ConfigManager
from ..core.events import EventBus, Event, EventTypes
from ..utils.logging import get_logger

class LaptopGUI:
    """Main GUI for Blue Relay Chat laptop client."""
    
    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        self.config = config_manager
        self.event_bus = event_bus
        self.logger = get_logger("laptop_gui")
        
        # GUI components
        self.root: Optional[tk.Tk] = None
        self.message_display: Optional[scrolledtext.ScrolledText] = None
        self.input_field: Optional[tk.Entry] = None
        self.peer_list: Optional[tk.Listbox] = None
        self.channel_var: Optional[tk.StringVar] = None
        self.status_label: Optional[tk.Label] = None
        
        # State
        self._running = False
        self._current_channel = config_manager.get("channels.default_channel", "mesh #bluetooth")
        self._message_history: List[Dict[str, Any]] = []
        self._connected_peers: Dict[str, Dict[str, Any]] = {}
        
        # GUI settings
        self.window_width = config_manager.get("laptop_gui.window_width", 600)
        self.window_height = config_manager.get("laptop_gui.window_height", 400)
        self.font_size = config_manager.get("laptop_gui.font_size", 10)
```

#### 2. Window Layout Implementation

```python
def create_window(self) -> None:
    """Create the main application window."""
    self.root = tk.Tk()
    self.root.title("Blue Relay Chat - Laptop Client")
    self.root.geometry(f"{self.window_width}x{self.window_height}")
    self.root.minsize(
        self.config.get("laptop_gui.min_window_width", 400),
        self.config.get("laptop_gui.min_window_height", 300)
    )
    
    # Configure styles
    self.setup_styles()
    
    # Create main frames
    self.create_main_frames()
    
    # Create status bar
    self.create_status_bar()
    
    # Setup event handlers
    self.setup_event_handlers()
    
    # Handle window close
    self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)

def create_main_frames(self) -> None:
    """Create the main layout frames."""
    # Main container
    main_frame = ttk.Frame(self.root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Top section (status and channel)
    top_frame = ttk.Frame(main_frame)
    top_frame.pack(fill=tk.X, pady=(0, 5))
    
    # Middle section (peer list and messages)
    middle_frame = ttk.Frame(main_frame)
    middle_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
    
    # Bottom section (input and controls)
    bottom_frame = ttk.Frame(main_frame)
    bottom_frame.pack(fill=tk.X)
    
    # Create components in each frame
    self.create_channel_selector(top_frame)
    self.create_peer_and_message_area(middle_frame)
    self.create_input_area(bottom_frame)

def create_peer_and_message_area(self, parent: ttk.Frame) -> None:
    """Create the peer list and message display area."""
    # Create paned window for resizable sections
    paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
    paned.pack(fill=tk.BOTH, expand=True)
    
    # Peer list frame
    peer_frame = ttk.LabelFrame(paned, text="Peers", width=150)
    paned.add(peer_frame, weight=1)
    
    self.peer_list = tk.Listbox(peer_frame, selectmode=tk.SINGLE)
    peer_scrollbar = ttk.Scrollbar(peer_frame, orient=tk.VERTICAL, command=self.peer_list.yview)
    self.peer_list.configure(yscrollcommand=peer_scrollbar.set)
    
    self.peer_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    peer_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Message display frame
    message_frame = ttk.LabelFrame(paned, text="Messages")
    paned.add(message_frame, weight=3)
    
    self.message_display = scrolledtext.ScrolledText(
        message_frame,
        wrap=tk.WORD,
        state=tk.DISABLED,
        font=(self.config.get("laptop_gui.font_family", "TkDefaultFont"), self.font_size)
    )
    self.message_display.pack(fill=tk.BOTH, expand=True)
    
    # Configure text tags for different message types
    self.message_display.tag_configure("timestamp", foreground="gray")
    self.message_display.tag_configure("system", foreground="blue", font=("TkDefaultFont", self.font_size, "italic"))
    self.message_display.tag_configure("error", foreground="red")
    self.message_display.tag_configure("sent", foreground="green")
    self.message_display.tag_configure("received", foreground="black")

def create_input_area(self, parent: ttk.Frame) -> None:
    """Create the message input area."""
    # Input frame
    input_frame = ttk.Frame(parent)
    input_frame.pack(fill=tk.X, pady=(5, 0))
    
    # Message input field
    self.input_field = ttk.Entry(input_frame, font=("TkDefaultFont", self.font_size))
    self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    
    # Send button
    send_button = ttk.Button(input_frame, text="Send", command=self.send_message)
    send_button.pack(side=tk.LEFT, padx=(0, 5))
    
    # Join channel button
    join_button = ttk.Button(input_frame, text="Join", command=self.join_channel)
    join_button.pack(side=tk.LEFT)
    
    # Bind Enter key to send message
    self.input_field.bind("<Return>", lambda e: self.send_message())

def create_status_bar(self) -> None:
    """Create the status bar at the bottom."""
    status_frame = ttk.Frame(self.root)
    status_frame.pack(fill=tk.X, side=tk.BOTTOM)
    
    self.status_label = ttk.Label(
        status_frame,
        text="Disconnected",
        relief=tk.SUNKEN,
        anchor=tk.W
    )
    self.status_label.pack(fill=tk.X, padx=2, pady=2)
```

#### 3. Message Display Functions

```python
def add_message(self, message: Dict[str, Any]) -> None:
    """Add a message to the display."""
    timestamp = datetime.now().strftime(self.config.get("messages.timestamp_format", "%H:%M:%S"))
    sender = message.get("sender", "Unknown")
    content = message.get("content", "")
    msg_type = message.get("type", "received")
    
    # Enable text widget for editing
    self.message_display.config(state=tk.NORMAL)
    
    # Add timestamp
    self.message_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
    
    # Format based on message type
    if msg_type == "sent":
        self.message_display.insert(tk.END, f"You: ", "sent")
        self.message_display.insert(tk.END, f"{content}\n", "sent")
    elif msg_type == "system":
        self.message_display.insert(tk.END, f"System: ", "system")
        self.message_display.insert(tk.END, f"{content}\n", "system")
    elif msg_type == "error":
        self.message_display.insert(tk.END, f"Error: ", "error")
        self.message_display.insert(tk.END, f"{content}\n", "error")
    else:
        self.message_display.insert(tk.END, f"{sender}: ", "received")
        self.message_display.insert(tk.END, f"{content}\n", "received")
    
    # Disable text widget and scroll to bottom
    self.message_display.config(state=tk.DISABLED)
    
    if self.config.get("laptop_gui.auto_scroll", True):
        self.message_display.see(tk.END)
    
    # Add to history
    self._message_history.append({
        "timestamp": datetime.now(),
        "sender": sender,
        "content": content,
        "type": msg_type
    })
    
    # Limit history size
    max_history = self.config.get("laptop_gui.max_message_history", 1000)
    if len(self._message_history) > max_history:
        self._message_history.pop(0)

def update_peer_list(self) -> None:
    """Update the peer list display."""
    self.peer_list.delete(0, tk.END)
    
    for peer_id, peer_info in self._connected_peers.items():
        display_name = peer_info.get("name", peer_id[:8])
        status = peer_info.get("status", "unknown")
        
        if status == "online":
            display_name = f"● {display_name}"
        elif status == "connecting":
            display_name = f"◐ {display_name}"
        else:
            display_name = f"○ {display_name}"
        
        self.peer_list.insert(tk.END, display_name)

def update_status(self, status_text: str) -> None:
    """Update the status bar."""
    self.status_label.config(text=status_text)
```

### GUI Component Files Structure

#### 1. Message Display Component (`bitchat/gui/components/message_display.py`)

```python
import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Dict, Any, List
from datetime import datetime

class MessageDisplay:
    """Component for displaying chat messages."""
    
    def __init__(self, parent, config_manager):
        self.parent = parent
        self.config = config_manager
        self.display = None
        self.setup_display()
    
    def setup_display(self):
        """Set up the message display widget."""
        self.display = scrolledtext.ScrolledText(
            self.parent,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=(self.config.get("laptop_gui.font_family", "TkDefaultFont"), 
                  self.config.get("laptop_gui.font_size", 10))
        )
        self.display.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags
        self.setup_tags()
    
    def setup_tags(self):
        """Configure text tags for different message types."""
        self.display.tag_configure("timestamp", foreground="gray")
        self.display.tag_configure("system", foreground="blue", font=("TkDefaultFont", 10, "italic"))
        self.display.tag_configure("error", foreground="red")
        self.display.tag_configure("sent", foreground="green")
        self.display.tag_configure("received", foreground="black")
    
    def add_message(self, message: Dict[str, Any]):
        """Add a message to the display."""
        # Implementation similar to main GUI class
        pass
    
    def clear(self):
        """Clear all messages."""
        self.display.config(state=tk.NORMAL)
        self.display.delete(1.0, tk.END)
        self.display.config(state=tk.DISABLED)
```

#### 2. Peer List Component (`bitchat/gui/components/peer_list.py`)

```python
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any

class PeerList:
    """Component for displaying connected peers."""
    
    def __init__(self, parent, config_manager):
        self.parent = parent
        self.config = config_manager
        self.listbox = None
        self.peers: Dict[str, Dict[str, Any]] = {}
        self.setup_list()
    
    def setup_list(self):
        """Set up the peer list widget."""
        frame = ttk.LabelFrame(self.parent, text="Peers", width=150)
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.listbox = tk.Listbox(frame, selectmode=tk.SINGLE)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def update_peer(self, peer_id: str, peer_info: Dict[str, Any]):
        """Update or add a peer in the list."""
        self.peers[peer_id] = peer_info
        self.refresh_display()
    
    def remove_peer(self, peer_id: str):
        """Remove a peer from the list."""
        if peer_id in self.peers:
            del self.peers[peer_id]
            self.refresh_display()
    
    def refresh_display(self):
        """Refresh the peer list display."""
        self.listbox.delete(0, tk.END)
        
        for peer_id, peer_info in self.peers.items():
            display_name = peer_info.get("name", peer_id[:8])
            status = peer_info.get("status", "unknown")
            
            if status == "online":
                display_name = f"● {display_name}"
            elif status == "connecting":
                display_name = f"◐ {display_name}"
            else:
                display_name = f"○ {display_name}"
            
            self.listbox.insert(tk.END, display_name)
```

#### 3. Input Panel Component (`bitchat/gui/components/input_panel.py`)

```python
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

class InputPanel:
    """Component for message input and controls."""
    
    def __init__(self, parent, config_manager, send_callback: Optional[Callable] = None):
        self.parent = parent
        self.config = config_manager
        self.send_callback = send_callback
        self.input_field = None
        self.setup_input()
    
    def setup_input(self):
        """Set up the input panel."""
        frame = ttk.Frame(self.parent)
        frame.pack(fill=tk.X, pady=(5, 0))
        
        # Message input field
        self.input_field = ttk.Entry(
            frame, 
            font=(self.config.get("laptop_gui.font_family", "TkDefaultFont"), 
                  self.config.get("laptop_gui.font_size", 10))
        )
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Send button
        send_button = ttk.Button(frame, text="Send", command=self.on_send)
        send_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Join channel button
        join_button = ttk.Button(frame, text="Join", command=self.on_join)
        join_button.pack(side=tk.LEFT)
        
        # Bind Enter key
        self.input_field.bind("<Return>", lambda e: self.on_send())
    
    def on_send(self):
        """Handle send button press."""
        if self.send_callback:
            text = self.input_field.get().strip()
            if text:
                self.send_callback(text)
                self.input_field.delete(0, tk.END)
    
    def on_join(self):
        """Handle join button press."""
        # Implementation for joining channels
        pass
    
    def get_text(self) -> str:
        """Get the current input text."""
        return self.input_field.get()
    
    def clear(self):
        """Clear the input field."""
        self.input_field.delete(0, tk.END)
    
    def focus(self):
        """Set focus to the input field."""
        self.input_field.focus_set()
```

## Main Entry Point

### Laptop Client Main (`main_laptop.py`)

```python
#!/usr/bin/env python3
"""
Main entry point for Blue Relay Chat laptop client.
"""

import asyncio
import sys
import os
import signal
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from bitchat.config.manager import ConfigManager
    from bitchat.gui.laptop_gui import LaptopGUI
    from bitchat.core.events import EventBus
    from bitchat.utils.logging import setup_logging, get_logger
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

class LaptopClientApp:
    """Main application for the laptop client."""
    
    def __init__(self):
        self.logger = get_logger("main")
        self.config = ConfigManager("config_laptop.ini")
        self.event_bus = EventBus()
        self.gui: Optional[LaptopGUI] = None
        self._running = False
        self._shutdown_requested = False
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle system signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self._shutdown_requested = True
    
    async def initialize(self):
        """Initialize the application."""
        try:
            self.logger.info("Initializing laptop client...")
            
            # Initialize GUI
            self.gui = LaptopGUI(self.config, self.event_bus)
            await self.gui.initialize()
            
            self.logger.info("Laptop client initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            raise
    
    async def start(self):
        """Start the application."""
        if self._running:
            return
        
        self._running = True
        self.logger.info("Starting laptop client...")
        
        try:
            # Start GUI
            await self.gui.start()
            
            # Run main loop
            while self._running and not self._shutdown_requested:
                await asyncio.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"Application error: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the application."""
        if not self._running:
            return
        
        self._running = False
        self.logger.info("Stopping laptop client...")
        
        try:
            if self.gui:
                await self.gui.stop()
            
            self.logger.info("Laptop client stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping application: {e}")

async def main():
    """Main entry point."""
    # Set up logging
    setup_logging(
        level="INFO",
        log_file=None,
        console_output=True
    )
    
    logger = get_logger("main")
    logger.info("Starting Blue Relay Chat Laptop Client...")
    
    # Create and run application
    app = LaptopClientApp()
    
    try:
        await app.initialize()
        await app.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

This implementation plan provides a comprehensive foundation for the laptop client GUI with all the necessary components and structure. The design follows the principles outlined in the design document and provides a clean, modular approach to building the interface.