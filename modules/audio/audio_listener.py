"""
Audio Listener Module (Hardened)
Handles raw microphone input and recording.
Ensures device availability checks and robust stream management.
"""

import pyaudio
import wave
import logging
import os
import time
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

class AudioListener:
    """
    Handles capturing audio from the default input device.
    Includes safeguards for device disconnection and buffer stability.
    """

    def __init__(self, format=pyaudio.paInt16, channels=1, rate=16000, chunk=1024):
        self.format = format
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.frames = []
        self._pa = None
        self._stream = None

    def _init_pyaudio(self) -> bool:
        """Initializes PyAudio only when needed."""
        try:
            if not self._pa:
                self._pa = pyaudio.PyAudio()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize PyAudio: {e}")
            return False

    def start_recording(self, max_duration: int = 5) -> bool:
        """
        Record audio for a fixed duration with safety checks.
        """
        if not self._init_pyaudio():
            return False

        logger.info(f"Starting recording (max {max_duration}s)...")
        self.frames = []
        
        try:
            self._stream = self._pa.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            # Calculate number of chunks
            num_chunks = int(self.rate / self.chunk * max_duration)
            
            for _ in range(num_chunks):
                if not self._stream or not self._stream.is_active():
                    break
                try:
                    data = self._stream.read(self.chunk, exception_on_overflow=False)
                    self.frames.append(data)
                except Exception as e:
                    logger.warning(f"Audio read glitch: {e}")
                    break
                
            self._stop_stream()
            logger.info("Recording finished.")
            return True

        except Exception as e:
            logger.error(f"Error during audio recording: {e}")
            self._stop_stream()
            return False

    def _stop_stream(self):
        """Internal helper to clean up stream."""
        try:
            if self._stream:
                try:
                    self._stream.stop_stream()
                    self._stream.close()
                except:
                    pass
            self._stream = None
        except Exception as e:
            logger.debug(f"Cleanup error: {e}")

    def save_recording(self, filename: str):
        """Saves captured frames to a WAV file."""
        if not self.frames:
            logger.warning("No frames to save.")
            return

        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                # Ensure _pa exists before calling get_sample_size
                if not self._pa:
                    self._init_pyaudio()
                wf.setsampwidth(self._pa.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(self.frames))
            logger.info(f"Audio saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save recording: {e}")

    def cleanup(self):
        """Final cleanup of PyAudio resources."""
        self._stop_stream()
        if self._pa:
            try:
                self._pa.terminate()
            except:
                pass
            self._pa = None
        logger.info("AudioListener resources cleaned up.")

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    listener = AudioListener()
    try:
        if listener.start_recording(max_duration=3):
            listener.save_recording("data/cache/test_hardened.wav")
    finally:
        listener.cleanup()
