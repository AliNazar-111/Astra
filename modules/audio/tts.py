"""
Text-to-Speech Module
Handles offline voice synthesis for Astra.
Uses pyttsx3 for deterministic, queue-safe audio output.
"""

import pyttsx3
import logging
import threading
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

class TTS:
    """
    Offline Text-to-Speech engine.
    Managed as a singleton or with a shared queue to ensure sequential speaking.
    """

    def __init__(self, rate: int = 180, volume: float = 1.0, voice_index: int = 0):
        """
        Initialize the TTS engine.
        
        Args:
            rate (int): Words per minute.
            volume (float): Volume level (0.0 to 1.0).
            voice_index (int): Index of the installed voice to use.
        """
        self.engine = pyttsx3.init()
        self.rate = rate
        self.volume = volume
        self.voice_index = voice_index
        
        # Configure initial settings
        self.engine.setProperty('rate', self.rate)
        self.engine.setProperty('volume', self.volume)
        
        # Set voice
        voices = self.engine.getProperty('voices')
        if voices:
            # Safely select voice
            idx = min(self.voice_index, len(voices) - 1)
            self.engine.setProperty('voice', voices[idx].id)
            logger.info(f"TTS initialized with voice: {voices[idx].name}")

        self._lock = threading.Lock()

    def speak(self, text: str, block: bool = True):
        """
        Synthesizes speech from text.
        
        Args:
            text (str): The text to speak.
            block (bool): Whether to wait for speaking to finish.
        """
        if not text:
            return

        logger.info(f"Speaking: '{text}'")
        
        # Use a lock to ensure thread-safely speaking one message at a time
        def _perform_speak():
            with self._lock:
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    logger.error(f"TTS Error: {e}")

        if block:
            _perform_speak()
        else:
            threading.Thread(target=_perform_speak, daemon=True).start()

    def set_rate(self, rate: int):
        """Adjusts the speaking speed (WPM)."""
        self.rate = rate
        self.engine.setProperty('rate', self.rate)
        logger.info(f"TTS rate set to: {rate}")

    def set_volume(self, volume: float):
        """Adjusts the volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        self.engine.setProperty('volume', self.volume)
        logger.info(f"TTS volume set to: {self.volume}")

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    tts = TTS()
    
    print("Testing TTS with different rates...")
    tts.speak("Hello, I am Astra. My system is fully operational.")
    
    tts.set_rate(120)
    tts.speak("I can speak slower if you want.")
    
    tts.set_rate(220)
    tts.speak("Or very fast if we are in a hurry!")
