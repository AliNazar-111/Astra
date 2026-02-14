"""
User Profile Module
Handles user identification and personalized greetings.
"""

import datetime
import logging
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

class UserProfile:
    """
    Manages user information and generates personalized greetings.
    """

    def __init__(self, name: str = "User"):
        """
        Initialize the user profile.
        
        Args:
            name (str): The name of the user to be addressed.
        """
        self.name = name

    def get_greeting(self) -> str:
        """
        Returns a time-based greeting for the user.
        Example: "Good morning, User."
        """
        hour = datetime.datetime.now().hour
        
        if 5 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 18:
            period = "afternoon"
        elif 18 <= hour < 22:
            period = "evening"
        else:
            period = "night"

        greeting = f"Good {period}, {self.name}."
        
        # Add a startup specific message if needed
        return greeting

    def set_name(self, name: str):
        """Updates the user's name."""
        self.name = name
        logger.info(f"User name updated to: {name}")

    def get_user_name(self) -> str:
        """Returns the current user name."""
        return self.name

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    profile = UserProfile(name="Ali")
    
    print(f"Standard Greeting: {profile.get_greeting()}")
    
    # Test time mocking if needed, but for now current time is fine
    print("User profile test complete.")
