"""
Short-Term Memory Module (Hardened)
Responsible for tracking conversation history and the last executed actions.
Enables follow-up commands and context-aware interactions.
"""

import logging
import json
from typing import List, Dict, Optional, Any

# Configure logging
logger = logging.getLogger(__name__)

class Memory:
    """
    Manages Astra's short-term context.
    Hardened to prevent memory leaks and handle state serialization.
    """

    def __init__(self, max_history: int = 15):
        self.max_history = max_history
        self.history: List[Dict[str, str]] = []  # List of {'user': text, 'astra': text}
        self.last_plan: Optional[Dict[str, Any]] = None
        self.active_context: Dict[str, Any] = {}

    def update_history(self, user_text: str, astra_response: str):
        """Adds a new interaction to history with size safety."""
        if not user_text and not astra_response:
            return

        entry = {
            "user": str(user_text or ""),
            "astra": str(astra_response or "")
        }
        
        self.history.append(entry)
        
        # Enforce history limit to avoid memory growth
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
            
        logger.debug(f"Memory entry added. Current history size: {len(self.history)}")

    def set_last_plan(self, plan: Any):
        """Stores the most recent validated execution plan."""
        if isinstance(plan, dict):
            self.last_plan = plan
            logger.debug("Active plan stored in memory.")
        else:
            logger.warning("Attempted to store invalid plan format in memory.")

    def get_last_plan(self) -> Optional[Dict[str, Any]]:
        """Retrieves the previous plan for repetition or reference."""
        return self.last_plan

    def get_full_context(self) -> List[Dict[str, str]]:
        """Returns the conversation history."""
        return self.history

    def clear(self):
        """Safely resets all short-term context."""
        self.history = []
        self.last_plan = None
        self.active_context = {}
        logger.info("Memory buffer flushed.")

    def to_json(self) -> str:
        """Serializes current memory state for potential persistence."""
        try:
            return json.dumps({
                "history": self.history,
                "last_plan": self.last_plan,
                "active_context": self.active_context
            })
        except Exception as e:
            logger.error(f"Memory serialization failed: {e}")
            return "{}"

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    mem = Memory()
    mem.update_history("hello", "hi there")
    print(f"Serialized: {mem.to_json()}")

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    mem = Memory()
    
    # Simulate history
    mem.update_history("open notepad", "Opening notepad for you.")
    
    # Simulate storing a plan
    sample_plan = {"intent": "open_app", "steps": [{"action": "open_app", "target": "notepad"}]}
    mem.set_last_plan(sample_plan)
    
    print(f"History Length: {len(mem.get_full_context())}")
    print(f"Last Plan Target: {mem.get_last_plan()['steps'][0]['target']}")
    
    mem.clear()
    print(f"History after clear: {len(mem.get_full_context())}")
