"""
AI Brain Module
Responsible for intent understanding and converting natural language into structured JSON actions.
Uses a local LLM (Ollama) for offline intelligence.
"""

import os
import json
import logging
import requests
from typing import List, Dict, Optional

# Configure logging
logger = logging.getLogger(__name__)

class AIBrain:
    """
    The orchestrator of intelligence for Astra.
    Converts speech-to-text input into machine-readable JSON plans.
    """

    def __init__(self, model: str = "llama3.2", host: str = "http://localhost:11434"):
        """
        Initialize the AI Brain.
        
        Args:
            model (str): The name of the local LLM model to use via Ollama.
            host (str): The Ollama server endpoint.
        """
        self.model = model
        self.host = host
        self.context: List[Dict[str, str]] = []
        self.max_context_len = 5  # Keep last 5 exchanges
        
        self.system_prompt = (
            "You are Astra, a Windows Desktop Voice Assistant. "
            "Your job is to convert user requests into a valid JSON plan. "
            "SCHEMA: {'intent': str, 'steps': [{'action': str, 'target': str, 'value': str}]}. "
            "RULES: 1. ALWAYS return valid JSON. 2. NEVER return any text or explanation outside the JSON. "
            "3. If a command is harmful, illegal, or unsafe (e.g., deleting system files, hacking), "
            "return {'intent': 'blocked', 'steps': []}. "
            "4. Multi-step support is required if the user asks for multiple things. "
            "AVAILABLE ACTIONS: open_app, close_app, type_text, mouse_click, search_browser, "
            "volume_control, brightness_control, system_shutdown, whatsapp_message, search_file."
        )

    def process_text(self, text: str) -> Dict:
        """
        Processes natural language text and returns a structured JSON plan.
        """
        logger.info(f"Processing input: '{text}'")
        
        # Add user message to context
        self.context.append({"role": "user", "content": text})
        
        # Trim context if too long
        if len(self.context) > self.max_context_len * 2:
            self.context = self.context[-(self.max_context_len * 2):]

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt}
            ] + self.context,
            "stream": False,
            "format": "json"
        }

        try:
            response = requests.post(f"{self.host}/api/chat", json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            raw_response = result.get("message", {}).get("content", "{}")
            
            # Parse and validate JSON
            parsed_json = json.loads(raw_response)
            
            # Add assistant response to context for future turns (short-term memory)
            # We store the raw response to help the LLM maintain state
            self.context.append({"role": "assistant", "content": raw_response})
            
            return parsed_json

        except requests.exceptions.ConnectionError:
            error_msg = "Ollama connection failed. Is the server running?"
            logger.error(error_msg)
            return {"intent": "error", "message": error_msg}
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON from LLM response.")
            return {"intent": "error", "message": "Invalid JSON response from AI."}
        except Exception as e:
            logger.error(f"Unexpected error in AI Brain: {e}")
            return {"intent": "error", "message": str(e)}

    def clear_context(self):
        """Resets the short-term memory."""
        self.context = []
        logger.info("AI Brain short-term context cleared.")

if __name__ == "__main__":
    # Test stub
    logging.basicConfig(level=logging.INFO)
    brain = AIBrain()
    print("Testing AI Brain (Request: 'Open notepad and type Hello')")
    plan = brain.process_text("Open notepad and type Hello")
    print(json.dumps(plan, indent=2))
