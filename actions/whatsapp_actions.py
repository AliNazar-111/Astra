"""
WhatsApp Web Automation Module
Provides specialized automation for WhatsApp Web.
Reuses BrowserActions session and logic.
"""

import time
import logging
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from actions.browser_actions import BrowserActions

# Configure logging
logger = logging.getLogger(__name__)

class WhatsAppActions(BrowserActions):
    """
    Subclass of BrowserActions specifically for WhatsApp Web tasks.
    """

    WHATSAPP_URL = "https://web.whatsapp.com"
    
    # Selectors (Subject to change as WhatsApp updates)
    SEARCH_INPUT = 'div[contenteditable="true"][data-tab="3"]'
    MESSAGE_INPUT = 'div[contenteditable="true"][data-tab="10"]'
    SIDEBAR_LOADED = '#pane-side'
    QR_CODE = 'canvas'

    def wait_for_login(self, timeout: int = 60) -> bool:
        """
        Waits for WhatsApp Web to load. 
        Returns True if logged in, False if still on QR code after timeout.
        """
        self.open_url(self.WHATSAPP_URL)
        logger.info("Waiting for WhatsApp Web to sync...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Check if chat list is visible
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, self.SIDEBAR_LOADED))
                )
                logger.info("WhatsApp Web logged in and ready.")
                return True
            except:
                # Check if QR code is still visible
                try:
                    self.driver.find_element(By.CSS_SELECTOR, self.QR_CODE)
                    logger.warning("Please scan the QR code to log in.")
                except:
                    pass
                time.sleep(2)
        
        logger.error("Login timeout reached.")
        return False

    def send_message(self, contact_name: str, message: str) -> bool:
        """
        Search for a contact and send a message.
        """
        if not self.driver:
            self._start_browser()
            
        if self.driver.current_url != self.WHATSAPP_URL:
            if not self.wait_for_login():
                return False

        try:
            # 1. Search for contact
            logger.info(f"Searching for contact: {contact_name}")
            search_box = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.SEARCH_INPUT))
            )
            search_box.clear()
            search_box.send_keys(contact_name)
            time.sleep(2) # Wait for results
            
            # 2. Click the contact from results
            contact_selector = f'span[title="{contact_name}"]'
            contact_element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, contact_selector))
            )
            contact_element.click()
            time.sleep(1)
            
            # 3. Type and send message
            logger.info(f"Sending message to {contact_name}: {message[:20]}...")
            msg_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.MESSAGE_INPUT))
            )
            msg_box.send_keys(message)
            msg_box.send_keys(Keys.ENTER)
            
            # 4. Verification (Check if 'Sent' icon appears or similar)
            # Simple check: Wait a bit to ensure enter was processed
            time.sleep(1)
            logger.info(f"Successfully sent message to {contact_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return False

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    wa = WhatsAppActions()
    
    # Note: Requires manual QR scan on first run!
    print("Testing WhatsApp (Check browser for QR code if not logged in)")
    if wa.send_message("Self", "Astra Test: Hello from automation!"):
        print("Test passed!")
    else:
        print("Test failed.")
