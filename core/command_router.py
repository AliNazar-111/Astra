"""
Command Router Module
Responsible for routing validated JSON steps to their respective action handlers.
Sequentially executes steps and reports status.
"""

import logging
from typing import Dict, List, Any

# Configure logging
logger = logging.getLogger(__name__)

class CommandRouter:
    """
    The central hub for distributing tasks to automation sub-modules.
    It does not contain execution logic itself; it routes requests.
    """

    def __init__(self):
        # In a real implementation, we would import and instantiate the actual handlers here.
        # For now, we define a mapping or a placeholder structure.
        self.action_map = {
            "open_app": self._handle_app_launch,
            "close_app": self._handle_app_launch,
            "type_text": self._handle_input,
            "mouse_click": self._handle_input,
            "search_browser": self._handle_browser,
            "volume_control": self._handle_system,
            "brightness_control": self._handle_system,
            "system_shutdown": self._handle_system,
            "whatsapp_message": self._handle_messaging,
            "search_file": self._handle_utilities
        }

    def execute_plan(self, plan: Dict) -> List[Dict[str, Any]]:
        """
        Iterates through the steps in a plan and routes them.
        """
        steps = plan.get("steps", [])
        execution_report = []

        logger.info(f"Starting execution of plan with {len(steps)} steps.")

        for i, step in enumerate(steps):
            action = step.get("action")
            logger.info(f"Routing step {i+1}: {action}")

            handler = self.action_map.get(action)
            
            if handler:
                try:
                    # Route to the appropriate handler
                    status = handler(step)
                    execution_report.append({
                        "step": i + 1,
                        "action": action,
                        "status": "success" if status else "failed"
                    })
                    
                    if not status:
                        logger.error(f"Step {i+1} ({action}) failed. Stopping sequential execution.")
                        break
                except Exception as e:
                    logger.error(f"Exception during step {i+1} execution: {e}")
                    execution_report.append({
                        "step": i + 1,
                        "action": action,
                        "status": "error",
                        "message": str(e)
                    })
                    break
            else:
                logger.warning(f"No handler found for action: {action}")
                execution_report.append({
                    "step": i + 1,
                    "action": action,
                    "status": "not_implemented"
                })
                break

        return execution_report

    # --- Router Handlers (Placeholders delegating to actions/ directory) ---

    def _handle_app_launch(self, step: Dict) -> bool:
        """Routes to actions/apps/app_launcher.py"""
        from actions.apps.app_launcher import AppLauncher
        # Implementation will instantiate specific handler
        logger.info(f"Delegating to AppLauncher: {step}")
        return True # Placeholder success

    def _handle_input(self, step: Dict) -> bool:
        """Routes to actions/input/keyboard_controller.py or mouse_controller.py"""
        logger.info(f"Delegating to InputController: {step}")
        return True # Placeholder success

    def _handle_browser(self, step: Dict) -> bool:
        """Routes to actions/browser/browser_launcher.py"""
        logger.info(f"Delegating to BrowserController: {step}")
        return True # Placeholder success

    def _handle_system(self, step: Dict) -> bool:
        """Routes to actions/system/ handlers"""
        logger.info(f"Delegating to SystemController: {step}")
        return True # Placeholder success

    def _handle_messaging(self, step: Dict) -> bool:
        """Routes to actions/messaging/whatsapp_controller.py"""
        logger.info(f"Delegating to MessagingController: {step}")
        return True # Placeholder success

    def _handle_utilities(self, step: Dict) -> bool:
        """Routes to actions/utilities/ handlers"""
        logger.info(f"Delegating to UtilitiesController: {step}")
        return True # Placeholder success

if __name__ == "__main__":
    # Test stub
    logging.basicConfig(level=logging.INFO)
    router = CommandRouter()
    
    test_plan = {
        "intent": "open_app",
        "steps": [
            {"action": "open_app", "target": "notepad", "value": ""},
            {"action": "type_text", "target": "notepad", "value": "Hello Astra"}
        ]
    }
    
    report = router.execute_plan(test_plan)
    print("Execution Report:")
    for r in report:
        print(r)
