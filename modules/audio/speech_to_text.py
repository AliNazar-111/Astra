"""
Speech-to-Text Module (Hardened)
Transcribes audio using Vosk (offline).
Ensures model availability and robust file processing.
"""

import os
import json
import logging
import wave
from vosk import Model, KaldiRecognizer
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

class SpeechToText:
    """
    Offline STT engine using Vosk.
    Hardened to handle missing models and corrupt audio gracefully.
    """

    def __init__(self, model_path: str = "models/vosk"):
        self.model_path = os.path.abspath(model_path)
        self.model = None
        self._load_model()

    def _load_model(self) -> bool:
        """Verifies and loads the Vosk model."""
        if not os.path.exists(self.model_path):
            logger.error(f"Vosk model not found at: {self.model_path}")
            return False
            
        try:
            logger.info(f"Loading Vosk model from {self.model_path}...")
            self.model = Model(self.model_path)
            return True
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {e}")
            return False

    def transcribe_wav(self, wav_path: str) -> str:
        """
        Transcribes a WAV file into text.
        """
        if not self.model and not self._load_model():
            logger.error("STT model could not be loaded. Transcription aborted.")
            return ""

        if not os.path.exists(wav_path):
            logger.error(f"Audio file not found for transcription: {wav_path}")
            return ""

        wf = None
        try:
            wf = wave.open(wav_path, "rb")
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                logger.error("Audio file must be WAV format mono PCM (16kHz recommended).")
                return ""

            rec = KaldiRecognizer(self.model, wf.getframerate())
            rec.SetWords(True)

            results = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    if res.get("text"):
                        results.append(res["text"])

            final_res = json.loads(rec.FinalResult())
            if final_res.get("text"):
                results.append(final_res["text"])

            transcription = " ".join(results).strip().lower()
            logger.info(f"Transcription complete: '{transcription}'")
            return transcription

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
        finally:
            if wf:
                try:
                    wf.close()
                except:
                    pass

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    stt = SpeechToText()
    text = stt.transcribe_wav("data/cache/last_command.wav")
    print(f"Result: {text}")
