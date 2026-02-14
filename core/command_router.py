"""
Command Router Module (Hardened)
Routes validated JSON steps to action handlers.
Ensures fail-safe execution and robust error reporting.
"""

import logging
import traceback
from typing import Dict, List, Any

# Configure logging
logger = logging.getLogger(__name__)

class CommandRouter:
    """
    The central distribution hub for automation.
    Hardened to handle missing sub-modules and runtime execution errors.
    """

    def __init__(self):
        # Lazy loading of specialized handlers to save memory
        self._handlers = {}

    def execute_plan(self, plan: Any) -> List[Dict[str, Any]]:
        """
        Sequentially executes steps and provides a robust execution report.
        """
        if not isinstance(plan, dict) or "steps" not in plan:
            logger.error("Router received invalid plan.")
            return [{"status": "fatal_error", "message": "Invalid plan structure"}]

        steps = plan.get("steps", [])
        report = []

        logger.info(f"Routing {len(steps)} steps for intent: {plan.get('intent')}")

        for i, step in enumerate(steps):
            action = step.get("action")
            logger.info(f"Step {i+1}: {action}")

            try:
                success = self._dispatch(step)
                report.append({
                    "step": i + 1,
                    "action": action,
                    "status": "success" if success else "failed"
                })
                
                if not success:
                    logger.warning(f"Stop-on-failure: Step {i+1} ({action}) failed.")
                    break
                    
            except Exception as e:
                error_trace = traceback.format_exc()
                logger.error(f"Execution crash in step {i+1} ({action}): {e}\n{error_trace}")
                report.append({
                    "step": i + 1,
                    "action": action,
                    "status": "error",
                    "message": str(e)
                })
                break

        return report

    def _dispatch(self, step: Dict) -> bool:
        """Dynamically routes to the correct handler."""
        action = step.get("action")
        
        # Mapping to internal handler methods
        # This keeps the router high-level and clean
        router_map = {
            "open_app": ("system", "open_app"),
            "close_app": ("system", "close_app"),
            "switch_window": ("system", "switch_window"),
            "type_text": ("system", "type_text"),
            "volume_control": ("system", "control_volume"),
            "search_browser": ("browser", "open_url"),
            "whatsapp_message": ("whatsapp", "send_message")
        }

        if action not in router_map:
            logger.error(f"No dispatch rule for action: {action}")
            return False

        module_type, method_name = router_map[action]
        handler = self._get_handler(module_type)
        
        if not handler:
            logger.error(f"Missing handler module: {module_type}")
            return False

        # Execute the method on the handler instance
        try:
            method = getattr(handler, method_name)
            
            # Special handling for argument passing
            # This would be expanded as we add more actions
            if module_type == "system":
                if action in ["open_app", "close_app", "switch_window"]:
                    return method(step.get("target"))
                elif action == "type_text":
                    return method(step.get("value"))
                elif action == "volume_control":
                    return method(step.get("target"), amount=int(step.get("value", 1)))
            
            elif module_type == "browser":
                return method(step.get("value") or step.get("target"))
            
            elif module_type == "whatsapp":
                return method(step.get("target"), step.get("value"))

        except Exception as e:
            logger.error(f"Dispatch logic error for {action}: {e}")
            return False

    def _get_handler(self, module_type: str) -> Any:
        """Lazy loads and caches action modules."""
        if module_type in self._handlers:
            return self._handlers[module_type]

        try:
            if module_type == "system":
                from actions.system_actions import SystemActions
                self._handlers[module_type] = SystemActions()
            elif module_type == "browser":
                from actions.browser_actions import BrowserActions
                self._handlers[module_type] = BrowserActions()
            elif module_type == "whatsapp":
                from actions.whatsapp_actions import WhatsAppActions
                self._handlers[module_type] = WhatsAppActions()
            
            return self._handlers.get(module_type)
        except ImportError as e:
            logger.error(f"Failed to import action module '{module_type}': {e}")
            return None
