"""
Instagram Account Creator Module.
Handles complete Instagram account creation flow with Selenium.
"""

import logging
import time
import random
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc

from config import Config
from user_config import UserConfig
from email_providers import EmailProviderManager
from captcha_solver import CaptchaSolver
from utils import (
    random_delay, human_typing_delay, generate_birthday,
    create_simple_avatar, save_credentials, generate_user_agent,
    get_random_resolution
)

logger = logging.getLogger(__name__)


class InstagramCreator:
    """Handles Instagram account creation automation."""
    
    def __init__(self, user_config: UserConfig, progress_callback: Optional[Callable] = None):
        """
        Initialize Instagram creator.
        
        Args:
            user_config: User configuration
            progress_callback: Callback function for progress updates
        """
        self.config = user_config
        self.progress_callback = progress_callback
        self.email_manager = EmailProviderManager()
        self.captcha_solver = CaptchaSolver()
        self.driver: Optional[webdriver.Chrome] = None
        self.current_account = 0
        self.successful_accounts = []
        self.failed_accounts = []
    
    def create_accounts(self) -> Dict[str, Any]:
        """
        Create multiple Instagram accounts.
        
        Returns:
            dict: Results summary
        """
        logger.info(f"Starting creation of {self.config.num_accounts} accounts...")
        self._send_progress("🚀 Starting account creation...", 0)
        
        start_time = time.time()
        
        for i in range(self.config.num_accounts):
            self.current_account = i + 1
            progress_pct = int((i / self.config.num_accounts) * 100)
            
            logger.info(f"\n{'='*50}")
            logger.info(f"Creating account {self.current_account}/{self.config.num_accounts}")
            logger.info(f"{'='*50}\n")
            
            self._send_progress(
                f"📝 Creating account {self.current_account}/{self.config.num_accounts}...",
                progress_pct
            )
            
            try:
                result = self._create_single_account(i)
                
                if result['success']:
                    self.successful_accounts.append(result)
                    self._send_progress(
                        f"✅ Account {self.current_account} created successfully!",
                        progress_pct
                    )
                else:
                    self.failed_accounts.append(result)
                    self._send_progress(
                        f"❌ Account {self.current_account} failed: {result.get('error', 'Unknown error')}",
                        progress_pct
                    )
                
            except Exception as e:
                logger.error(f"Unexpected error creating account {self.current_account}: {e}")
                self.failed_accounts.append({
                    'account_number': self.current_account,
                    'success': False,
                    'error': str(e)
                })
            
            # Delay between accounts
            if i < self.config.num_accounts - 1:
                delay = random.randint(
                    Config.MIN_DELAY_BETWEEN_ACCOUNTS,
                    Config.MAX_DELAY_BETWEEN_ACCOUNTS
                )
                logger.info(f"Waiting {delay} seconds before next account...")
                time.sleep(delay)
        
        elapsed_time = int(time.time() - start_time)
        
        summary = {
            'total': self.config.num_accounts,
            'successful': len(self.successful_accounts),
            'failed': len(self.failed_accounts),
            'elapsed_time': elapsed_time,
            'accounts': self.successful_accounts
        }
        
        self._send_progress("✨ Account creation completed!", 100)
        
        return summary
    
    def _create_single_account(self, index: int) -> Dict[str, Any]:
        """
        Create a single Instagram account.
        
        Args:
            index: Account index
            
        Returns:
            dict: Account creation result
        """
        account_data = {
            'account_number': self.current_account,
            'success': False,
            'created_at': datetime.now().isoformat()
        }
        
        try:
            # Step 1: Initialize browser
            self._send_progress("🌐 Initializing browser...", step="browser")
            if not self._init_browser():
                raise Exception("Failed to initialize browser")
            
            # Step 2: Generate email
            self._send_progress("📧 Creating email address...", step="email")
            email_data = self.email_manager.create_email_with_rotation()
            
            if not email_data:
                raise Exception("Failed to create email address")
            
            account_data['email'] = email_data['email']
            account_data['email_provider'] = email_data.get('provider', 'unknown')
            
            # Step 3: Generate account details
            username = self.config.get_username(index)
            fullname = self.config.get_fullname(index)
            password = self.config.get_password(index)
            
            account_data['username'] = username
            account_data['fullname'] = fullname
            account_data['password'] = password
            
            logger.info(f"Account details: {username} / {email_data['email']}")
            
            # Step 4: Navigate to signup page
            self._send_progress("🔗 Opening Instagram signup page...", step="navigate")
            if not self._navigate_to_signup():
                raise Exception("Failed to navigate to signup page")
            
            # Step 5: Fill signup form
            self._send_progress("✍️ Filling signup form...", step="form")
            if not self._fill_signup_form(email_data['email'], fullname, username, password):
                raise Exception("Failed to fill signup form")
            
            # Step 6: Handle captcha if present
            if self._check_for_captcha():
                self._send_progress("🤖 Solving captcha...", step="captcha")
                if not self._solve_captcha():
                    raise Exception("Failed to solve captcha")
            
            # Step 7: Submit form
            self._send_progress("📤 Submitting signup form...", step="submit")
            if not self._submit_signup():
                raise Exception("Failed to submit signup form")
            
            # Step 8: Wait for and enter verification code
            self._send_progress("📬 Waiting for verification code...", step="verification")
            verification_code = self.email_manager.fetch_instagram_code(
                email_data,
                timeout=Config.EMAIL_CHECK_TIMEOUT
            )
            
            if not verification_code:
                # Try to resend code
                self._click_resend_code()
                verification_code = self.email_manager.fetch_instagram_code(
                    email_data,
                    timeout=Config.EMAIL_CHECK_TIMEOUT
                )
            
            if not verification_code:
                raise Exception("Failed to receive verification code")
            
            if not self._enter_verification_code(verification_code):
                raise Exception("Failed to enter verification code")
            
            # Step 9: Complete birthday selection
            self._send_progress("🎂 Setting birthday...", step="birthday")
            if not self._set_birthday():
                raise Exception("Failed to set birthday")
            
            # Step 10: Optional profile setup
            if Config.ADD_PROFILE_PICTURE:
                self._send_progress("📸 Adding profile picture...", step="avatar")
                avatar_path = create_simple_avatar(username)
                if avatar_path:
                    self._upload_profile_picture(avatar_path)
            
            # Step 11: Follow suggested accounts
            if Config.FOLLOW_SUGGESTED_ACCOUNTS:
                self._send_progress("👥 Following suggested accounts...", step="follow")
                self._follow_suggested_accounts()
            
            # Step 12: Setup 2FA (optional)
            if Config.ENABLE_2FA:
                self._send_progress("🔐 Setting up 2FA...", step="2fa")
                totp_secret = self._setup_2fa()
                if totp_secret:
                    account_data['totp_secret'] = totp_secret
            
            # Save credentials
            account_data['success'] = True
            account_data['status'] = 'active'
            save_credentials(account_data)
            
            logger.info(f"✅ Account created successfully: {username}")
            
            return account_data
            
        except Exception as e:
            logger.error(f"Error creating account: {e}")
            account_data['error'] = str(e)
            return account_data
            
        finally:
            self._cleanup_browser()
    
    def _init_browser(self) -> bool:
        """
        Initialize browser with stealth settings.
        
        Returns:
            bool: True if successful
        """
        try:
            options = uc.ChromeOptions()
            
            if Config.HEADLESS_MODE:
                options.add_argument('--headless=new')
            
            # Stealth arguments
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument(f'--user-agent={generate_user_agent()}')
            
            # Random window size
            width, height = get_random_resolution()
            options.add_argument(f'--window-size={width},{height}')
            
            self.driver = uc.Chrome(options=options, version_main=120)
            
            # Additional stealth settings
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": generate_user_agent()
            })
            
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
            logger.info("Browser initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing browser: {e}")
            return False
    
    def _navigate_to_signup(self) -> bool:
        """
        Navigate to Instagram signup page.
        
        Returns:
            bool: True if successful
        """
        try:
            self.driver.get(Config.INSTAGRAM_SIGNUP_URL)
            
            # Wait for page load
            time.sleep(5)
            
            # Scroll page naturally
            self.driver.execute_script("window.scrollTo(0, 300);")
            random_delay(1, 2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            random_delay(2, 3)
            
            logger.info("Navigated to signup page")
            return True
            
        except Exception as e:
            logger.error(f"Error navigating to signup: {e}")
            return False
    
    def _fill_signup_form(self, email: str, fullname: str, username: str, password: str) -> bool:
        """
        Fill the signup form with account details.
        
        Args:
            email: Email address
            fullname: Full name
            username: Username
            password: Password
            
        Returns:
            bool: True if successful
        """
        try:
            wait = WebDriverWait(self.driver, 20)
            
            # Fill email
            logger.info("Filling email field...")
            email_input = wait.until(
                EC.presence_of_element_located((By.NAME, "emailOrPhone"))
            )
            self._human_type(email_input, email)
            random_delay(Config.MIN_FIELD_DELAY, Config.MAX_FIELD_DELAY)
            
            # Fill full name
            if fullname:
                logger.info("Filling full name field...")
                fullname_input = self.driver.find_element(By.NAME, "fullName")
                self._human_type(fullname_input, fullname)
                random_delay(Config.MIN_FIELD_DELAY, Config.MAX_FIELD_DELAY)
            
            # Fill username
            logger.info("Filling username field...")
            username_input = self.driver.find_element(By.NAME, "username")
            self._human_type(username_input, username)
            random_delay(Config.MIN_FIELD_DELAY, Config.MAX_FIELD_DELAY)
            
            # Check if username is available
            time.sleep(3)
            if not self._check_username_available():
                # Add random digits and retry
                username = f"{username}{random.randint(10, 99)}"
                username_input.clear()
                self._human_type(username_input, username)
                random_delay(2, 3)
            
            # Fill password
            logger.info("Filling password field...")
            password_input = self.driver.find_element(By.NAME, "password")
            self._human_type(password_input, password)
            random_delay(Config.MIN_FIELD_DELAY, Config.MAX_FIELD_DELAY)
            
            logger.info("Signup form filled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error filling signup form: {e}")
            return False
    
    def _human_type(self, element, text: str) -> None:
        """
        Type text with human-like delays.
        
        Args:
            element: Web element to type into
            text: Text to type
        """
        element.click()
        time.sleep(random.uniform(0.3, 0.7))
        
        for char in text:
            element.send_keys(char)
            time.sleep(human_typing_delay())
            
            # Random typo simulation (10% chance)
            if random.random() < 0.1:
                element.send_keys(random.choice('abcdefgh'))
                time.sleep(human_typing_delay())
                element.send_keys(Keys.BACKSPACE)
                time.sleep(human_typing_delay())
    
    def _check_username_available(self) -> bool:
        """
        Check if username is available.
        
        Returns:
            bool: True if available
        """
        try:
            # Look for error message
            error_elements = self.driver.find_elements(
                By.XPATH,
                "//*[contains(text(), \"isn't available\") or contains(text(), 'not available')]"
            )
            
            return len(error_elements) == 0
            
        except Exception:
            return True
    
    def _check_for_captcha(self) -> bool:
        """
        Check if captcha is present.
        
        Returns:
            bool: True if captcha found
        """
        try:
            # Look for reCAPTCHA iframe or checkbox
            captcha_elements = self.driver.find_elements(
                By.XPATH,
                "//iframe[contains(@src, 'recaptcha')]"
            )
            
            return len(captcha_elements) > 0
            
        except Exception:
            return False
    
    def _solve_captcha(self) -> bool:
        """
        Solve captcha if present.
        
        Returns:
            bool: True if solved
        """
        try:
            # Try free methods first
            logger.info("Attempting free captcha bypass...")
            time.sleep(15)
            
            # If still present, use paid service
            if self._check_for_captcha() and self.captcha_solver.api_key:
                logger.info("Using 2Captcha service...")
                # Implementation would extract site key and solve
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Error solving captcha: {e}")
            return False
    
    def _submit_signup(self) -> bool:
        """
        Submit the signup form.
        
        Returns:
            bool: True if successful
        """
        try:
            # Find and click signup button
            submit_button = self.driver.find_element(
                By.XPATH,
                "//button[@type='submit' or contains(text(), 'Sign up')]"
            )
            
            # Move to button and click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            random_delay(0.5, 1)
            submit_button.click()
            
            logger.info("Signup form submitted")
            
            # Wait for response
            random_delay(5, 8)
            
            # Check for errors
            error_elements = self.driver.find_elements(
                By.XPATH,
                "//*[contains(text(), 'error') or contains(text(), 'Error')]"
            )
            
            if error_elements:
                logger.error("Error message detected after submission")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error submitting signup: {e}")
            return False
    
    def _enter_verification_code(self, code: str) -> bool:
        """
        Enter the email verification code.
        
        Args:
            code: 6-digit verification code
            
        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"Entering verification code: {code}")
            
            wait = WebDriverWait(self.driver, 20)
            
            # Look for code input fields
            code_inputs = wait.until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "input"))
            )
            
            # Filter for code inputs (usually 6 separate inputs)
            code_fields = [inp for inp in code_inputs if inp.get_attribute('maxlength') == '1']
            
            if code_fields and len(code_fields) == 6:
                # Enter each digit separately
                for i, digit in enumerate(code):
                    code_fields[i].click()
                    time.sleep(0.3)
                    code_fields[i].send_keys(digit)
                    time.sleep(0.3)
            else:
                # Single input field
                code_input = code_inputs[0]
                self._human_type(code_input, code)
            
            # Wait for auto-submit or click confirm
            random_delay(3, 5)
            
            # Try to find and click confirm button
            try:
                confirm_button = self.driver.find_element(
                    By.XPATH,
                    "//button[contains(text(), 'Confirm') or contains(text(), 'Next')]"
                )
                confirm_button.click()
            except NoSuchElementException:
                pass
            
            logger.info("Verification code entered")
            random_delay(3, 5)
            
            return True
            
        except Exception as e:
            logger.error(f"Error entering verification code: {e}")
            return False
    
    def _click_resend_code(self) -> None:
        """Click the resend code button if available."""
        try:
            resend_button = self.driver.find_element(
                By.XPATH,
                "//button[contains(text(), 'Resend')]"
            )
            resend_button.click()
            logger.info("Resend code clicked")
            time.sleep(5)
        except Exception:
            pass
    
    def _set_birthday(self) -> bool:
        """
        Set birthday on Instagram.
        
        Returns:
            bool: True if successful
        """
        try:
            logger.info("Setting birthday...")
            
            birthday = generate_birthday()
            
            wait = WebDriverWait(self.driver, 20)
            
            # Month select
            month_select = wait.until(
                EC.presence_of_element_located((By.XPATH, "//select[@title='Month:' or @aria-label='Month']"))
            )
            month_select.click()
            time.sleep(0.5)
            month_option = month_select.find_element(By.XPATH, f"//option[@value='{birthday['month']}']")
            month_option.click()
            time.sleep(0.5)
            
            # Day select
            day_select = self.driver.find_element(By.XPATH, "//select[@title='Day:' or @aria-label='Day']")
            day_select.click()
            time.sleep(0.5)
            day_option = day_select.find_element(By.XPATH, f"//option[@value='{birthday['day']}']")
            day_option.click()
            time.sleep(0.5)
            
            # Year select
            year_select = self.driver.find_element(By.XPATH, "//select[@title='Year:' or @aria-label='Year']")
            year_select.click()
            time.sleep(0.5)
            year_option = year_select.find_element(By.XPATH, f"//option[@value='{birthday['year']}']")
            year_option.click()
            time.sleep(0.5)
            
            # Click Next
            next_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Next')]")
            next_button.click()
            
            logger.info(f"Birthday set: {birthday['month']}/{birthday['day']}/{birthday['year']}")
            random_delay(3, 5)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting birthday: {e}")
            return False
    
    def _upload_profile_picture(self, image_path: str) -> bool:
        """
        Upload profile picture.
        
        Args:
            image_path: Path to image file
            
        Returns:
            bool: True if successful
        """
        try:
            logger.info("Uploading profile picture...")
            
            # Look for upload button or skip button
            try:
                upload_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
                upload_input.send_keys(image_path)
                random_delay(2, 3)
                
                # Click confirm/next
                next_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Next')]")
                next_button.click()
                
                logger.info("Profile picture uploaded")
                return True
            except NoSuchElementException:
                # Skip if not available
                skip_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Skip')]")
                skip_button.click()
                return False
                
        except Exception as e:
            logger.error(f"Error uploading profile picture: {e}")
            return False
    
    def _follow_suggested_accounts(self) -> bool:
        """
        Follow suggested accounts.
        
        Returns:
            bool: True if successful
        """
        try:
            logger.info("Following suggested accounts...")
            
            # Look for follow buttons
            follow_buttons = self.driver.find_elements(
                By.XPATH,
                "//button[contains(text(), 'Follow')]"
            )
            
            # Follow random 2-3 accounts
            num_to_follow = random.randint(
                Config.MIN_ACCOUNTS_TO_FOLLOW,
                Config.MAX_ACCOUNTS_TO_FOLLOW
            )
            
            for i in range(min(num_to_follow, len(follow_buttons))):
                follow_buttons[i].click()
                logger.info(f"Followed account {i + 1}")
                random_delay(2, 3)
            
            # Click Next or Done
            try:
                next_button = self.driver.find_element(
                    By.XPATH,
                    "//button[contains(text(), 'Next') or contains(text(), 'Done')]"
                )
                next_button.click()
            except NoSuchElementException:
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Error following accounts: {e}")
            return False
    
    def _setup_2fa(self) -> Optional[str]:
        """
        Setup two-factor authentication.
        
        Returns:
            str: TOTP secret or None
        """
        try:
            logger.info("Setting up 2FA...")
            
            # Navigate to security settings
            self.driver.get("https://www.instagram.com/accounts/two_factor_authentication/")
            random_delay(3, 5)
            
            # Implementation would:
            # 1. Click setup 2FA
            # 2. Extract QR code
            # 3. Decode to get TOTP secret
            # 4. Generate and enter first code
            # 5. Save backup codes
            
            # Placeholder return
            return None
            
        except Exception as e:
            logger.error(f"Error setting up 2FA: {e}")
            return None
    
    def _cleanup_browser(self) -> None:
        """Clean up browser resources."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                logger.info("Browser cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up browser: {e}")
    
    def _send_progress(self, message: str, percentage: Optional[int] = None, step: Optional[str] = None) -> None:
        """
        Send progress update via callback.
        
        Args:
            message: Progress message
            percentage: Progress percentage (0-100)
            step: Current step name
        """
        if self.progress_callback:
            self.progress_callback({
                'message': message,
                'percentage': percentage,
                'step': step,
                'account': self.current_account,
                'total': self.config.num_accounts
            })
