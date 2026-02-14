"""
Browser Automation Module
Provides automation for web browsing tasks using Selenium.
Supports headed mode, persistent sessions, and reliable interaction.
"""

import os
import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# Configure logging
logger = logging.getLogger(__name__)

class BrowserActions:
    """
    Browser automation handler using Microsoft Edge (default on Windows).
    """

    def __init__(self, user_data_dir: Optional[str] = None):
        """
        Initialize the browser controller.
        
        Args:
            user_data_dir (str): Path for persistent sessions. 
                                Default: 'data/cache/browser_session'
        """
        self.driver = None
        self.user_data_dir = user_data_dir or os.path.abspath("data/cache/browser_session")
        self.wait_timeout = 10

    def _start_browser(self):
        """Starts the Edge browser in headed mode with persistent session."""
        if self.driver:
            return

        logger.info("Starting Edge browser...")
        options = webdriver.EdgeOptions()
        
        # Persistent session support
        os.makedirs(self.user_data_dir, exist_ok=True)
        options.add_argument(f"user-data-dir={self.user_data_dir}")
        options.add_argument("--start-maximized")
        options.add_experimental_option("detach", True) # Keep browser open after script ends

        try:
            service = EdgeService(EdgeChromiumDriverManager().install())
            self.driver = webdriver.Edge(service=service, options=options)
            logger.info("Browser started successfully.")
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise

    def open_url(self, url: str) -> bool:
        """Navigates to a specific URL."""
        if not url.startswith("http"):
            url = f"https://www.google.com/search?q={url}" # Default to search if not URL
            
        logger.info(f"Navigating to: {url}")
        try:
            self._start_browser()
            self.driver.get(url)
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False

    def click_element(self, selector: str, by: By = By.CSS_SELECTOR) -> bool:
        """Clicks an element found by selector."""
        logger.info(f"Clicking element: {selector}")
        try:
            element = WebDriverWait(self.driver, self.wait_timeout).until(
                EC.element_to_be_clickable((by, selector))
            )
            element.click()
            return True
        except Exception as e:
            logger.error(f"Click failed for {selector}: {e}")
            return False

    def type_text(self, selector: str, text: str, submit: bool = False, by: By = By.CSS_SELECTOR) -> bool:
        """Types text into an input field."""
        logger.info(f"Typing into {selector}: {text[:20]}...")
        try:
            element = WebDriverWait(self.driver, self.wait_timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            element.clear()
            element.send_keys(text)
            if submit:
                element.send_keys(Keys.ENTER)
            return True
        except Exception as e:
            logger.error(f"Typing failed for {selector}: {e}")
            return False

    def close_browser(self):
        """Closes the browser instance."""
        if self.driver:
            logger.info("Closing browser.")
            self.driver.quit()
            self.driver = None

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    browser = BrowserActions()
    
    print("Test: Searching Google...")
    if browser.open_url("https://www.google.com"):
        browser.type_text("textarea[name='q']", "Astra Voice Assistant GitHub", submit=True)
        print("Test: Search submitted.")
    else:
        print("Test failed: Could not open browser.")
