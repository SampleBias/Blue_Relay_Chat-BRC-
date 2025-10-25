"""
Main GUI for Blue Relay Chat laptop client.

This module provides the main application window that integrates
all GUI components and handles user interactions.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from ..config.manager import ConfigManager
from ..core.events import EventBus, Event, EventTypes
from ..utils.logging import get_logger
from .components.message_display import MessageDisplay
from .components.peer_list import PeerList
from .components.input_panel import InputPanel


class LaptopGUI:
    """Main GUI for Blue Relay Chat laptop client."""
    
    # UI modes
    UI_MODE_CHAT = "chat"
    UI_MODE_SETTINGS = "settings"
    UI_MODE_ABOUT = "about"
    
    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        """
        Initialize the laptop GUI.
        
        Args:
            config_manager: Configuration manager instance
            event_bus: Event bus for component communication
        """
        self.config = config_manager
        self.event_bus = event_bus
        self.logger = get_logger("laptop_gui")
        
        # Main window
        self.root: Optional[tk.Tk] = None
        
        # GUI components
        self.message_display: Optional[MessageDisplay] = None
        self.peer_list: Optional[PeerList] = None
        self.input_panel: Optional[InputPanel] = None
        
        # Status bar
        self.status_label: Optional[ttk.Label] = None
        
        # UI state
        self._current_mode = self.UI_MODE_CHAT
        self._current_channel = config_manager.get("channels.default_channel", "mesh #bluetooth")
        self._connected_peers = 0
        self._transport_status = {"mesh": "offline", "nostr": "offline"}
        
        # Configuration
        self.window_width = config_manager.get("laptop_gui.window_width", 600)
        self.window_height = config_manager.get("laptop_gui.window_height", 400)
        self.min_width = config_manager.get("laptop_gui.min_window_width", 400)
        self.min_height = config_manager.get("laptop_gui.min_window_height", 300)
        
        # Application state
        self._running = False
        self._initialized = False
        
        self.logger.info("Laptop GUI initialized")
    
    async def initialize(self) -> None:
        """Initialize the GUI components."""
        try:
            # Create main window
            self.create_window()
            
            # Create GUI components
            await self.create_components()
            
            # Setup event subscriptions
            self.setup_event_subscriptions()
            
            # Setup window close handler
            self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
            
            # Show welcome message
            self.show_welcome_message()
            
            self._initialized = True
            self.logger.info("Laptop GUI initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize GUI: {e}")
            raise
    
    def create_window(self) -> None:
        """Create the main application window."""
        try:
            self.root = tk.Tk()
            self.root.title("Blue Relay Chat - Laptop Client")
            self.root.geometry(f"{self.window_width}x{self.window_height}")
            self.root.minsize(self.min_width, self.min_height)
            
            # Center window on screen
            self.center_window()
            
            # Create menu bar
            self.create_menu_bar()
            
            # Create status bar
            self.create_status_bar()
            
            self.logger.debug("Main window created")
            
        except Exception as e:
            self.logger.error(f"Failed to create window: {e}")
            raise
    
    def center_window(self) -> None:
        """Center the window on the screen."""
        try:
            self.root.update_idletasks()
            
            # Get window dimensions
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            
            # Get screen dimensions
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Calculate center position
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)
            
            # Set window position
            self.root.geometry(f"{width}x{height}+{x}+{y}")
            
        except Exception as e:
            self.logger.error(f"Failed to center window: {e}")
    
    def create_menu_bar(self) -> None:
        """Create the application menu bar."""
        try:
            menubar = tk.Menu(self.root)
            self.root.config(menu=menubar)
            
            # File menu
            file_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="File", menu=file_menu)
            
            file_menu.add_command(label="Settings", command=self._show_settings)
            file_menu.add_separator()
            file_menu.add_command(label="Exit", command=self._on_window_close)
            
            # Edit menu
            edit_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Edit", menu=edit_menu)
            
            edit_menu.add_command(label="Clear Messages", command=self._clear_messages)
            edit_menu.add_command(label="Clear Peers", command=self._clear_peers)
            
            # View menu
            view_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="View", menu=view_menu)
            
            view_menu.add_command(label="Refresh", command=self._refresh_peers)
            view_menu.add_command(label="Status", command=self._show_status)
            
            # Help menu
            help_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Help", menu=help_menu)
            
            help_menu.add_command(label="User Guide", command=self._show_user_guide)
            help_menu.add_command(label="About", command=self._show_about)
            
            self.logger.debug("Menu bar created")
            
        except Exception as e:
            self.logger.error(f"Failed to create menu bar: {e}")
    
    def create_status_bar(self) -> None:
        """Create the status bar at the bottom of the window."""
        try:
            status_frame = ttk.Frame(self.root)
            status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)
            
            self.status_label = ttk.Label(
                status_frame,
                text="Status: Initializing...",
                relief=tk.SUNKEN,
                anchor=tk.W
            )
            self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            self.logger.debug("Status bar created")
            
        except Exception as e:
            self.logger.error(f"Failed to create status bar: {e}")
    
    async def create_components(self) -> None:
        """Create and arrange GUI components."""
        try:
            # Create main container frame
            main_frame = ttk.Frame(self.root)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Create paned window for resizable sections
            paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
            paned.pack(fill=tk.BOTH, expand=True)
            
            # Peer list frame
            peer_frame = ttk.LabelFrame(paned, text="Peers", width=150)
            paned.add(peer_frame, weight=1)
            
            # Message display frame
            message_frame = ttk.LabelFrame(paned, text="Messages")
            paned.add(message_frame, weight=3)
            
            # Create components
            self.peer_list = PeerList(peer_frame, self.config)
            self.message_display = MessageDisplay(message_frame, self.config)
            
            # Input panel frame
            input_frame = ttk.Frame(self.root)
            input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
            
            self.input_panel = InputPanel(input_frame, self.config, self._on_send_message)
            
            self.logger.debug("GUI components created")
            
        except Exception as e:
            self.logger.error(f"Failed to create components: {e}")
            raise
    
    def setup_event_subscriptions(self) -> None:
        """Set up event subscriptions for GUI updates."""
        try:
            # Subscribe to message events
            self.event_bus.subscribe(EventTypes.MESSAGE_RECEIVED, self._on_message_received)
            self.event_bus.subscribe(EventTypes.MESSAGE_SENT, self._on_message_sent)
            self.event_bus.subscribe(EventTypes.PEER_CONNECTED, self._on_peer_connected)
            self.event_bus.subscribe(EventTypes.PEER_DISCONNECTED, self._on_peer_disconnected)
            self.event_bus.subscribe(EventTypes.TRANSPORT_CONNECTED, self._on_transport_connected)
            self.event_bus.subscribe(EventTypes.TRANSPORT_DISCONNECTED, self._on_transport_disconnected)
            self.event_bus.subscribe(EventTypes.CHANNEL_JOINED, self._on_channel_joined)
            
            self.logger.debug("Event subscriptions set up")
            
        except Exception as e:
            self.logger.error(f"Failed to setup event subscriptions: {e}")
    
    def show_welcome_message(self) -> None:
        """Show a welcome message in the message display."""
        try:
            welcome_msg = {
                "sender": "System",
                "content": "Welcome to Blue Relay Chat! Your laptop client is ready.",
                "type": "system",
                "timestamp": datetime.now()
            }
            
            self.message_display.add_message(welcome_msg)
            
        except Exception as e:
            self.logger.error(f"Failed to show welcome message: {e}")
    
    def update_status(self, status_text: str) -> None:
        """Update the status bar text."""
        try:
            if self.status_label:
                self.status_label.config(text=f"Status: {status_text}")
        except Exception as e:
            self.logger.error(f"Failed to update status: {e}")
    
    async def start(self) -> None:
        """Start the GUI main loop."""
        if self._running:
            self.logger.warning("GUI is already running")
            return
        
        if not self._initialized:
            raise RuntimeError("GUI must be initialized before starting")
        
        self._running = True
        self.logger.info("Starting laptop GUI...")
        
        try:
            # Show window
            self.root.deiconify()
            self.root.update()
            
            # Run main loop
            while self._running:
                try:
                    # Update GUI
                    self.root.update()
                    
                    # Small delay to prevent high CPU usage
                    await asyncio.sleep(0.05)
                    
                except tk.TclError as e:
                    self.logger.error(f"TclError in GUI loop: {e}")
                    break
                except Exception as e:
                    self.logger.error(f"Error in GUI loop: {e}")
                    await asyncio.sleep(0.1)
            
        except Exception as e:
            self.logger.error(f"GUI loop error: {e}")
        finally:
            self._running = False
    
    async def stop(self) -> None:
        """Stop the GUI."""
        self._running = False
        self.logger.info("Stopping laptop GUI...")
        
        try:
            if self.root:
                self.root.quit()
        except Exception as e:
            self.logger.error(f"Error stopping GUI: {e}")
    
    # Event handlers
    def _on_send_message(self, text: str) -> None:
        """Handle message sending from input panel."""
        try:
            if text.strip():
                # Create message object
                message = {
                    "content": text.strip(),
                    "type": "text",
                    "sender": "You",
                    "timestamp": datetime.now(),
                    "channel_id": self._current_channel
                }
                
                # Publish message sent event
                asyncio.create_task(self.event_bus.publish(Event(
                    type=EventTypes.MESSAGE_SENT,
                    data={"message": message},
                    source="gui"
                )))
                
                # Add to display
                self.message_display.add_message(message)
                
                self.logger.debug(f"Message sent: {text[:50]}...")
                
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
    
    async def _on_message_received(self, event: Event) -> None:
        """Handle received message event."""
        try:
            message_data = event.data.get("message", {})
            
            # Add message to display
            self.message_display.add_message(message_data)
            
            self.logger.debug(f"Message received: {message_data.get('content', '')[:50]}...")
            
        except Exception as e:
            self.logger.error(f"Failed to handle received message: {e}")
    
    async def _on_message_sent(self, event: Event) -> None:
        """Handle message sent event."""
        try:
            # Message is already in display from _on_send_message
            # This could be used for delivery confirmation
            message_data = event.data.get("message", {})
            
            self.logger.debug(f"Message sent confirmation: {message_data.get('content', '')[:50]}...")
            
        except Exception as e:
            self.logger.error(f"Failed to handle message sent event: {e}")
    
    async def _on_peer_connected(self, event: Event) -> None:
        """Handle peer connected event."""
        try:
            peer_data = event.data.get("peer", {})
            peer_id = peer_data.get("id", "unknown")
            peer_info = peer_data.get("info", {})
            
            # Update peer list
            self.peer_list.update_peer(peer_id, peer_info)
            
            # Update connected peers count
            self._connected_peers += 1
            self._update_status_display()
            
            self.logger.info(f"Peer connected: {peer_info.get('name', peer_id)}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle peer connected: {e}")
    
    async def _on_peer_disconnected(self, event: Event) -> None:
        """Handle peer disconnected event."""
        try:
            peer_data = event.data.get("peer", {})
            peer_id = peer_data.get("id", "unknown")
            
            # Remove from peer list
            self.peer_list.remove_peer(peer_id)
            
            # Update connected peers count
            self._connected_peers = max(0, self._connected_peers - 1)
            self._update_status_display()
            
            self.logger.info(f"Peer disconnected: {peer_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle peer disconnected: {e}")
    
    async def _on_transport_connected(self, event: Event) -> None:
        """Handle transport connected event."""
        try:
            transport_type = event.data.get("transport_type", "unknown")
            self._transport_status[transport_type] = "online"
            self._update_status_display()
            
            self.logger.info(f"Transport connected: {transport_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle transport connected: {e}")
    
    async def _on_transport_disconnected(self, event: Event) -> None:
        """Handle transport disconnected event."""
        try:
            transport_type = event.data.get("transport_type", "unknown")
            self._transport_status[transport_type] = "offline"
            self._update_status_display()
            
            self.logger.info(f"Transport disconnected: {transport_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle transport disconnected: {e}")
    
    async def _on_channel_joined(self, event: Event) -> None:
        """Handle channel joined event."""
        try:
            channel_id = event.data.get("channel_id", "unknown")
            self._current_channel = channel_id
            
            # Update input panel
            if self.input_panel:
                self.input_panel.set_channel(channel_id)
            
            self._update_status_display()
            
            self.logger.info(f"Channel joined: {channel_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle channel joined: {e}")
    
    def _update_status_display(self) -> None:
        """Update the status bar with current information."""
        try:
            # Build status text
            mesh_status = self._transport_status.get("mesh", "offline")
            nostr_status = self._transport_status.get("nostr", "offline")
            
            status_parts = [
                f"Peers: {self._connected_peers}",
                f"Channel: {self._current_channel}",
                f"Mesh: {mesh_status[0].upper()}",
                f"Nostr: {nostr_status[0].upper()}"
            ]
            
            status_text = " | ".join(status_parts)
            self.update_status(status_text)
            
        except Exception as e:
            self.logger.error(f"Failed to update status display: {e}")
    
    # Menu command handlers
    def _show_settings(self) -> None:
        """Show settings dialog."""
        try:
            # This would open a settings dialog
            # For now, just show a message
            messagebox.showinfo("Settings", "Settings dialog not yet implemented")
            
        except Exception as e:
            self.logger.error(f"Failed to show settings: {e}")
    
    def _clear_messages(self) -> None:
        """Clear all messages."""
        try:
            if self.message_display:
                self.message_display.clear()
            
        except Exception as e:
            self.logger.error(f"Failed to clear messages: {e}")
    
    def _clear_peers(self) -> None:
        """Clear all peers."""
        try:
            if self.peer_list:
                self.peer_list.clear()
                self._connected_peers = 0
                self._update_status_display()
            
        except Exception as e:
            self.logger.error(f"Failed to clear peers: {e}")
    
    def _refresh_peers(self) -> None:
        """Refresh the peer list."""
        try:
            if self.peer_list:
                self.peer_list.refresh_display()
            
        except Exception as e:
            self.logger.error(f"Failed to refresh peers: {e}")
    
    def _show_status(self) -> None:
        """Show detailed status information."""
        try:
            status_info = f"""Blue Relay Chat Status
            
Connected Peers: {self._connected_peers}
Current Channel: {self._current_channel}
Mesh Status: {self._transport_status.get('mesh', 'unknown')}
Nostr Status: {self._transport_status.get('nostr', 'unknown')}

Application Version: {self.config.get('application.version', '1.0.0')}
Platform: {self.config.get_hardware_info().get('platform_name', 'Unknown')}
"""
            
            messagebox.showinfo("Status", status_info)
            
        except Exception as e:
            self.logger.error(f"Failed to show status: {e}")
    
    def _show_user_guide(self) -> None:
        """Show user guide."""
        try:
            guide_info = """Blue Relay Chat - User Guide

Getting Started:
1. Ensure Bluetooth is enabled on your device
2. The application will automatically discover nearby BRC devices
3. Type your message and press Enter to send
4. Use the peer list to see connected devices

Basic Commands:
- /help - Show this help message
- /join <channel> - Join a specific channel
- /who - Show all connected peers
- /status - Show detailed status information

For more information, see the user guide documentation."""
            
            messagebox.showinfo("User Guide", guide_info)
            
        except Exception as e:
            self.logger.error(f"Failed to show user guide: {e}")
    
    def _show_about(self) -> None:
        """Show about dialog."""
        try:
            about_info = """Blue Relay Chat - Laptop Client
Version: 1.0.0

A decentralized messaging application using Bluetooth mesh networking.
Communicate with nearby devices without requiring internet connectivity.

© 2024 Blue Relay Chat Project"""
            
            messagebox.showinfo("About Blue Relay Chat", about_info)
            
        except Exception as e:
            self.logger.error(f"Failed to show about: {e}")
    
    def _on_window_close(self) -> None:
        """Handle window close event."""
        try:
            # Confirm close if there are active connections
            if self._connected_peers > 0:
                result = messagebox.askyesno(
                    "Confirm Exit",
                    f"You have {self._connected_peers} active connections. Are you sure you want to exit?"
                )
                if not result:
                    return
            
            # Publish shutdown event
            asyncio.create_task(self.event_bus.publish(Event(
                type=EventTypes.SYSTEM_SHUTDOWN,
                data={"source": "gui"},
                source="gui"
            )))
            
            # Stop GUI
            self._running = False
            
        except Exception as e:
            self.logger.error(f"Failed to handle window close: {e}")
    
    def get_widget(self) -> Optional[tk.Tk]:
        """Get the main Tkinter widget."""
        return self.root