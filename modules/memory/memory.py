"""
Short-Term Memory Module
Responsible for tracking conversation history and the last executed actions.
Enables follow-up commands like "do it again".
"""

import logging
from typing import List, Dict, Optional, Any

# Configure logging
logger = logging.getLogger(__name__)

class Memory:
    """
    Manages Astra's short-term context.
    Stores recent interactions and the last validated plan.
    """

    def __init__(self, max_history: int = 10):
        """
        Initialize the memory buffer.
        
        Args:
            max_history (int): Maximum number of command-response pairs to keep.
        """
        self.max_history = max_history
        self.history: List[Dict[str, str]] = []  # List of {'user': text, 'astra': text}
        self.last_plan: Optional[Dict[str, Any]] = None
        self.active_context: Dict[str, Any] = {}

    def update_history(self, user_text: str, astra_response: str):
        """Adds a new interaction to history."""
        self.history.append({
            "user": user_text,
            "astra": astra_response
        })
        
        # Keep within bounds
        if len(self.history) > self.max_history:
            self.history.pop(0)
            
        logger.info(f"Memory updated with interaction: {user_text[:20]}...")

    def set_last_plan(self, plan: Dict[str, Any]):
        """Stores the most recent validated execution plan."""
        self.last_plan = plan
        logger.info("Most recent plan stored in memory.")

    def get_last_plan(self) -> Optional[Dict[str, Any]]:
        """Retrieves the previous plan for repetition or reference."""
        return self.last_plan

    def get_full_context(self) -> List[Dict[str, str]]:
        """Returns the conversation history for context usage."""
        return self.history

    def clear(self):
        """Safely resets all short-term context."""
        self.history = []
        self.last_plan = None
        self.active_context = {}
        logger.info("Short-term memory cleared.")

    def set_context_value(self, key: str, value: Any):
        """Stores a specific piece of context information."""
        self.active_context[key] = value

    def get_context_value(self, key: str) -> Optional[Any]:
        """Retrieves a specific value from active context."""
        return self.active_context.get(key)

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
