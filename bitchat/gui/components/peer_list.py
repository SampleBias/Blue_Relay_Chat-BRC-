"""
Peer list component for Blue Relay Chat laptop client.

This module provides a list widget for displaying connected Bluetooth peers
with status indicators and peer management functionality.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, List

from ...config.manager import ConfigManager
from ...utils.logging import get_logger


class PeerList:
    """Component for displaying and managing connected peers."""
    
    def __init__(self, parent, config_manager: ConfigManager):
        """
        Initialize the peer list component.
        
        Args:
            parent: Parent Tkinter widget
            config_manager: Configuration manager instance
        """
        self.parent = parent
        self.config = config_manager
        self.logger = get_logger("peer_list")
        
        # List widget
        self.listbox: Optional[tk.Listbox] = None
        
        # Peer data
        self.peers: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self.font_family = config_manager.get("laptop_gui.font_family", "TkDefaultFont")
        self.font_size = config_manager.get("laptop_gui.font_size", 10)
        
        # Setup widget
        self.setup_list()
    
    def setup_list(self) -> None:
        """Set up the peer list widget."""
        try:
            # Create main frame
            main_frame = ttk.LabelFrame(self.parent, text="Peers", width=150)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Create listbox with scrollbar
            list_frame = ttk.Frame(main_frame)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            self.listbox = tk.Listbox(
                list_frame,
                selectmode=tk.SINGLE,
                font=(self.font_family, self.font_size),
                height=10
            )
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
            self.listbox.configure(yscrollcommand=scrollbar.set)
            
            # Pack widgets
            self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Bind events
            self.listbox.bind("<Double-Button-1>", self._on_peer_double_click)
            self.listbox.bind("<Button-3>", self._on_peer_right_click)
            
            # Add context menu
            self.setup_context_menu()
            
            self.logger.debug("Peer list component initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to setup peer list: {e}")
            raise
    
    def setup_context_menu(self) -> None:
        """Set up context menu for peer list."""
        try:
            self.context_menu = tk.Menu(self.parent, tearoff=0)
            
            # Add menu items
            self.context_menu.add_command(label="Connect", command=self._connect_to_peer)
            self.context_menu.add_command(label="Disconnect", command=self._disconnect_from_peer)
            self.context_menu.add_command(label="Send Message", command=self._send_private_message)
            self.context_menu.add_separator()
            self.context_menu.add_command(label="View Info", command=self._view_peer_info)
            self.context_menu.add_command(label="Trust/Untrust", command=self._toggle_peer_trust)
            
            # Bind to right-click
            self.listbox.bind("<Button-3>", self._show_context_menu)
            
        except Exception as e:
            self.logger.error(f"Failed to setup context menu: {e}")
    
    def _show_context_menu(self, event) -> None:
        """Show context menu on right-click."""
        try:
            # Select the item under the cursor
            index = self.listbox.nearest(event.y)
            if index >= 0:
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(index)
                
                # Show context menu
                self.context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            self.logger.error(f"Failed to show context menu: {e}")
    
    def update_peer(self, peer_id: str, peer_info: Dict[str, Any]) -> None:
        """
        Update or add a peer in the list.
        
        Args:
            peer_id: Unique identifier for the peer
            peer_info: Dictionary containing peer information
        """
        try:
            self.peers[peer_id] = peer_info
            
            # Find existing entry
            existing_index = self._find_peer_index(peer_id)
            
            # Get display name and status
            display_name = peer_info.get("name", peer_id[:8])
            status = peer_info.get("status", "unknown")
            
            # Format with status indicator
            if status == "online":
                display_text = f"● {display_name}"
            elif status == "connecting":
                display_text = f"◐ {display_name}"
            elif status == "offline":
                display_text = f"○ {display_name}"
            else:
                display_text = f"? {display_name}"
            
            if existing_index >= 0:
                # Update existing entry
                self.listbox.delete(existing_index)
                self.listbox.insert(existing_index, display_text)
            else:
                # Add new entry
                self.listbox.insert(tk.END, display_text)
            
            self.logger.debug(f"Updated peer {peer_id}: {display_text}")
            
        except Exception as e:
            self.logger.error(f"Failed to update peer {peer_id}: {e}")
    
    def remove_peer(self, peer_id: str) -> None:
        """
        Remove a peer from the list.
        
        Args:
            peer_id: Unique identifier for the peer to remove
        """
        try:
            if peer_id in self.peers:
                del self.peers[peer_id]
                
                # Find and remove from listbox
                index = self._find_peer_index(peer_id)
                if index >= 0:
                    self.listbox.delete(index)
                
                self.logger.debug(f"Removed peer {peer_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to remove peer {peer_id}: {e}")
    
    def _find_peer_index(self, peer_id: str) -> int:
        """
        Find the index of a peer in the listbox.
        
        Args:
            peer_id: Unique identifier for the peer
            
        Returns:
            Index of the peer in the listbox, or -1 if not found
        """
        try:
            # Search through all items in the listbox
            for i in range(self.listbox.size()):
                item_text = self.listbox.get(i)
                
                # Extract peer name from display text
                if "● " in item_text:
                    display_name = item_text[2:]  # Remove "● "
                elif "◐ " in item_text:
                    display_name = item_text[2:]  # Remove "◐ "
                elif "○ " in item_text:
                    display_name = item_text[2:]  # Remove "○ "
                elif "? " in item_text:
                    display_name = item_text[2:]  # Remove "? "
                else:
                    display_name = item_text
                
                # Check if this matches our peer
                peer_info = self.peers.get(peer_id, {})
                peer_name = peer_info.get("name", peer_id[:8])
                
                if display_name == peer_name or display_name == peer_id[:8]:
                    return i
            
            return -1
            
        except Exception as e:
            self.logger.error(f"Failed to find peer index: {e}")
            return -1
    
    def get_selected_peer(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the currently selected peer.
        
        Returns:
            Dictionary with peer information, or None if no selection
        """
        try:
            selection_indices = self.listbox.curselection()
            if not selection_indices:
                return None
            
            selected_index = selection_indices[0]
            selected_text = self.listbox.get(selected_index)
            
            # Find peer by display text
            for peer_id, peer_info in self.peers.items():
                display_name = peer_info.get("name", peer_id[:8])
                
                if display_name in selected_text or peer_id[:8] in selected_text:
                    return peer_info
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get selected peer: {e}")
            return None
    
    def get_all_peers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all peers in the list.
        
        Returns:
            Dictionary of all peers with their information
        """
        return self.peers.copy()
    
    def clear(self) -> None:
        """Clear all peers from the list."""
        try:
            self.peers.clear()
            self.listbox.delete(0, tk.END)
            self.logger.debug("Cleared peer list")
            
        except Exception as e:
            self.logger.error(f"Failed to clear peer list: {e}")
    
    def refresh_display(self) -> None:
        """Refresh the display of all peers."""
        try:
            # Clear current display
            self.listbox.delete(0, tk.END)
            
            # Re-add all peers with current status
            for peer_id, peer_info in self.peers.items():
                display_name = peer_info.get("name", peer_id[:8])
                status = peer_info.get("status", "unknown")
                
                if status == "online":
                    display_text = f"● {display_name}"
                elif status == "connecting":
                    display_text = f"◐ {display_name}"
                elif status == "offline":
                    display_text = f"○ {display_name}"
                else:
                    display_text = f"? {display_name}"
                
                self.listbox.insert(tk.END, display_text)
            
            self.logger.debug("Refreshed peer list display")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh peer display: {e}")
    
    # Event handlers
    def _on_peer_double_click(self, event) -> None:
        """Handle double-click on a peer."""
        try:
            selected_peer = self.get_selected_peer()
            if selected_peer:
                self.logger.info(f"Double-clicked peer: {selected_peer.get('name', 'Unknown')}")
                # Could trigger a private message or info display
                self._send_private_message()
        except Exception as e:
            self.logger.error(f"Failed to handle peer double-click: {e}")
    
    def _on_peer_right_click(self, event) -> None:
        """Handle right-click on a peer."""
        # This is handled by the context menu
        pass
    
    def _connect_to_peer(self) -> None:
        """Connect to the selected peer."""
        try:
            selected_peer = self.get_selected_peer()
            if selected_peer:
                peer_id = list(self.peers.keys())[list(self.peers.values()).index(selected_peer)]
                self.logger.info(f"Connecting to peer: {selected_peer.get('name', 'Unknown')}")
                
                # This would trigger a connection request
                # In a full implementation, this would call the Bluetooth transport
                print(f"TODO: Connect to peer {peer_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to connect to peer: {e}")
    
    def _disconnect_from_peer(self) -> None:
        """Disconnect from the selected peer."""
        try:
            selected_peer = self.get_selected_peer()
            if selected_peer:
                peer_id = list(self.peers.keys())[list(self.peers.values()).index(selected_peer)]
                self.logger.info(f"Disconnecting from peer: {selected_peer.get('name', 'Unknown')}")
                
                # This would trigger a disconnection request
                # In a full implementation, this would call the Bluetooth transport
                print(f"TODO: Disconnect from peer {peer_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to disconnect from peer: {e}")
    
    def _send_private_message(self) -> None:
        """Send a private message to the selected peer."""
        try:
            selected_peer = self.get_selected_peer()
            if selected_peer:
                peer_id = list(self.peers.keys())[list(self.peers.values()).index(selected_peer)]
                self.logger.info(f"Sending private message to: {selected_peer.get('name', 'Unknown')}")
                
                # This would trigger a private message dialog
                # In a full implementation, this would open a message dialog
                print(f"TODO: Send private message to peer {peer_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to send private message: {e}")
    
    def _view_peer_info(self) -> None:
        """Show information about the selected peer."""
        try:
            selected_peer = self.get_selected_peer()
            if selected_peer:
                peer_id = list(self.peers.keys())[list(self.peers.values()).index(selected_peer)]
                self.logger.info(f"Viewing info for peer: {selected_peer.get('name', 'Unknown')}")
                
                # This would show a peer info dialog
                # In a full implementation, this would open an info dialog
                print(f"TODO: Show info for peer {peer_id}")
                print(f"Peer info: {selected_peer}")
                
        except Exception as e:
            self.logger.error(f"Failed to view peer info: {e}")
    
    def _toggle_peer_trust(self) -> None:
        """Toggle trust status for the selected peer."""
        try:
            selected_peer = self.get_selected_peer()
            if selected_peer:
                peer_id = list(self.peers.keys())[list(self.peers.values()).index(selected_peer)]
                current_trust = selected_peer.get("trusted", False)
                new_trust = not current_trust
                
                # Update peer trust status
                selected_peer["trusted"] = new_trust
                
                self.logger.info(f"Toggled trust for peer {selected_peer.get('name', 'Unknown')}: {new_trust}")
                
                # This would update the trust status in the database
                # In a full implementation, this would call the identity manager
                print(f"TODO: Toggle trust for peer {peer_id} to {new_trust}")
                
        except Exception as e:
            self.logger.error(f"Failed to toggle peer trust: {e}")
    
    def get_widget(self) -> Optional[tk.Listbox]:
        """Get the underlying Tkinter widget."""
        return self.listbox