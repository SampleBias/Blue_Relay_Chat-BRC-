#!/usr/bin/env python3
"""
Visual demonstration of small screen GUI.

This script provides a visual representation of what the
small screen GUI would look like on a 1.44-inch display.
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from bitchat.gui.small_screen_gui import SmallScreenGUI
    from bitchat.config.manager import ConfigManager
    from bitchat.core.events import EventBus
    from bitchat.utils.logging import setup_logging, get_logger
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system('clear' if os.name == 'posix' else 'cls')


def draw_border(width: int, height: int) -> None:
    """Draw a border around the screen."""
    print("+" + "-" * (width - 2) + "+")
    for i in range(height - 2):
        print("|" + " " * (width - 2) + "|")
    print("+" + "-" * (width - 2) + "+")


def draw_status_bar(width: int) -> None:
    """Draw the status bar."""
    print("| Channel: mesh #local P:2 M:offline N:offline |")
    print("+" + "-" * (width - 2) + "+")


def draw_chat_content(width: int, height: int) -> None:
    """Draw the chat content area."""
    content_height = height - 2  # Leave room for status and input
    
    # Sample messages
    messages = [
        ("09:15 >: Hello world", "sent"),
        ("09:18 <user1>: Hi there!", "received"),
        ("09:20 user1>: How are you?", "sent"),
        ("09:22 <user2>: I'm good, thanks!", "received"),
    ]
    
    for i, (msg, msg_type) in enumerate(messages[-content_height:]):
        if i >= content_height:
            break
            
        prefix = ">" if msg_type == "sent" else "<"
        sender = msg.split(":")[0] if msg_type == "received" else ""
        content = msg.split(":")[1] if ":" in msg else msg
        
        # Truncate content if too long
        max_content_len = width - 20  # Account for timestamp and prefix
        if len(content) > max_content_len:
            content = content[:max_content_len-2] + ".."
        
        print(f"| {sender} {prefix} {content}" + " " * (width - len(f"{sender} {prefix} {content}") - 3) + "|")
    
    # Fill remaining space
    for i in range(len(messages), content_height):
        print("|" + " " * (width - 2) + "|")


def draw_input_area(width: int) -> None:
    """Draw the input area."""
    print("| NAV MODE | SELECT: Text Input |")
    print("+" + "-" * (width - 2) + "+")


def draw_menu_screen(width: int, height: int) -> None:
    """Draw the menu screen."""
    menu_options = [
        "Send Message",
        "View Status",
        "Change Channel",
        "Settings",
        "Exit",
    ]
    
    # Title
    title = "Blue Relay Chat"
    title_padding = (width - len(title)) // 2
    print("|" + " " * title_padding + title + " " * title_padding + "|")
    print("+" + "-" * (width - 2) + "+")
    
    # Menu options
    for i, option in enumerate(menu_options):
        prefix = "> " if i == 0 else " "
        print(f"| {prefix} {option}" + " " * (width - len(f"{prefix} {option}") - 3) + "|")
    
    # Fill remaining space
    for i in range(len(menu_options), height - 3 - len(menu_options)):
        print("|" + " " * (width - 2) + "|")
    
    print("+" + "-" * (width - 2) + "+")


def draw_status_screen(width: int, height: int) -> None:
    """Draw the status screen."""
    # Title
    title = "System Status"
    title_padding = (width - len(title)) // 2
    print("|" + " " * title_padding + title + " " * title_padding + "|")
    print("+" + "-" * (width - 2) + "+")
    
    # Status pages
    status_pages = [
        ("Peers & Transport", [
            "Connected Peers: 2",
            "Mesh Status: online",
            "Nostr Status: offline",
        ]),
        ("Network Info", [
            "Current Channel: mesh #local",
            "Max Peers: 8",
            "Max Relays: 1",
        ]),
        ("System Info", [
            "Hardware: RPi Zero 2W",
            "Memory: 512MB",
            "CPU: 4 cores",
        ]),
        ("Battery & Signal", [
            "Battery: 85%",
            "Signal: ████░░",
        ]),
    ]
    
    for i, (page_name, items) in enumerate(status_pages):
        if i >= height - 3:
            break
            
        # Page title
        print(f"| {page_name}" + " " * (width - len(page_name) - 3) + "|")
        print("+" + "-" * (width - 2) + "+")
        
        # Page items
        for item in items:
            print(f"| {item}" + " " * (width - len(item) - 3) + "|")
        
        print("+" + "-" * (width - 2) + "+")


def draw_text_input_screen(width: int, height: int) -> None:
    """Draw the text input screen."""
    # Title
    title = "Text Input"
    title_padding = (width - len(title)) // 2
    print("|" + " " * title_padding + title + " " * title_padding + "|")
    print("+" + "-" * (width - 2) + "+")
    
    # Character grid (simplified for demo)
    char_grid = [
        "A B C D E F",
        "G H I J K L",
        "M N O P Q R",
        "S T U V W X",
        "Y Z 0 1 2 3",
        "4 5 6 7 8 9",
        "  , . ? ! @",
    ]
    
    # Current input
    current_input = "HELLO WORLD"
    
    # Draw character grid
    for row in char_grid:
        print(f"| {row}" + " " * (width - len(row) - 3) + "|")
    
    print("+" + "-" * (width - 2) + "+")
    
    # Current input
    print(f"| Input: {current_input}")
    print("+" + "-" * (width - 2) + "+")


def simulate_navigation(current_mode: str, width: int, height: int) -> str:
    """Simulate navigation between modes."""
    modes = ["chat", "menu", "status", "text_input"]
    
    # Find current mode index
    try:
        current_index = modes.index(current_mode)
    except ValueError:
        current_index = 0
    
    # Wait for user input
    print(f"\nCurrent mode: {current_mode}")
    print("Navigation: [n]ext, [p]rev, [q]uit, [s]witch mode")
    
    while True:
        try:
            choice = input("> ").lower()
            
            if choice in ['n', '']:
                # Next mode
                current_index = (current_index + 1) % len(modes)
            elif choice == 'p':
                # Previous mode
                current_index = (current_index - 1) % len(modes)
            elif choice == 'q':
                # Quit
                return "quit"
            elif choice == 's':
                # Switch mode
                print("Available modes:")
                for i, mode in enumerate(modes):
                    print(f"  {i}: {mode}")
                
                while True:
                    try:
                        choice = input(f"Select mode [{current_index}]: ").strip()
                        if choice.isdigit():
                            choice_index = int(choice)
                            if 0 <= choice_index < len(modes):
                                current_index = choice_index
                                break
                    except ValueError:
                        if choice in modes:
                            current_index = modes.index(choice)
                            break
                current_mode = modes[current_index]
            else:
                print(f"Unknown choice: {choice}")
            
            if current_mode != "quit":
                return current_mode
                
        except KeyboardInterrupt:
            return "quit"


def main() -> None:
    """Main demonstration function."""
    # Set up logging
    setup_logging(
        level="INFO",
        log_file=None,
        console_output=True
    )
    
    logger = get_logger("demo")
    logger.info("Starting small screen GUI demonstration...")
    
    # Screen dimensions
    width = 80  # Terminal width
    height = 24  # Terminal height
    
    current_mode = "chat"
    
    while current_mode != "quit":
        clear_screen()
        draw_border(width, height)
        
        if current_mode == "chat":
            draw_status_bar(width)
            draw_chat_content(width, height)
            draw_input_area(width)
        elif current_mode == "menu":
            draw_menu_screen(width, height)
        elif current_mode == "status":
            draw_status_screen(width, height)
        elif current_mode == "text_input":
            draw_text_input_screen(width, height)
        
        # Simulate navigation
        current_mode = simulate_navigation(current_mode, width, height)
    
    print("\nThank you for trying the small screen GUI demonstration!")
    print("To run the actual GUI:")
    print("  python3 -m bitchat.gui.small_screen_gui")
    print("\nTo run with mock display:")
    print("  export BITCHAT_MOCK_DISPLAY=true")
    print("  python3 -m bitchat.gui.small_screen_gui")


if __name__ == "__main__":
    main()