"""
System Actions Module
Handles low-level OS automation for Windows:
- Application life-cycle (Open/Close)
- Window management (Switching)
- Input simulation (Keyboard/Mouse)
- System controls (Volume)
"""

import os
import subprocess
import logging
import pyautogui
import pywinauto
import time
from typing import Optional

# Configure PyAutoGUI safety
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.5      # Small delay between actions

logger = logging.getLogger(__name__)

class SystemActions:
    """
    Deterministic automation handlers for Windows.
    No AI logic - just direct execution.
    """

    def open_app(self, app_name: str) -> bool:
        """
        Launches an application by name or common path.
        """
        logger.info(f"Attempting to open: {app_name}")
        try:
            # Try to start file directly (works for many apps in PATH or registered)
            os.startfile(app_name)
            return True
        except Exception as e:
            logger.error(f"Failed to open {app_name} via startfile: {e}")
            # Fallback for common aliases
            aliases = {
                "chrome": "chrome.exe",
                "notepad": "notepad.exe",
                "calculator": "calc.exe",
                "edge": "msedge.exe"
            }
            target = aliases.get(app_name.lower(), app_name)
            try:
                subprocess.Popen(target, shell=True)
                return True
            except Exception as e2:
                logger.error(f"Fallback launch failed for {target}: {e2}")
                return False

    def close_app(self, app_name: str) -> bool:
        """
        Closes an application using taskkill.
        """
        logger.info(f"Attempting to close: {app_name}")
        try:
            # Force close the process by name
            # Note: app_name should be the process name (e.g., 'notepad.exe')
            if not app_name.endswith(".exe"):
                app_name += ".exe"
            subprocess.run(["taskkill", "/F", "/IM", app_name], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            logger.warning(f"Process {app_name} not found or could not be killed.")
            return False
        except Exception as e:
            logger.error(f"Error closing app {app_name}: {e}")
            return False

    def switch_window(self, title_query: str) -> bool:
        """
        Switches focus to a window containing the title_query.
        """
        logger.info(f"Switching to window: {title_query}")
        try:
            app = pywinauto.Desktop(backend="win32").window(title_re=f".*{title_query}.*", found_index=0)
            if app.exists():
                app.set_focus()
                return True
            return False
        except Exception as e:
            logger.error(f"Error switching to window '{title_query}': {e}")
            return False

    def control_volume(self, action: str, amount: int = 1) -> bool:
        """
        Controls system volume.
        action: 'up', 'down', 'mute'
        """
        logger.info(f"Volume control: {action}")
        try:
            if action == "up":
                for _ in range(amount):
                    pyautogui.press("volumeup")
            elif action == "down":
                for _ in range(amount):
                    pyautogui.press("volumedown")
            elif action == "mute":
                pyautogui.press("volumemute")
            return True
        except Exception as e:
            logger.error(f"Volume control failed: {e}")
            return False

    def press_shortcut(self, keys: list) -> bool:
        """
        Executes a keyboard shortcut (e.g., ['ctrl', 'c']).
        """
        logger.info(f"Executing shortcut: {keys}")
        try:
            pyautogui.hotkey(*keys)
            return True
        except Exception as e:
            logger.error(f"Shortcut failed: {e}")
            return False

    def type_text(self, text: str) -> bool:
        """
        Types text progressively.
        """
        logger.info(f"Typing text: {text[:20]}...")
        try:
            pyautogui.write(text, interval=0.01)
            return True
        except Exception as e:
            logger.error(f"Typing failed: {e}")
            return False

    def mouse_move_and_click(self, x: Optional[int] = None, y: Optional[int] = None, click: bool = True) -> bool:
        """
        Moves mouse to coordinates and optionally clicks.
        If x, y are None, it clicks at current position.
        """
        logger.info(f"Mouse action: move to ({x}, {y}), click={click}")
        try:
            if x is not None and y is not None:
                pyautogui.moveTo(x, y, duration=0.2)
            if click:
                pyautogui.click()
            return True
        except Exception as e:
            logger.error(f"Mouse action failed: {e}")
            return False

if __name__ == "__main__":
    # Test script (Run with caution!)
    logging.basicConfig(level=logging.INFO)
    actions = SystemActions()
    
    print("Test: Opening Notepad...")
    if actions.open_app("notepad"):
        time.sleep(1)
        print("Test: Typing message...")
        actions.type_text("Astra is alive!")
        time.sleep(1)
        print("Test: Volume Up...")
        actions.control_volume("up", 2)
    else:
        print("Test failed: Could not open notepad.")
