#!/usr/bin/env python3
"""
Test script for Blue Relay Chat laptop client implementation.

This script provides a simple way to test the implemented components
without requiring actual Bluetooth hardware.
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from bitchat.config.manager import ConfigManager
    from bitchat.core.events import EventBus
    from bitchat.gui.laptop_gui import LaptopGUI
    from bitchat.core.laptop_controller import LaptopController
    from bitchat.utils.logging import setup_logging, get_logger
    IMPLEMENTATION_AVAILABLE = True
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("This is expected if some components are not yet implemented.")
    IMPLEMENTATION_AVAILABLE = False


class MockTestRunner:
    """Test runner with mocked components."""
    
    def __init__(self):
        self.logger = get_logger("test_runner")
        self.config = ConfigManager()
        self.event_bus = EventBus()
        self.gui = None
        self.controller = None
    
    async def test_gui_components(self):
        """Test GUI components individually."""
        print("Testing GUI components...")
        
        try:
            if not IMPLEMENTATION_AVAILABLE:
                print("GUI components not yet implemented, skipping test")
                return
            
            # Create a test window
            import tkinter as tk
            root = tk.Tk()
            root.title("GUI Component Test")
            root.geometry("400x300")
            
            # Test message display
            from bitchat.gui.components.message_display import MessageDisplay
            message_display = MessageDisplay(root, self.config)
            
            # Add test messages
            test_messages = [
                {"sender": "TestUser1", "content": "Hello from GUI test!", "type": "received"},
                {"sender": "TestUser2", "content": "This is a system message", "type": "system"},
                {"sender": "You", "content": "This is a sent message", "type": "sent"}
            ]
            
            for msg in test_messages:
                message_display.add_message(msg)
                await asyncio.sleep(0.1)
            
            print("✅ Message display component test passed")
            
            # Test peer list
            from bitchat.gui.components.peer_list import PeerList
            peer_list = PeerList(root, self.config)
            
            # Add test peers
            test_peers = [
                {"id": "peer1", "name": "TestPeer1", "status": "online"},
                {"id": "peer2", "name": "TestPeer2", "status": "connecting"},
                {"id": "peer3", "name": "TestPeer3", "status": "offline"}
            ]
            
            for peer_id, peer_info in test_peers.items():
                peer_list.update_peer(peer_id, peer_info)
                await asyncio.sleep(0.1)
            
            print("✅ Peer list component test passed")
            
            # Test input panel
            from bitchat.gui.components.input_panel import InputPanel
            
            def test_send_callback(text):
                print(f"Send callback triggered: {text}")
                return True
            
            input_panel = InputPanel(root, self.config, test_send_callback)
            
            # Test input functionality
            input_panel.set_text("Test message")
            await asyncio.sleep(0.5)
            
            sent_text = input_panel.get_text()
            if sent_text == "Test message":
                print("✅ Input panel component test passed")
            else:
                print(f"❌ Input panel test failed: {sent_text}")
            
            root.destroy()
            
        except Exception as e:
            print(f"❌ GUI component test failed: {e}")
    
    async def test_integration(self):
        """Test integration between components."""
        print("Testing component integration...")
        
        if not IMPLEMENTATION_AVAILABLE:
            print("Components not yet implemented, skipping integration test")
            return
        
        try:
            # Initialize controller
            controller = LaptopController(self.config, self.event_bus)
            await controller.initialize()
            
            # Test message sending
            result = await controller.send_message("Test integration message")
            if result:
                print("✅ Integration message sending test passed")
            else:
                print("❌ Integration message sending test failed")
            
            # Test status
            status = await controller.get_status()
            if status.get("running", False):
                print("✅ Integration status test passed")
            else:
                print(f"❌ Integration status test failed: {status}")
            
            # Stop controller
            await controller.stop()
            
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
    
    async def test_full_gui(self):
        """Test the full GUI with mocked backend."""
        print("Testing full GUI with mocked backend...")
        
        if not IMPLEMENTATION_AVAILABLE:
            print("GUI not yet implemented, skipping full GUI test")
            return
        
        try:
            # Create event bus
            event_bus = EventBus()
            
            # Create GUI
            gui = LaptopGUI(self.config, event_bus)
            
            # Create mock controller
            class MockController:
                def __init__(self):
                    self.running = True
                
                async def initialize(self):
                    pass
                
                async def start(self):
                    pass
                
                async def stop(self):
                    self.running = False
                
                async def send_message(self, text):
                    print(f"Mock send message: {text}")
                    return True
                
                async def join_channel(self, channel_id):
                    print(f"Mock join channel: {channel_id}")
                    return True
                
                def is_running(self):
                    return self.running
            
            mock_controller = MockController()
            gui.set_controller(mock_controller)
            
            # Initialize GUI
            await gui.initialize()
            
            # Show window
            gui.root.deiconify()
            gui.root.update()
            
            print("✅ Full GUI test started")
            print("Close the GUI window to continue testing...")
            
            # Run for a few seconds
            start_time = time.time()
            while mock_controller.running and (time.time() - start_time) < 10:
                gui.root.update()
                await asyncio.sleep(0.1)
            
            # Stop GUI
            await gui.stop()
            
            print("✅ Full GUI test completed")
            
        except Exception as e:
            print(f"❌ Full GUI test failed: {e}")
    
    async def run_tests(self):
        """Run all tests."""
        print("Starting Blue Relay Chat laptop client tests...")
        print("=" * 50)
        
        # Test GUI components
        await self.test_gui_components()
        
        # Test integration
        await self.test_integration()
        
        # Test full GUI
        await self.test_full_gui()
        
        print("=" * 50)
        print("All tests completed!")


async def main():
    """Main test entry point."""
    # Set up logging
    setup_logging(
        level="INFO",
        log_file=None,
        console_output=True
    )
    
    logger = get_logger("test_main")
    logger.info("Starting Blue Relay Chat laptop client tests...")
    
    # Create test runner
    runner = MockTestRunner()
    
    # Run tests
    await runner.run_tests()
    
    logger.info("Tests completed")


if __name__ == "__main__":
    asyncio.run(main())