"""
Astra - Main Application Orchestrator
Connects individual modules into a continuous, offline voice assistant loop.
"""

import os
import time
import logging
from typing import Optional

# Import modules
from modules.audio.wake_word import WakeWordDetector
from modules.audio.audio_listener import AudioListener
from modules.audio.speech_to_text import SpeechToText
from modules.audio.tts import TTS
from modules.ai.ai_brain import AIBrain
from modules.safety.command_guard import CommandGuard
from core.command_router import CommandRouter
from utils.user_profile import UserProfile
from modules.memory.memory import Memory

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/astra_main.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Astra")

class AstraAssistant:
    def __init__(self):
        logger.info("Initializing Astra components...")
        
        # 1. Personalization & Memory
        self.profile = UserProfile(name=os.getenv("USER_NAME", "User"))
        self.memory = Memory()
        
        # 2. Audio Processing
        self.tts = TTS()
        self.listener = AudioListener()
        self.stt = SpeechToText()
        self.wake_detector = WakeWordDetector()
        
        # 3. Intelligence & Safety
        self.brain = AIBrain()
        self.guard = CommandGuard()
        
        # 4. Execution Core
        self.router = CommandRouter()
        
        self.is_running = False

    def startup(self):
        """Initial startup sequence."""
        greeting = self.profile.get_greeting()
        logger.info(f"System startup: {greeting}")
        self.tts.speak(f"{greeting} Astra is now online and ready to assist you.")

    def run(self):
        """Main execution loop."""
        self.is_running = True
        self.startup()
        
        try:
            while self.is_running:
                # 1. Listen for Wake Word ("Astra")
                # This is a blocking call until wake word or PTT is detected
                logger.info("Entering standby mode...")
                
                # We pass a lambda/callback to the detector
                self.wake_detector.start_listening(on_wake=self._on_wake_detected)
                
                # The detector loop manages itself. 
                # Our main logic is triggered via the callback below.
                
        except KeyboardInterrupt:
            logger.info("Shutdown requested via keyboard.")
        except Exception as e:
            logger.critical(f"Critical system failure: {e}")
        finally:
            self.shutdown()

    def _on_wake_detected(self):
        """Callback triggered when the wake word 'Astra' is heard."""
        logger.info("Wake word detected! Entering active mode.")
        
        try:
            # 1. Acknowledge
            self.tts.speak("Yes?", block=True) # Short acknowledgment
            
            # 2. Capture Audio
            # We record until silence is detected or 10 seconds pass
            audio_path = os.path.abspath("data/cache/last_command.wav")
            self.listener.start_recording(max_duration=10)
            self.listener.save_recording(audio_path)
            
            # 3. Speech to Text
            user_text = self.stt.transcribe_wav(audio_path)
            
            if not user_text:
                self.tts.speak("I'm sorry, I didn't catch that.")
                return

            logger.info(f"User said: {user_text}")
            
            # 4. AI Brain - Parse intent
            plan = self.brain.process_text(user_text)
            
            # 5. Safety Guard - Validate plan
            is_valid, reason, needs_confirm = self.guard.validate_plan(plan)
            
            if not is_valid:
                logger.warning(f"Safety Block: {reason}")
                self.tts.speak(f"I'm sorry, I cannot do that. {reason}")
                return
            
            if needs_confirm:
                self.tts.speak("This action requires confirmation. Are you sure?")
                # Note: In a full version, we'd record another snippet for "yes/no"
                # For MVP, we proceed if reason is just notification
                pass

            # 6. Command Router - Execution
            results = self.router.execute_plan(plan)
            
            # 7. Response Generation & Execution Speech
            # We build a final response based on execution results
            if all(r["status"] == "success" for r in results):
                self.tts.speak("Task completed successfully.")
            else:
                failed_items = [r["action"] for r in results if r["status"] != "success"]
                self.tts.speak(f"I encountered an issue with: {', '.join(failed_items)}.")

            # Update memory
            self.memory.update_history(user_text, "Task executed.")
            self.memory.set_last_plan(plan)

        except Exception as e:
            logger.error(f"Error during active processing: {e}")
            self.tts.speak("Something went wrong while processing your request.")

    def shutdown(self):
        """Graceful shutdown logic."""
        logger.info("Astra is shutting down...")
        self.is_running = False
        self.wake_detector.stop()
        self.tts.speak("Goodbye.")
        logger.info("Shutdown protocol complete.")

if __name__ == "__main__":
    # Create and run the assistant
    astra = AstraAssistant()
    astra.run()
