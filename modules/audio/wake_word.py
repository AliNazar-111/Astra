"""
Wake Word Detection Module
Handles continuous listening for the wake word "Astra".
Supports Porcupine (primary) and Push-to-Talk (fallback).
"""

import os
import time
import struct
import logging
import threading
from typing import Optional, Callable
import pvporcupine
import pyaudio
import keyboard  # For push-to-talk fallback

# Configure logging
logger = logging.getLogger(__name__)

class WakeWordDetector:
    def __init__(self, 
                 access_key: Optional[str] = None,
                 keywords: list = ["porcupine"], # Default to porcupine if "astra" not available
                 sensitivities: list = [0.5],
                 input_device_index: Optional[int] = None):
        """
        Initialize wake word detector.
        
        Args:
            access_key (str): Picovoice AccessKey (env: PICOVOICE_ACCESS_KEY)
            keywords (list): List of keywords to detect (e.g. ['astra'])
            sensitivities (list): Sensitivity for each keyword (0.0 to 1.0)
            input_device_index (int): Audio input device index
        """
        self.access_key = access_key or os.getenv("PICOVOICE_ACCESS_KEY")
        self.keywords = keywords
        self.sensitivities = sensitivities
        self.input_device_index = input_device_index
        
        self.porcupine = None
        self.pa = None
        self.audio_stream = None
        
        self.is_listening = False
        self._stop_event = threading.Event()
        self.last_detection_time = 0
        self.debounce_seconds = 1.0
        
        # Initialize engine
        self._init_porcupine()

    def _init_porcupine(self):
        """Initialize Porcupine engine."""
        if not self.access_key:
            logger.warning("No Picovoice AccessKey found. Wake word detection disabled. Using PTT only.")
            return

        try:
            # Try to load custom keyword path if it's a file, otherwise use default keywords
            keyword_paths = [k for k in self.keywords if k.endswith('.ppn')]
            builtin_keywords = [k for k in self.keywords if not k.endswith('.ppn')]
            
            # If "astra" is requested but no file provided, fall back to "porcupine" for testing
            # Real usage requires a custom .ppn file for "Astra"
            if not keyword_paths and not builtin_keywords:
                builtin_keywords = ["porcupine"]

            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=builtin_keywords if builtin_keywords else None,
                keyword_paths=keyword_paths if keyword_paths else None,
                sensitivities=self.sensitivities
            )
            logger.info(f"Porcupine initialized. Keywords: {self.keywords}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Porcupine: {e}")
            self.porcupine = None

    def start_listening(self, on_wake: Callable[[], None]):
        """
        Start the wake word loop. Blocking call (run in thread if needed).
        
        Args:
            on_wake (func): Callback function trigger when wake word detected
        """
        self.is_listening = True
        self._stop_event.clear()
        
        # Start PTT listener in background
        threading.Thread(target=self._ptt_loop, args=(on_wake,), daemon=True).start()
        
        if not self.porcupine:
            logger.info("Wake word engine not active. interactive mode via PTT only.")
            # Keep main thread alive if just PTT
            while self.is_listening and not self._stop_event.is_set():
                time.sleep(0.1)
            return

        # Audio stream setup
        try:
            self.pa = pyaudio.PyAudio()
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length,
                input_device_index=self.input_device_index
            )
            
            logger.info("Listening for wake word...")
            
            while self.is_listening and not self._stop_event.is_set():
                pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                
                keyword_index = self.porcupine.process(pcm)
                
                if keyword_index >= 0:
                    current_time = time.time()
                    if current_time - self.last_detection_time > self.debounce_seconds:
                        logger.info(f"Wake word detected! (Index: {keyword_index})")
                        self.last_detection_time = current_time
                        
                        # Trigger callback
                        on_wake()
                        
                        # Optional: Pause listening briefly during active processing?
                        # Usually the orchestrator handles stopping this loop.
                        
        except Exception as e:
            logger.error(f"Error in wake word loop: {e}")
        finally:
            self.stop()

    def _ptt_loop(self, on_wake):
        """Push-to-talk handler using keyboard hook."""
        # Clean debounce for PTT
        last_press = 0
        
        while self.is_listening and not self._stop_event.is_set():
             # Example: Check for 'ctrl+alt+a'
            if keyboard.is_pressed('ctrl+alt+a'):
                current_time = time.time()
                if current_time - last_press > 1.0: # 1 sec debounce
                    logger.info("Push-to-talk triggered.")
                    last_press = current_time
                    on_wake()
            time.sleep(0.05)

    def stop(self):
        """Stop listening and cleanup."""
        self.is_listening = False
        self._stop_event.set()
        
        if self.audio_stream:
            try:
                self.audio_stream.close()
            except: pass
            self.audio_stream = None
            
        if self.pa:
            try:
                self.pa.terminate()
            except: pass
            self.pa = None
            
        if self.porcupine:
            try:
                self.porcupine.delete()
            except: pass
            self.porcupine = None
            
        logger.info("Wake word detector stopped.")

if __name__ == "__main__":
    # Test stub
    logging.basicConfig(level=logging.INFO)
    
    def wake_callback():
        print(">>> WAKE WORD TRIGGERED! <<<")
        # Simulate active listening
        time.sleep(1)
        
    detector = WakeWordDetector()
    try:
        print("Press Ctrl+C to exit. (Or triggers wake word if key set)")
        print("Fallback PTT: Ctrl+Alt+A")
        detector.start_listening(wake_callback)
    except KeyboardInterrupt:
        detector.stop()
