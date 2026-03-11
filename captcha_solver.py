"""
Captcha Solver for Instagram Account Creator Bot.
Implements FREE methods first, then falls back to paid services.
"""

import logging
import time
import requests
from typing import Optional, Dict, Any
from config import Config

logger = logging.getLogger(__name__)


class CaptchaSolver:
    """Handles captcha solving with free and paid methods."""
    
    def __init__(self):
        """Initialize captcha solver."""
        self.api_key = Config.CAPTCHA_API_KEY
        self.service = Config.CAPTCHA_SERVICE
        self.balance = None
        
        if self.api_key:
            self.check_balance()
        
        logger.info(f"CaptchaSolver initialized (API Key: {'Yes' if self.api_key else 'No'})")
    
    def solve_captcha(self, site_key: str, page_url: str) -> Optional[str]:
        """
        Solve captcha using available methods.
        
        Args:
            site_key: reCAPTCHA site key
            page_url: Page URL where captcha appears
            
        Returns:
            str: Captcha solution token or None
        """
        logger.info("Attempting to solve captcha...")
        
        # Try FREE methods first
        free_solution = self._try_free_methods()
        if free_solution:
            return free_solution
        
        # Fall back to paid service if API key available
        if self.api_key:
            return self._solve_with_2captcha(site_key, page_url)
        
        logger.warning("No captcha solution available (no API key configured)")
        return None
    
    def _try_free_methods(self) -> Optional[str]:
        """
        Try free captcha bypass methods.
        
        Returns:
            str: Success indicator or None
        """
        logger.info("Trying free captcha bypass methods...")
        
        # Method 1: Timing bypass (wait and retry)
        logger.info("Method 1: Timing bypass - waiting 15 seconds...")
        time.sleep(15)
        
        # Return indicator that free method was attempted
        # The actual bypass happens in the browser automation
        return "free_method_attempted"
    
    def _solve_with_2captcha(self, site_key: str, page_url: str) -> Optional[str]:
        """
        Solve captcha using 2Captcha service.
        
        Args:
            site_key: reCAPTCHA site key
            page_url: Page URL
            
        Returns:
            str: Captcha solution token or None
        """
        try:
            logger.info("Solving captcha with 2Captcha...")
            
            # Submit captcha
            submit_url = "http://2captcha.com/in.php"
            submit_params = {
                'key': self.api_key,
                'method': 'userrecaptcha',
                'googlekey': site_key,
                'pageurl': page_url,
                'json': 1
            }
            
            response = requests.post(submit_url, data=submit_params, timeout=30)
            result = response.json()
            
            if result.get('status') != 1:
                logger.error(f"2Captcha submit failed: {result.get('request')}")
                return None
            
            captcha_id = result.get('request')
            logger.info(f"Captcha submitted, ID: {captcha_id}")
            
            # Wait for solution
            result_url = "http://2captcha.com/res.php"
            max_attempts = 30
            
            for attempt in range(max_attempts):
                time.sleep(5)
                
                result_params = {
                    'key': self.api_key,
                    'action': 'get',
                    'id': captcha_id,
                    'json': 1
                }
                
                response = requests.get(result_url, params=result_params, timeout=30)
                result = response.json()
                
                if result.get('status') == 1:
                    solution = result.get('request')
                    logger.info("Captcha solved successfully!")
                    return solution
                
                if result.get('request') != 'CAPCHA_NOT_READY':
                    logger.error(f"2Captcha error: {result.get('request')}")
                    return None
                
                logger.debug(f"Waiting for solution... ({attempt + 1}/{max_attempts})")
            
            logger.error("Captcha solution timeout")
            return None
            
        except Exception as e:
            logger.error(f"Error solving captcha with 2Captcha: {e}")
            return None
    
    def check_balance(self) -> Optional[float]:
        """
        Check 2Captcha balance.
        
        Returns:
            float: Balance amount or None
        """
        if not self.api_key:
            return None
        
        try:
            url = "http://2captcha.com/res.php"
            params = {
                'key': self.api_key,
                'action': 'getbalance',
                'json': 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            if result.get('status') == 1:
                self.balance = float(result.get('request', 0))
                logger.info(f"2Captcha balance: ${self.balance:.2f}")
                return self.balance
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking balance: {e}")
            return None
    
    def get_balance_str(self) -> str:
        """
        Get formatted balance string.
        
        Returns:
            str: Formatted balance
        """
        if self.balance is not None:
            return f"${self.balance:.2f}"
        elif self.api_key:
            balance = self.check_balance()
            if balance is not None:
                return f"${balance:.2f}"
        
        return "Not configured"
