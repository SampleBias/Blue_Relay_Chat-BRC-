# Testing Guide for Blue Relay Chat Laptop Client

## Overview

This guide provides step-by-step instructions for testing the Blue Relay Chat laptop client implementation. Since we've completed the planning phase, this guide focuses on practical testing approaches.

## Testing Approaches

### 1. Mock Testing (Recommended for Development)

Since the full implementation requires actual Bluetooth hardware, you can start with mock testing:

#### Create Mock Environment
```python
# tests/mocks/bluetooth_mock.py
import asyncio
from typing import Dict, List, Any
from unittest.mock import Mock

class MockBluetoothAdapter:
    """Mock Bluetooth adapter for testing without hardware."""
    
    def __init__(self):
        self.discovered_devices = []
        self.connected_devices = {}
        self.message_history = []
    
    async def scan_for_devices(self, duration: int = 10) -> List[Dict[str, Any]]:
        """Mock device scanning."""
        # Simulate finding devices after delay
        await asyncio.sleep(duration)
        
        mock_devices = [
            {
                "address": "00:11:22:33:44:55",
                "name": "MockDevice1",
                "rssi": -60,
                "services": ["12345678-1234-1234-1234-123456789abc"]
            },
            {
                "address": "00:11:22:33:44:66",
                "name": "MockDevice2", 
                "rssi": -70,
                "services": ["12345678-1234-1234-1234-123456789abc"]
            }
        ]
        
        self.discovered_devices.extend(mock_devices)
        return mock_devices
    
    async def connect_to_device(self, address: str) -> bool:
        """Mock device connection."""
        await asyncio.sleep(1)  # Simulate connection time
        
        if address in [dev["address"] for dev in self.discovered_devices]:
            self.connected_devices[address] = {
                "connected": True,
                "connection_time": asyncio.get_event_loop().time()
            }
            return True
        return False
    
    async def send_message(self, address: str, message: Dict[str, Any]) -> bool:
        """Mock message sending."""
        if address not in self.connected_devices:
            return False
        
        # Store message in history
        self.message_history.append({
            "recipient": address,
            "message": message,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Simulate message delivery
        await asyncio.sleep(0.1)
        return True
    
    async def disconnect_device(self, address: str) -> bool:
        """Mock device disconnection."""
        if address in self.connected_devices:
            del self.connected_devices[address]
            return True
        return False
```

#### Mock GUI Testing
```python
# tests/test_mock_gui.py
import tkinter as tk
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bitchat.gui.laptop_gui import LaptopGUI
from bitchat.config.manager import ConfigManager
from bitchat.core.events import EventBus
from tests.mocks.bluetooth_mock import MockBluetoothAdapter

class MockTestRunner:
    """Test runner with mocked components."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.config = ConfigManager()
        self.event_bus = EventBus()
        self.mock_bluetooth = MockBluetoothAdapter()
        
        # Patch the Bluetooth transport to use mock
        import bitchat.transports.laptop_bluetooth
        bitchat.transports.laptop_bluetooth.BleakScanner = MockBluetoothAdapter
        
        self.gui = LaptopGUI(self.config, self.event_bus)
    
    async def test_basic_functionality(self):
        """Test basic GUI functionality with mock data."""
        print("Testing basic GUI functionality...")
        
        # Initialize GUI
        await self.gui.initialize()
        
        # Show window
        self.gui.root.deiconify()
        self.gui.root.update()
        
        # Test adding messages
        test_messages = [
            {"sender": "TestUser1", "content": "Hello from mock!", "type": "received"},
            {"sender": "TestUser2", "content": "Mock message 2", "type": "received"},
            {"sender": "You", "content": "Sent message", "type": "sent"}
        ]
        
        for msg in test_messages:
            self.gui.add_message(msg)
            await asyncio.sleep(0.1)
        
        # Test peer list
        test_peers = [
            {"id": "peer1", "name": "MockPeer1", "status": "online"},
            {"id": "peer2", "name": "MockPeer2", "status": "connecting"}
        ]
        
        for peer in test_peers:
            self.gui.update_peer(peer["id"], peer)
            await asyncio.sleep(0.1)
        
        print("Basic functionality test completed. Check the GUI window.")
        print("Press Ctrl+C to continue...")
        
        # Keep GUI running for inspection
        try:
            while True:
                self.gui.root.update()
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("\nContinuing with next test...")
    
    def run_tests(self):
        """Run all mock tests."""
        print("Starting mock GUI tests...")
        
        # Run in async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self.test_basic_functionality())
        finally:
            loop.close()
            self.root.destroy()

if __name__ == "__main__":
    runner = MockTestRunner()
    runner.run_tests()
```

### 2. Minimal Implementation Testing

Create a minimal version to test core concepts:

#### Minimal GUI Test
```python
# test_minimal_gui.py
import tkinter as tk
from tkinter import ttk, scrolledtext
import asyncio
import time

class MinimalLaptopGUI:
    """Minimal GUI for testing basic concepts."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BRC Laptop Client - Test")
        self.root.geometry("600x400")
        
        self.setup_ui()
        self.test_data = []
    
    def setup_ui(self):
        """Set up minimal UI for testing."""
        # Status bar
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Status: Testing Mode")
        self.status_label.pack(side=tk.LEFT)
        
        # Main content area
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # Peer list
        peer_frame = ttk.LabelFrame(content_frame, text="Peers")
        peer_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        self.peer_list = tk.Listbox(peer_frame, width=20)
        self.peer_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Message area
        message_frame = ttk.LabelFrame(content_frame, text="Messages")
        message_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.message_display = scrolledtext.ScrolledText(message_frame, state=tk.DISABLED)
        self.message_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Input area
        input_frame = ttk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.input_field = ttk.Entry(input_frame)
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(input_frame, text="Send", command=self.send_message).pack(side=tk.LEFT)
        
        # Bind Enter key
        self.input_field.bind("<Return>", lambda e: self.send_message())
        
        # Add some test data
        self.add_test_data()
    
    def add_test_data(self):
        """Add test data to simulate a working environment."""
        test_peers = ["TestPeer1", "TestPeer2", "TestPeer3"]
        for peer in test_peers:
            self.peer_list.insert(tk.END, f"● {peer}")
        
        test_messages = [
            "[12:34] TestPeer1: Hello there!",
            "[12:35] TestPeer2: Hi everyone!",
            "[12:36] System: TestPeer3 joined",
            "[12:37] You: This is a test message"
        ]
        
        self.message_display.config(state=tk.NORMAL)
        for msg in test_messages:
            self.message_display.insert(tk.END, msg + "\n")
        self.message_display.config(state=tk.DISABLED)
    
    def send_message(self):
        """Test message sending."""
        text = self.input_field.get().strip()
        if text:
            timestamp = time.strftime("%H:%M")
            message = f"[{timestamp}] You: {text}\n"
            
            self.message_display.config(state=tk.NORMAL)
            self.message_display.insert(tk.END, message)
            self.message_display.config(state=tk.DISABLED)
            self.message_display.see(tk.END)
            
            self.input_field.delete(0, tk.END)
            
            print(f"Message sent: {text}")
    
    def run(self):
        """Run the test GUI."""
        print("Starting minimal GUI test...")
        print("This is a basic test of the GUI layout and functionality.")
        print("Close the window to exit.")
        
        self.root.mainloop()

if __name__ == "__main__":
    app = MinimalLaptopGUI()
    app.run()
```

### 3. Component Unit Testing

Test individual components without full integration:

#### Test GUI Components
```python
# test_gui_components.py
import unittest
import tkinter as tk
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from bitchat.gui.components.message_display import MessageDisplay
    from bitchat.gui.components.peer_list import PeerList
    from bitchat.gui.components.input_panel import InputPanel
    from bitchat.config.manager import ConfigManager
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"Components not available yet: {e}")
    COMPONENTS_AVAILABLE = False

class TestGUIComponents(unittest.TestCase):
    """Test GUI components individually."""
    
    def setUp(self):
        if not COMPONENTS_AVAILABLE:
            self.skipTest("GUI components not implemented yet")
        
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during tests
        self.config = ConfigManager()
    
    def tearDown(self):
        self.root.destroy()
    
    def test_message_display_creation(self):
        """Test message display component creation."""
        if not COMPONENTS_AVAILABLE:
            self.skipTest("MessageDisplay not implemented")
        
        display = MessageDisplay(self.root, self.config)
        self.assertIsNotNone(display.display)
        self.assertEqual(display.display['state'], tk.DISABLED)
    
    def test_peer_list_creation(self):
        """Test peer list component creation."""
        if not COMPONENTS_AVAILABLE:
            self.skipTest("PeerList not implemented")
        
        peer_list = PeerList(self.root, self.config)
        self.assertIsNotNone(peer_list.listbox)
        self.assertEqual(peer_list.listbox.size(), 0)
    
    def test_input_panel_creation(self):
        """Test input panel component creation."""
        if not COMPONENTS_AVAILABLE:
            self.skipTest("InputPanel not implemented")
        
        input_panel = InputPanel(self.root, self.config)
        self.assertIsNotNone(input_panel.input_field)
        self.assertIsNotNone(input_panel.send_callback)

if __name__ == "__main__":
    unittest.main()
```

### 4. Integration Testing with Existing BRC

Test integration with existing BRC components:

#### Test Core Integration
```python
# test_brc_integration.py
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from bitchat.config.manager import ConfigManager
    from bitchat.core.events import EventBus
    from bitchat.core.router import MessageRouter
    from bitchat.utils.logging import setup_logging, get_logger
    BRC_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"BRC components not available: {e}")
    BRC_COMPONENTS_AVAILABLE = False

class TestBRCIntegration:
    """Test integration with existing BRC components."""
    
    def __init__(self):
        if not BRC_COMPONENTS_AVAILABLE:
            print("Cannot test BRC integration - components not available")
            return
        
        setup_logging(level="INFO", console_output=True)
        self.logger = get_logger("test_integration")
        
        self.config = ConfigManager()
        self.event_bus = EventBus()
        self.message_router = MessageRouter(self.config, self.event_bus)
    
    async def test_event_system(self):
        """Test the event system."""
        print("Testing event system...")
        
        # Test event subscription
        event_received = False
        
        def test_handler(event):
            nonlocal event_received
            event_received = True
            print(f"Received event: {event.type}")
        
        self.event_bus.subscribe("test_event", test_handler)
        
        # Test event publishing
        await self.event_bus.publish({
            "type": "test_event",
            "data": {"test": "data"},
            "source": "test"
        })
        
        # Wait for event processing
        await asyncio.sleep(0.1)
        
        if event_received:
            print("✅ Event system working correctly")
        else:
            print("❌ Event system not working")
    
    async def test_message_routing(self):
        """Test message routing."""
        print("Testing message routing...")
        
        # Start message router
        await self.message_router.start()
        
        # Test message routing
        test_message = {
            "content": "Test message",
            "type": "text",
            "sender": "test_sender"
        }
        
        # Since we don't have actual transports, this will test the routing logic
        try:
            result = await self.message_router.route_message(test_message)
            print(f"Message routing result: {result}")
        except Exception as e:
            print(f"Message routing error: {e}")
        
        # Stop message router
        await self.message_router.stop()
    
    async def run_tests(self):
        """Run all integration tests."""
        print("Starting BRC integration tests...")
        
        await self.test_event_system()
        await self.test_message_routing()
        
        print("Integration tests completed.")

if __name__ == "__main__":
    if not BRC_COMPONENTS_AVAILABLE:
        print("BRC components not available. Please ensure the project is properly set up.")
        sys.exit(1)
    
    tester = TestBRCIntegration()
    asyncio.run(tester.run_tests())
```

## Step-by-Step Testing Process

### Phase 1: Environment Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio pytest-mock
   ```

2. **Verify Project Structure**
   ```bash
   # Check if all directories exist
   ls -la bitchat/gui/
   ls -la bitchat/core/
   ls -la bitchat/transports/
   ```

3. **Run Basic Tests**
   ```bash
   # Test minimal GUI
   python test_minimal_gui.py
   
   # Test component unit tests
   python -m pytest test_gui_components.py -v
   
   # Test BRC integration
   python test_brc_integration.py
   ```

### Phase 2: Component Testing

1. **Test GUI Components Individually**
   ```bash
   python -m pytest tests/unit/test_gui_components.py -v
   ```

2. **Test Bluetooth Transport**
   ```bash
   python -m pytest tests/unit/test_laptop_bluetooth.py -v
   ```

3. **Test Configuration**
   ```bash
   python -m pytest tests/unit/test_laptop_config.py -v
   ```

### Phase 3: Integration Testing

1. **Mock Integration Tests**
   ```bash
   python test_mock_gui.py
   ```

2. **End-to-End Tests**
   ```bash
   python -m pytest tests/e2e/ -v
   ```

3. **Performance Tests**
   ```bash
   python -m pytest tests/performance/ -v
   ```

### Phase 4: Platform-Specific Testing

#### Windows Testing
```batch
REM Test on Windows
python test_minimal_gui.py
python -m pytest tests/ -v
python scripts/build_laptop_client.py
```

#### macOS Testing
```bash
# Test on macOS
python3 test_minimal_gui.py
python3 -m pytest tests/ -v
python3 scripts/build_laptop_client.py
```

#### Linux Testing
```bash
# Test on Linux
python3 test_minimal_gui.py
python3 -m pytest tests/ -v
python3 scripts/build_laptop_client.py

# Test Bluetooth functionality
sudo hciconfig  # Check Bluetooth adapter
python3 -c "import bleak; print('Bleak available')"
```

## Expected Test Results

### Successful Tests Should Show:

1. **GUI Window Opens**: Tkinter window appears without errors
2. **Components Render**: All UI elements are visible and functional
3. **Message Display**: Messages appear correctly formatted
4. **Peer List**: Peer list shows connected devices
5. **Input Functionality**: Text input and message sending works
6. **Event System**: Events are published and received correctly
7. **Configuration**: Settings load and save properly

### Common Issues and Solutions:

#### Import Errors
```bash
# If you get import errors, check:
python -c "import sys; print(sys.path)"
python -c "import bitchat; print('BRC imported successfully')"
```

#### GUI Issues
```bash
# If GUI doesn't appear:
python -c "import tkinter; print('Tkinter working')"
python -c "import tkinter as tk; root = tk.Tk(); print('GUI test passed')"
```

#### Bluetooth Issues
```bash
# Check Bluetooth availability:
python -c "import bleak; print('Bleak available')"
python -c "import platform; print(f'Platform: {platform.system()}')"
```

## Continuous Testing

### Automated Test Runner
```bash
# Run all tests automatically
python scripts/run_tests.py --all

# Run specific test suites
python scripts/run_tests.py unit
python scripts/run_tests.py integration
python scripts/run_tests.py e2e
```

### Test Coverage
```bash
# Generate coverage report
python -m pytest tests/ --cov=bitchat --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Next Steps After Testing

### If Tests Pass:
1. **Implement Missing Components**: Build the actual components based on working tests
2. **Add Real Bluetooth**: Replace mocks with actual Bluetooth implementation
3. **Integration Testing**: Test with real BRC devices
4. **Platform Testing**: Test on actual Windows, macOS, and Linux systems

### If Tests Fail:
1. **Debug Issues**: Use test output to identify problems
2. **Fix Dependencies**: Ensure all required packages are installed
3. **Check Environment**: Verify Python version and system compatibility
4. **Update Tests**: Fix test issues and re-run

This testing guide provides a comprehensive approach to validate the laptop client implementation before full deployment. Start with mock testing to verify concepts, then move to integration testing with real components.