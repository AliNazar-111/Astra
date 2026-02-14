"""
Wake Word Detector Module (Hardened)
Listens for the specific phrase "Astra" to trigger the assistant.
Ensures low CPU usage and reliable detection loop.
"""

import logging
import time
import threading
from typing import Callable, Optional

# Configure logging
logger = logging.getLogger(__name__)

class WakeWordDetector:
    """
    Simulated Wake Word Detector for Astra.
    Hardened to ensure it responds to stop signals and stays efficient.
    """

    def __init__(self, wake_word: str = "Astra"):
        self.wake_word = wake_word
        self.is_listening = False
        self._stop_event = threading.Event()

    def start_listening(self, on_wake: Callable):
        """
        Starts the detection loop.
        
        Args:
            on_wake (Callable): Function to call when wake word is detected.
        """
        self.is_listening = True
        self._stop_event.clear()
        logger.info(f"Wake word detector started for: '{self.wake_word}'")
        
        try:
            while not self._stop_event.is_set():
                # Simulation: To keep CPU low, we sleep
                time.sleep(0.5) 
                
                # In a real implementation, we would check the mic stream here.
                # For this hardened shell, we just maintain the loop logic.
                
        except Exception as e:
            logger.error(f"Wake Word Loop Error: {e}")
        finally:
            self.stop()

    def stop(self):
        """Safely stops the detector."""
        self._stop_event.set()
        self.is_listening = False
        logger.info("Wake word detector stopped.")

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    detector = WakeWordDetector()
    
    def test_callback():
        print("WAKE DETECTED!")
        
    print("Detector running... (Ctrl+C to stop)")
    try:
        # Start in a thread for testing
        t = threading.Thread(target=detector.start_listening, args=(test_callback,), daemon=True)
        t.start()
        time.sleep(2)
        detector.stop()
    except KeyboardInterrupt:
        detector.stop()
