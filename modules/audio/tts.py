"""
Text-to-Speech Module (Hardened)
Handles offline voice synthesis for Astra.
Ensures non-blocking audio output and initialization safety.
"""

import pyttsx3
import logging
import threading
import queue
import time
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

class TTS:
    """
    Offline Text-to-Speech engine.
    Managed with a background thread queue to prevent UI/Execution freezes.
    """

    def __init__(self, rate: int = 180, volume: float = 1.0, voice_index: int = 0):
        self.rate = rate
        self.volume = volume
        self.voice_index = voice_index
        
        self.speech_queue = queue.Queue()
        self._stop_event = threading.Event()
        
        # Start background worker for speech
        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()
        logger.info("TTS background worker started.")

    def _speech_worker(self):
        """Processes the speech queue in a separate thread to avoid blocking."""
        engine = None
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', self.rate)
            engine.setProperty('volume', self.volume)
            
            voices = engine.getProperty('voices')
            if voices:
                idx = min(self.voice_index, len(voices) - 1)
                engine.setProperty('voice', voices[idx].id)
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            return

        while not self._stop_event.is_set():
            try:
                # Wait for text to speak (with timeout to check stop_event)
                text = self.speech_queue.get(timeout=1.0)
                if text:
                    logger.debug(f"Synthesizing speech: '{text}'")
                    engine.say(text)
                    engine.runAndWait()
                self.speech_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"TTS Worker Error during synthesis: {e}")
                # Try to re-init engine if it crashes
                try:
                    engine = pyttsx3.init()
                except:
                    pass

    def speak(self, text: str, block: bool = False):
        """ 
        Adds text to the speech queue. 
        Args:
            text (str): Message to speak.
            block (bool): If True, waits for text to be processed (not recommended for main loop).
        """
        if not text:
            return

        self.speech_queue.put(text)
        
        if block:
            self.speech_queue.join()

    def stop(self):
        """Stops the worker thread."""
        self._stop_event.set()
        logger.info("TTS worker thread signaled to stop.")

    def set_rate(self, rate: int):
        self.rate = rate # Note: Changes will apply to next engine re-init or 
                         # we could add a dynamic parameter check in worker
        logger.info(f"TTS target rate: {rate}")

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))
        logger.info(f"TTS target volume: {self.volume}")

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    tts = TTS()
    tts.speak("Hardening test one.", block=True)
    tts.speak("Hardening test two, non-blocking.")
    print("This line prints immediately while Astra speaks test two.")
    time.sleep(3)
    tts.stop()


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
