"""
Speech-to-Text Module
Handles offline transcription of WAV audio files to text using Vosk.
Responsible ONLY for transcription and text cleaning.
"""

import os
import json
import wave
import logging
from typing import Optional
from vosk import Model, KaldiRecognizer

# Configure logging
logger = logging.getLogger(__name__)

class SpeechToText:
    """
    Offline Speech-to-Text engine using Vosk.
    """
    
    # Common English filler words to remove
    FILLER_WORDS = {
        "um", "uh", "err", "ah", "like", "you know", "hmmm", "well"
    }

    def __init__(self, model_path: str = "models/vosk"):
        """
        Initialize the STT engine.
        
        Args:
            model_path (str): Path to the Vosk model directory.
        """
        self.model_path = model_path
        self.model = None
        
        # Check if model exists
        if not os.path.exists(self.model_path):
            logger.error(f"Vosk model not found at {self.model_path}. Please download a model from https://alphacephei.com/vosk/models")
            return

        try:
            logger.info(f"Loading Vosk model from {self.model_path}...")
            self.model = Model(self.model_path)
            logger.info("Vosk model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {e}")

    def transcribe_wav(self, file_path: str) -> Optional[str]:
        """
        Transcribe a WAV file to text.
        
        Args:
            file_path (str): Path to the WAV file.
            
        Returns:
            str: Transcribed and cleaned text, or None if failed.
        """
        if not self.model:
            logger.error("STT model is not initialized.")
            return None

        if not os.path.exists(file_path):
            logger.error(f"WAV file not found: {file_path}")
            return None

        try:
            wf = wave.open(file_path, "rb")
            
            # Basic validation of the WAV file
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                logger.warning("Audio file must be WAV format mono PCM. Attempting transcription anyway...")

            rec = KaldiRecognizer(self.model, wf.getframerate())
            rec.SetWords(True)
            
            # Read and process the audio in chunks
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                rec.AcceptWaveform(data)

            # Get the final result
            result_json = rec.FinalResult()
            result_dict = json.loads(result_json)
            
            raw_text = result_dict.get("text", "")
            cleaned_text = self._clean_text(raw_text)
            
            wf.close()
            
            if cleaned_text:
                logger.info(f"Transcription successful: '{cleaned_text}'")
                return cleaned_text
            else:
                logger.info("Transcription returned empty result.")
                return ""

        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return None

    def _clean_text(self, text: str) -> str:
        """
        Clean the transcription: lowercase and remove filler words.
        """
        # Convert to lowercase
        text = text.lower().strip()
        
        # Split into words
        words = text.split()
        
        # Filter out filler words
        cleaned_words = [word for word in words if word not in self.FILLER_WORDS]
        
        return " ".join(cleaned_words)

if __name__ == "__main__":
    # Example usage / testing stub
    logging.basicConfig(level=logging.INFO)
    stt = SpeechToText()
    
    # In a real test, you'd provide a path to an actual WAV file
    test_file = "output.wav"
    if os.path.exists(test_file):
        text = stt.transcribe_wav(test_file)
        print(f"Result: {text}")
    else:
        print(f"No test file found at {test_file}. Record one using audio_listener.py first.")
