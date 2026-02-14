"""
Astra - Main Application Orchestrator (Hardened)
Connects individual modules into a continuous, offline voice assistant loop.
Ensures robustness, low CPU usage, and safe error recovery.
"""

import os
import time
import logging
import threading
import signal
import sys
from typing import Optional

# Import modules
try:
    from modules.audio.wake_word import WakeWordDetector
    from modules.audio.audio_listener import AudioListener
    from modules.audio.speech_to_text import SpeechToText
    from modules.audio.tts import TTS
    from modules.ai.ai_brain import AIBrain
    from modules.safety.command_guard import CommandGuard
    from core.command_router import CommandRouter
    from utils.user_profile import UserProfile
    from modules.memory.memory import Memory
except ImportError as e:
    print(f"CRITICAL: Failed to import internal modules: {e}")
    sys.exit(1)

# Configure Logging (Hardened)
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "astra_main.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Astra")

class AstraAssistant:
    def __init__(self):
        logger.info("Initializing Astra components...")
        self.is_running = False
        self._stop_event = threading.Event()
        
        try:
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
            
            logger.info("All modules initialized successfully.")
        except Exception as e:
            logger.critical(f"Initialization failed: {e}", exc_info=True)
            raise

    def startup(self):
        """Initial startup sequence."""
        try:
            greeting = self.profile.get_greeting()
            logger.info(f"System startup for user: {self.profile.get_user_name()}")
            # Non-blocking greeting to avoid startup freeze
            self.tts.speak(f"{greeting} Astra is now online and ready to assist you.", block=False)
        except Exception as e:
            logger.error(f"Startup greeting failed: {e}")

    def run(self):
        """Main execution loop."""
        self.is_running = True
        self.startup()
        
        # Register signal handlers for clean exit
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Entering main operational loop.")
        
        try:
            while self.is_running and not self._stop_event.is_set():
                logger.info("Astra is listening for wake word...")
                
                # The wake detector runs its own loop. 
                # We use a non-blocking wait or specific detector logic.
                try:
                    self.wake_detector.start_listening(on_wake=self._on_wake_detected)
                except Exception as e:
                    logger.error(f"Wake detector error: {e}. Restarting detector in 5s...")
                    time.sleep(5)
                
                # Small sleep to yield CPU if detector is non-blocking
                time.sleep(0.1)
                
        except Exception as e:
            logger.critical(f"Unexpected loop crash: {e}", exc_info=True)
        finally:
            self.shutdown()

    def _on_wake_detected(self):
        """Callback triggered when the wake word 'Astra' is heard."""
        logger.info("Active session started via wake word.")
        
        # Run active processing in a separate thread to keep the detector alive/unfrozen
        thread = threading.Thread(target=self._process_active_command, daemon=True)
        thread.start()

    def _process_active_command(self):
        """Handles the recording -> AI -> Action pipeline."""
        try:
            # 1. Acknowledge (Immediate feedback)
            self.tts.speak("Listening.", block=True)
            
            # 2. Capture Audio (With timeout protection)
            audio_path = os.path.abspath("data/cache/last_command.wav")
            os.makedirs(os.path.dirname(audio_path), exist_ok=True)
            
            success = self.listener.start_recording(max_duration=10)
            if not success:
                logger.warning("Recording failed or timed out.")
                return

            self.listener.save_recording(audio_path)
            
            # 3. Speech to Text
            user_text = self.stt.transcribe_wav(audio_path)
            
            if not user_text or len(user_text.strip()) < 2:
                logger.debug("No valid speech detected.")
                return

            logger.info(f"Command received: '{user_text}'")
            
            # 4. AI Brain - Intent Understanding
            plan = self.brain.process_text(user_text)
            
            # 5. Safety Guard - Policy Check
            is_valid, reason, needs_confirm = self.guard.validate_plan(plan)
            
            if not is_valid:
                logger.warning(f"Security Alert: Blocked action '{user_text}'. Reason: {reason}")
                self.tts.speak(f"I'm sorry, that action is not permitted. {reason}")
                return
            
            # 6. Command Execution (Via Router)
            logger.info(f"Executing plan: {plan.get('intent', 'unknown')}")
            results = self.router.execute_plan(plan)
            
            # 7. Final Response (Feedback)
            if results:
                failed = [r['action'] for r in results if r['status'] != 'success']
                if not failed:
                    self.tts.speak("Success.", block=False)
                else:
                    self.tts.speak(f"Problem with {', '.join(failed)}.", block=False)
            
            # Update history for context
            self.memory.update_history(user_text, "Processed.")
            self.memory.set_last_plan(plan)

        except Exception as e:
            logger.error(f"Error in command processing: {e}", exc_info=True)
            self.tts.speak("I encountered an internal error.", block=False)

    def _signal_handler(self, signum, frame):
        """Handles OS signals for graceful termination."""
        logger.info(f"Signal {signum} received. Stopping Astra...")
        self.is_running = False
        self._stop_event.set()

    def shutdown(self):
        """Ensures all resources are released correctly."""
        if not hasattr(self, '_shutting_down'):
            self._shutting_down = True
            logger.info("Initiating graceful shutdown sequence...")
            
            try:
                self.is_running = False
                self.wake_detector.stop()
                self.tts.speak("Shutting down. Goodbye.", block=True)
            except Exception as e:
                logger.error(f"Error during module shutdown: {e}")
            
            logger.info("Astra has been safely deactivated.")
            sys.exit(0)

if __name__ == "__main__":
    try:
        astra = AstraAssistant()
        astra.run()
    except Exception as e:
        print(f"FATAL: Application failed to start: {e}")


if __name__ == "__main__":
    # Create and run the assistant
    astra = AstraAssistant()
    astra.run()
