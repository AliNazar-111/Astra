"""
Audio Listener Module
Handles raw microphone input, silence detection, and WAV file saving.
Responsible ONLY for audio capture.
"""

import os
import wave
import time
import math
import struct
import threading
import logging
from typing import Optional, List
import pyaudio

# Configure logging
logger = logging.getLogger(__name__)

class AudioListener:
    def __init__(self, 
                 sample_rate: int = 16000, 
                 channels: int = 1, 
                 chunk_size: int = 4000,
                 silence_threshold: int = 500,
                 silence_duration: float = 2.0):
        """
        Initialize the audio listener.
        
        Args:
            sample_rate (int): Audio sample rate (default 16000Hz)
            channels (int): Number of audio channels (default 1)
            chunk_size (int): Buffer size for reading audio
            silence_threshold (int): RMS amplitude threshold for silence
            silence_duration (float): Seconds of silence to trigger stop
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        
        self.format = pyaudio.paInt16
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self._stop_event = threading.Event()
        self._frames: List[bytes] = []

    def _calculate_rms(self, audio_data: bytes) -> float:
        """Calculate Root Mean Square (RMS) amplitude of audio chunk."""
        count = len(audio_data) // 2
        if count == 0:
            return 0
            
        format = "<{}h".format(count)
        shorts = struct.unpack(format, audio_data)
        sum_squares = sum(s * s for s in shorts)
        return math.sqrt(sum_squares / count)

    def start_recording(self, max_duration: int = 10) -> None:
        """
        Start recording audio processing.
        background-safe: runs in the caller's thread (blocking) or can be threaded.
        For non-blocking, wrap this in a thread.
        
        Args:
            max_duration (int): Maximum recording duration in seconds
        """
        try:
            self.stream = self.p.open(format=self.format,
                                      channels=self.channels,
                                      rate=self.sample_rate,
                                      input=True,
                                      frames_per_buffer=self.chunk_size)
            
            logger.info("Recording started...")
            self.is_recording = True
            self._frames = []
            self._stop_event.clear()
            
            start_time = time.time()
            silence_start_time = None
            
            while self.is_recording and not self._stop_event.is_set():
                # Check max duration
                if time.time() - start_time > max_duration:
                    logger.info("Max duration reached.")
                    break
                    
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                self._frames.append(data)
                
                # Silence detection
                rms = self._calculate_rms(data)
                if rms < self.silence_threshold:
                    if silence_start_time is None:
                        silence_start_time = time.time()
                    elif time.time() - silence_start_time >= self.silence_duration:
                        logger.info("Silence detected, stopping recording.")
                        break
                else:
                    silence_start_time = None
                    
        except Exception as e:
            logger.error(f"Error during recording: {e}")
            raise
        finally:
            self.stop_recording()

    def stop_recording(self) -> None:
        """Stop the recording and clean up stream."""
        self.is_recording = False
        self._stop_event.set()
        
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error closing stream: {e}")
            self.stream = None
        
        logger.info("Recording stopped.")

    def save_recording(self, filename: str) -> Optional[str]:
        """
        Save recorded frames to a WAV file.
        
        Args:
            filename (str): Path to save the WAV file
            
        Returns:
            str: Absolute path to saved file, or None if failed
        """
        if not self._frames:
            logger.warning("No audio data to save.")
            return None
            
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            wf = wave.open(filename, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self._frames))
            wf.close()
            
            logger.info(f"Audio saved to {filename}")
            return os.path.abspath(filename)
            
        except Exception as e:
            logger.error(f"Error saving WAV file: {e}")
            return None

    def __del__(self):
        """Cleanup PyAudio instance."""
        if self.p:
            self.p.terminate()

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    listener = AudioListener()
    try:
        print("Recording for 5 seconds (or until silence)...")
        listener.start_recording(max_duration=5)
        listener.save_recording("output.wav")
    except KeyboardInterrupt:
        listener.stop_recording()
