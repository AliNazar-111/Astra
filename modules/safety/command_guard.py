"""
Command Guard Module
Responsible for validating AI-generated plans against security policies.
Ensures only whitelisted actions and applications are executed.
"""

import logging
from typing import Dict, List, Tuple

# Configure logging
logger = logging.getLogger(__name__)

class CommandGuard:
    """
    Security gatekeeper for Astra.
    Validates plans before they reach the execution layer.
    """

    # Whitelist of allowed actions
    ALLOWED_ACTIONS = {
        "open_app", "close_app", "type_text", "mouse_click", 
        "search_browser", "volume_control", "brightness_control", 
        "system_shutdown", "whatsapp_message", "search_file"
    }

    # Whitelist of allowed applications (can be expanded)
    ALLOWED_APPS = {
        "notepad", "calculator", "chrome", "msedge", "spotify", 
        "vlc", "explorer", "cmd", "powershell", "taskmgr"
    }

    # Actions that require explicit user confirmation
    SENSITIVE_ACTIONS = {
        "system_shutdown", "system_restart", "delete_file", "send_message"
    }

    # Keywords that indicate destructive or dangerous intent
    DESTRUCTIVE_KEYWORDS = {
        "rm", "del", "format", "erase", "wipe", "shutdown /s", "drop table", "reg delete"
    }

    def validate_plan(self, plan: Dict) -> Tuple[bool, str, bool]:
        """
        Validates the entire plan.
        
        Returns:
            Tuple[bool, str, bool]: (is_valid, reason_or_message, needs_confirmation)
        """
        if not isinstance(plan, dict):
            return False, "Invalid plan format: Expected dictionary.", False

        intent = plan.get("intent")
        steps = plan.get("steps", [])

        # Check for blocked intent from AI brain
        if intent == "blocked":
            logger.warning("AI Brain blocked this request as unsafe.")
            return False, "This request was blocked by the AI as unsafe.", False

        if not steps:
            return True, "No steps to execute.", False

        needs_confirmation = False

        for step in steps:
            action = step.get("action")
            target = str(step.get("target", "")).lower()
            value = str(step.get("value", "")).lower()

            # 1. Validate Action
            if action not in self.ALLOWED_ACTIONS:
                logger.error(f"Rejected unknown action: {action}")
                return False, f"Action '{action}' is not allowed.", False

            # 2. Validate Target App (if applicable)
            if action in ["open_app", "close_app"]:
                if target not in self.ALLOWED_APPS:
                    logger.error(f"Rejected unauthorized app: {target}")
                    return False, f"Application '{target}' is not in the whitelist.", False

            # 3. Prevent Destructive Commands
            combined_input = f"{target} {value}"
            for kw in self.DESTRUCTIVE_KEYWORDS:
                if kw in combined_input:
                    logger.critical(f"Detected destructive command attempt: {combined_input}")
                    return False, f"Destructive command detected and blocked: {kw}", False

            # 4. Check for Sensitive Actions
            if action in self.SENSITIVE_ACTIONS:
                needs_confirmation = True

        return True, "Plan validated successfully.", needs_confirmation

if __name__ == "__main__":
    # Test stub
    logging.basicConfig(level=logging.INFO)
    guard = CommandGuard()

    # Test case: Good plan
    good_plan = {
        "intent": "open_app",
        "steps": [{"action": "open_app", "target": "notepad", "value": ""}]
    }
    print(f"Good Plan: {guard.validate_plan(good_plan)}")

    # Test case: Unsafe app
    bad_app = {
        "intent": "open_app",
        "steps": [{"action": "open_app", "target": "malware.exe", "value": ""}]
    }
    print(f"Bad App: {guard.validate_plan(bad_app)}")

    # Test case: Dangerous command
    danger = {
        "intent": "type_text",
        "steps": [{"action": "type_text", "target": "cmd", "value": "del /f /s /q C:\\"}]
    }
    print(f"Danger: {guard.validate_plan(danger)}")
