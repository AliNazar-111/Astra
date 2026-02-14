"""
AI Brain Module (Hardened)
Responsible for intent understanding and converting natural language into structured JSON actions.
Uses a local LLM (Ollama) with retries and robust error handling.
"""

import os
import json
import logging
import requests
import time
from typing import List, Dict, Optional, Any

# Configure logging
logger = logging.getLogger(__name__)

class AIBrain:
    """
    The orchestrator of intelligence for Astra.
    Converts speech-to-text input into machine-readable JSON plans.
    """

    def __init__(self, model: str = None, host: str = None):
        """
        Initialize the AI Brain.
        """
        self.model = model or os.getenv("LLM_MODEL", "llama3.2")
        self.host = host or os.getenv("LLM_HOST", "http://localhost:11434")
        self.context: List[Dict[str, str]] = []
        self.max_context_len = 5
        self.timeout = 15 # Seconds
        self.max_retries = 2
        
        self.system_prompt = (
            "You are Astra, a Windows Desktop Voice Assistant. "
            "Convert user requests into a valid JSON plan. "
            "SCHEMA: {'intent': str, 'steps': [{'action': str, 'target': str, 'value': str}]}. "
            "RULES: 1. ALWAYS return valid JSON. 2. NO extra text. "
            "3. If unsafe, return {'intent': 'blocked', 'steps': []}. "
            "ACTIONS: open_app, close_app, type_text, mouse_click, search_browser, "
            "volume_control, brightness_control, system_shutdown, whatsapp_message, search_file."
        )

    def process_text(self, text: str) -> Dict[str, Any]:
        """
        Processes natural language text and returns a structured JSON plan.
        Includes retries and parsing safety.
        """
        if not text:
            return {"intent": "empty", "steps": []}

        logger.info(f"Processing command: '{text}'")
        
        # Maintain context
        self.context.append({"role": "user", "content": text})
        if len(self.context) > self.max_context_len * 2:
            self.context = self.context[-(self.max_context_len * 2):]

        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": self.system_prompt}] + self.context,
            "stream": False,
            "format": "json"
        }

        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(f"{self.host}/api/chat", json=payload, timeout=self.timeout)
                response.raise_for_status()
                
                result = response.json()
                raw_content = result.get("message", {}).get("content", "{}").strip()
                
                # Robust JSON Recovery
                try:
                    parsed_json = json.loads(raw_content)
                except json.JSONDecodeError:
                    logger.warning(f"Malformed JSON from AI (Attempt {attempt+1}). Cleaning response...")
                    # Basic cleanup for common LLM hiccups (extra backticks, etc)
                    clean_content = raw_content.replace("```json", "").replace("```", "").strip()
                    parsed_json = json.loads(clean_content)
                
                # Check for empty or invalid schema
                if "intent" not in parsed_json:
                    parsed_json["intent"] = "unknown"
                if "steps" not in parsed_json:
                    parsed_json["steps"] = []

                # Feed back to context
                self.context.append({"role": "assistant", "content": json.dumps(parsed_json)})
                logger.info(f"Successfully generated plan: {parsed_json.get('intent')}")
                return parsed_json

            except requests.exceptions.Timeout:
                logger.error(f"Ollama request timed out (Attempt {attempt+1}/{self.max_retries + 1})")
            except requests.exceptions.ConnectionError:
                logger.error(f"Ollama connection refused. Is server running at {self.host}?")
                break # Don't retry connection refused immediately
            except Exception as e:
                logger.error(f"Unexpected error in AI Brain (Attempt {attempt+1}): {e}")
            
            if attempt < self.max_retries:
                time.sleep(1) # Small backoff

        return {"intent": "error", "message": "Failed to communicate with AI Brain.", "steps": []}

    def clear_context(self):
        """Resets the short-term memory."""
        self.context = []
        logger.info("AI Brain context cleared.")


if __name__ == "__main__":
    # Test stub
    logging.basicConfig(level=logging.INFO)
    brain = AIBrain()
    print("Testing AI Brain (Request: 'Open notepad and type Hello')")
    plan = brain.process_text("Open notepad and type Hello")
    print(json.dumps(plan, indent=2))
