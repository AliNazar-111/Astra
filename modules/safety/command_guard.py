"""
Command Guard Module (Hardened)
Responsible for validating AI-generated plans against security policies.
Ensures strict whitelist adherence and destructive command blocking.
"""

import logging
import json
from typing import Dict, List, Tuple, Any

# Configure logging
logger = logging.getLogger(__name__)

class CommandGuard:
    """
    Security gatekeeper for Astra.
    Hardened for fail-safe validation.
    """

    # Whitelist of allowed actions
    ALLOWED_ACTIONS = {
        "open_app", "close_app", "type_text", "mouse_click", 
        "search_browser", "volume_control", "brightness_control", 
        "system_shutdown", "whatsapp_message", "search_file"
    }

    # Whitelist of allowed applications
    ALLOWED_APPS = {
        "notepad", "calculator", "chrome", "msedge", "spotify", 
        "vlc", "explorer", "cmd", "powershell", "taskmgr"
    }

    # Dangerous patterns
    DESTRUCTIVE_KEYWORDS = {
        "rm ", "del ", "format ", "erase ", "wipe ", "drop table", "reg delete", "> nul"
    }

    def validate_plan(self, plan: Any) -> Tuple[bool, str, bool]:
        """
        Validates the entire plan.
        Returns: (is_valid, reason, needs_confirmation)
        """
        if not isinstance(plan, dict):
            logger.error(f"Validation failed: Plan is not a dictionary. Got {type(plan)}")
            return False, "Invalid plan format.", False

        intent = str(plan.get("intent", "unknown")).lower()
        steps = plan.get("steps", [])

        if intent == "blocked":
            logger.warning("AI Brain explicitly blocked this request.")
            return False, "AI safety filter triggered.", False

        if not isinstance(steps, list):
            logger.error("Validation failed: 'steps' is not a list.")
            return False, "Invalid steps format.", False

        needs_confirmation = False

        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                logger.error(f"Step {i} is not a dictionary.")
                return False, f"Malformed step {i}.", False

            action = step.get("action")
            target = str(step.get("target", "")).lower()
            value = str(step.get("value", "")).lower()

            # 1. Action Whitelist
            if action not in self.ALLOWED_ACTIONS:
                logger.warning(f"Unauthorized action attempt: {action}")
                return False, f"Action '{action}' is not permitted.", False

            # 2. App Whitelist
            if action in ["open_app", "close_app"]:
                if not any(app in target for app in self.ALLOWED_APPS):
                    logger.warning(f"Unauthorized app access: {target}")
                    return False, f"Access to '{target}' is restricted.", False

            # 3. Destructive Command Scan
            combined = f"{target} {value}".lower()
            for kw in self.DESTRUCTIVE_KEYWORDS:
                if kw in combined:
                    logger.critical(f"DESTRUCTIVE COMMAND DETECTED: {kw} in {combined}")
                    return False, "Destructive operation blocked.", False

            # 4. Confirmation Flags
            if action in ["system_shutdown", "whatsapp_message"]:
                needs_confirmation = True

        logger.info(f"Plan validation successful: {intent}")
        return True, "Safe", needs_confirmation

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
