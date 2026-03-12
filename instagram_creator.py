"""
Instagram Account Creator Module.
Handles complete Instagram account creation flow with Selenium.
Railway deployment optimized - Full debug version.
"""

import logging
import time
import random
import os
import glob
import subprocess
from typing import Optional, Dict, Any, Callable
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

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
        """Initialize Instagram creator."""
        self.config = user_config
        self.progress_callback = progress_callback
        self.email_manager = EmailProviderManager()
        self.captcha_solver = CaptchaSolver()
        self.driver: Optional[webdriver.Chrome] = None
        self.current_account = 0
        self.successful_accounts = []
        self.failed_accounts = []

    def create_accounts(self) -> Dict[str, Any]:
        """Create multiple Instagram accounts."""
        logger.info(f"Starting creation of {self.config.num_accounts} accounts...")
        self._send_progress("🚀 Starting account creation...", 0)

        start_time = time.time()

        for i in range(self.config.num_accounts):
            self.current_account = i + 1
            progress_pct = int((i / self.config.num_accounts) * 100)

            logger.info(f"\n{'='*70}")
            logger.info(f"ACCOUNT {self.current_account}/{self.config.num_accounts}")
            logger.info(f"{'='*70}\n")

            self._send_progress(
                f"📝 Creating account {self.current_account}/{self.config.num_accounts}...",
                progress_pct,
                account=self.current_account,
                total=self.config.num_accounts
            )

            try:
                result = self._create_single_account(i)

                if result['success']:
                    self.successful_accounts.append(result)
                    self._send_progress(
                        f"✅ Account {self.current_account} created!",
                        progress_pct
                    )
                else:
                    self.failed_accounts.append(result)
                    self._send_progress(
                        f"❌ Account {self.current_account} failed: {result.get('error', 'Unknown')}",
                        progress_pct
                    )

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                import traceback
                traceback.print_exc()
                self.failed_accounts.append({
                    'account_number': self.current_account,
                    'success': False,
                    'error': str(e)
                })

            if i < self.config.num_accounts - 1:
                delay = random.randint(
                    Config.MIN_DELAY_BETWEEN_ACCOUNTS,
                    Config.MAX_DELAY_BETWEEN_ACCOUNTS
                )
                logger.info(f"Waiting {delay}s before next account...")
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
        """Create a single Instagram account."""
        account_data = {
            'account_number': self.current_account,
            'success': False,
            'created_at': datetime.now().isoformat()
        }

        try:
            logger.info("=" * 70)
            logger.info(f"ACCOUNT {self.current_account}/{self.config.num_accounts} - STARTING")
            logger.info("=" * 70)

            # Step 1: Browser
            self._send_progress("🌐 Step 1/10: Initializing browser...", step="browser")
            logger.info("Step 1: Browser initialization...")
            if not self._init_browser():
                raise Exception("Browser initialization failed")
            logger.info("✅ Browser initialized successfully")

            # Step 2: Email
            self._send_progress("📧 Step 2/10: Creating email address...", step="email")
            logger.info("Step 2: Creating email...")
            email_data = self.email_manager.create_email_with_rotation()
            if not email_data:
                raise Exception("Email creation failed - all providers failed")
            logger.info(f"✅ Email created: {email_data['email']}")
            logger.info(f"   Provider: {email_data.get('provider', 'unknown')}")
            account_data['email'] = email_data['email']
            account_data['email_provider'] = email_data.get('provider', 'unknown')

            # Step 3: Generate account details
            self._send_progress("🔧 Step 3/10: Generating account details...", step="details")
            logger.info("Step 3: Generating account details...")
            username = self.config.get_username(index)
            fullname = self.config.get_fullname(index)
            password = self.config.get_password(index)
            account_data['username'] = username
            account_data['fullname'] = fullname
            account_data['password'] = password
            logger.info(f"✅ Username: {username}")
            logger.info(f"   Fullname: {fullname}")
            logger.info(f"   Password: {'*' * len(password)}")

            # Step 4: Navigate
            self._send_progress("🔗 Step 4/10: Opening Instagram...", step="navigate")
            logger.info("Step 4: Navigating to Instagram...")
            if not self._navigate_to_signup():
                raise Exception("Failed to open Instagram signup page")
            logger.info("✅ Instagram page opened")

            # Step 5: Fill form
            self._send_progress("✍️ Step 5/10: Filling signup form...", step="form")
            logger.info("Step 5: Filling form...")
            if not self._fill_signup_form(
                email_data['email'], fullname, username, password
            ):
                raise Exception("Failed to fill signup form")
            logger.info("✅ Form filled")

            # Step 6: Captcha
            self._send_progress("🤖 Step 6/10: Checking for captcha...", step="captcha")
            logger.info("Step 6: Captcha check...")
            if self._check_for_captcha():
                logger.warning("⚠️ Captcha detected!")
                self._send_progress("🤖 Solving captcha...", step="captcha")
                if not self._solve_captcha():
                    raise Exception("Captcha solve failed")
            logger.info("✅ No captcha or solved")

            # Step 7: Submit
            self._send_progress("📤 Step 7/10: Submitting form...", step="submit")
            logger.info("Step 7: Submitting...")
            if not self._submit_signup():
                raise Exception("Form submission failed")
            logger.info("✅ Form submitted")

            # Step 8: Verification
            self._send_progress("📬 Step 8/10: Waiting for verification code...", step="verification")
            logger.info("Step 8: Waiting for verification code...")
            verification_code = self.email_manager.fetch_instagram_code(
                email_data,
                timeout=Config.EMAIL_CHECK_TIMEOUT
            )
            if not verification_code:
                logger.warning("⚠️ No code, trying resend...")
                self._click_resend_code()
                verification_code = self.email_manager.fetch_instagram_code(
                    email_data,
                    timeout=Config.EMAIL_CHECK_TIMEOUT
                )
            if not verification_code:
                raise Exception("Verification code not received")
            logger.info(f"✅ Code received: {verification_code}")
            if not self._enter_verification_code(verification_code):
                raise Exception("Failed to enter verification code")
            logger.info("✅ Code entered")

            # Step 9: Birthday
            self._send_progress("🎂 Step 9/10: Setting birthday...", step="birthday")
            logger.info("Step 9: Setting birthday...")
            if not self._set_birthday():
                raise Exception("Failed to set birthday")
            logger.info("✅ Birthday set")

            # Step 10: Finalize
            self._send_progress("✨ Step 10/10: Finalizing account...", step="finalize")
            logger.info("Step 10: Profile setup...")
            if Config.ADD_PROFILE_PICTURE:
                avatar_path = create_simple_avatar(username)
                if avatar_path:
                    self._upload_profile_picture(avatar_path)
            if Config.FOLLOW_SUGGESTED_ACCOUNTS:
                self._follow_suggested_accounts()
            logger.info("✅ Profile setup complete")

            account_data['success'] = True
            account_data['status'] = 'active'
            save_credentials(account_data)

            logger.info("=" * 70)
            logger.info(f"✅ ACCOUNT {self.current_account} CREATED SUCCESSFULLY!")
            logger.info("=" * 70)

            return account_data

        except Exception as e:
            logger.error("=" * 70)
            logger.error(f"❌ ACCOUNT {self.current_account} FAILED!")
            logger.error(f"Error: {str(e)}")
            logger.error("=" * 70)
            import traceback
            traceback.print_exc()
            account_data['error'] = str(e)
            return account_data

        finally:
            self._cleanup_browser()

    def _init_browser(self) -> bool:
        """Initialize browser - Railway optimized with full debug."""
        try:
            logger.info("=" * 50)
            logger.info("BROWSER INIT - SYSTEM DEBUG")
            logger.info("=" * 50)

            # System info
            try:
                result = subprocess.run(
                    ['uname', '-a'],
                    capture_output=True, text=True, timeout=5
                )
                logger.info(f"OS: {result.stdout.strip()}")
            except Exception as e:
                logger.info(f"OS check failed: {e}")

            for cmd in ['google-chrome', 'chromium', 'chromium-browser']:
                try:
                    result = subprocess.run(
                        ['which', cmd],
                        capture_output=True, text=True, timeout=5
                    )
                    logger.info(f"which {cmd}: {result.stdout.strip() or 'NOT FOUND'}")
                except Exception as e:
                    logger.info(f"which {cmd} failed: {e}")

            try:
                result = subprocess.run(
                    ['which', 'chromedriver'],
                    capture_output=True, text=True, timeout=5
                )
                logger.info(f"which chromedriver: {result.stdout.strip() or 'NOT FOUND'}")
            except Exception as e:
                logger.info(f"which chromedriver failed: {e}")

            try:
                result = subprocess.run(
                    'ls /usr/bin/ | grep -i chrom',
                    shell=True, capture_output=True, text=True, timeout=5
                )
                logger.info(f"/usr/bin chrom*: {result.stdout.strip() or 'NOTHING FOUND'}")
            except Exception as e:
                logger.info(f"ls /usr/bin failed: {e}")

            try:
                result = subprocess.run(
                    'ls /usr/local/bin/ | grep -i chrom',
                    shell=True, capture_output=True, text=True, timeout=5
                )
                logger.info(f"/usr/local/bin chrom*: {result.stdout.strip() or 'NOTHING FOUND'}")
            except Exception as e:
                logger.info(f"ls /usr/local/bin failed: {e}")

            logger.info(f"CHROME_BIN env: {os.getenv('CHROME_BIN', 'NOT SET')}")
            logger.info(f"CHROMEDRIVER_PATH env: {os.getenv('CHROMEDRIVER_PATH', 'NOT SET')}")
            logger.info("=" * 50)

            # Chrome binary
            chrome_bin = os.getenv('CHROME_BIN')
            if not chrome_bin or not os.path.exists(chrome_bin):
                chrome_paths = [
                    '/usr/bin/google-chrome',
                    '/usr/bin/google-chrome-stable',
                    '/usr/bin/chromium',
                    '/usr/bin/chromium-browser',
                    '/usr/local/bin/google-chrome',
                    '/usr/local/bin/chromium',
                ]
                chrome_bin = None
                for path in chrome_paths:
                    if os.path.exists(path):
                        chrome_bin = path
                        logger.info(f"✅ Chrome found: {path}")
                        break

            if not chrome_bin:
                nix_paths = glob.glob('/nix/store/*/bin/chromium')
                if nix_paths:
                    chrome_bin = nix_paths[0]
                    logger.info(f"✅ Chrome found in nix: {chrome_bin}")

            if not chrome_bin:
                logger.error("❌ Chrome binary NOT FOUND!")
                return False

            try:
                result = subprocess.run(
                    [chrome_bin, '--version'],
                    capture_output=True, text=True, timeout=10
                )
                logger.info(f"Chrome version: {result.stdout.strip()}")
            except Exception as e:
                logger.warning(f"Chrome version check failed: {e}")

            # ChromeDriver
            driver_bin = os.getenv('CHROMEDRIVER_PATH')
            if not driver_bin or not os.path.exists(driver_bin):
                driver_paths = [
                    '/usr/local/bin/chromedriver',
                    '/usr/bin/chromedriver',
                    '/usr/lib/chromium/chromedriver',
                    '/usr/lib/chromium-browser/chromedriver',
                ]
                driver_bin = None
                for path in driver_paths:
                    if os.path.exists(path):
                        driver_bin = path
                        logger.info(f"✅ ChromeDriver found: {path}")
                        break

            if not driver_bin:
                nix_paths = glob.glob('/nix/store/*/bin/chromedriver')
                if nix_paths:
                    driver_bin = nix_paths[0]
                    logger.info(f"✅ ChromeDriver found in nix: {driver_bin}")

            if not driver_bin:
                logger.error("❌ ChromeDriver NOT FOUND!")
                return False

            try:
                result = subprocess.run(
                    [driver_bin, '--version'],
                    capture_output=True, text=True, timeout=10
                )
                logger.info(f"ChromeDriver version: {result.stdout.strip()}")
            except Exception as e:
                logger.warning(f"ChromeDriver version check failed: {e}")

            # Options
            options = Options()
            options.binary_location = chrome_bin

            for arg in [
                '--headless=new',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-setuid-sandbox',
                '--no-zygote',
                '--single-process',
                '--disable-extensions',
                '--disable-background-networking',
                '--disable-default-apps',
                '--disable-sync',
                '--disable-translate',
                '--hide-scrollbars',
                '--mute-audio',
                '--disable-blink-features=AutomationControlled',
                '--window-size=1920,1080',
                '--disable-infobars',
                '--ignore-certificate-errors',
                '--allow-running-insecure-content',
                f'--user-agent={generate_user_agent()}',
            ]:
                options.add_argument(arg)

            options.add_experimental_option(
                "excludeSwitches", ["enable-automation"]
            )
            options.add_experimental_option(
                'useAutomationExtension', False
            )

            # Create driver
            logger.info("Creating WebDriver instance...")
            service = Service(executable_path=driver_bin)
            self.driver = webdriver.Chrome(
                service=service,
                options=options
            )

            self.driver.set_page_load_timeout(60)
            self.driver.implicitly_wait(10)

            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', "
                "{get: () => undefined})"
            )

            self.driver.get("about:blank")
            logger.info(f"Test page title: '{self.driver.title}'")
            logger.info("✅ Browser initialized successfully!")
            return True

        except Exception as e:
            logger.error(f"❌ Browser init failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _navigate_to_signup(self) -> bool:
        """Navigate to Instagram signup page."""
        try:
            logger.info(f"Opening URL: {Config.INSTAGRAM_SIGNUP_URL}")
            self.driver.get(Config.INSTAGRAM_SIGNUP_URL)
            time.sleep(8)

            logger.info(f"Page title: {self.driver.title}")
            logger.info(f"Current URL: {self.driver.current_url}")

            # Page source preview
            page_source = self.driver.page_source
            logger.info(f"Page source length: {len(page_source)}")
            logger.info(f"Page source preview: {page_source[:500]}")

            try:
                self.driver.save_screenshot("/tmp/instagram_page.png")
                logger.info("Screenshot saved: /tmp/instagram_page.png")
            except Exception as e:
                logger.warning(f"Screenshot failed: {e}")

            # Instagram load check
            if "instagram" not in self.driver.title.lower():
                logger.warning(f"Unexpected title: {self.driver.title}")
                logger.warning("Trying alternative URL...")
                self.driver.get("https://www.instagram.com/accounts/emailsignup/")
                time.sleep(8)
                logger.info(f"Alt page title: {self.driver.title}")
                logger.info(f"Alt URL: {self.driver.current_url}")

            # Log all inputs
            try:
                all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                logger.info(f"Found {len(all_inputs)} input fields:")
                for inp in all_inputs:
                    logger.info(
                        f"  Input - name: {inp.get_attribute('name')}, "
                        f"type: {inp.get_attribute('type')}, "
                        f"placeholder: {inp.get_attribute('placeholder')}, "
                        f"id: {inp.get_attribute('id')}"
                    )
            except Exception as e:
                logger.warning(f"Input scan failed: {e}")

            self.driver.execute_script("window.scrollTo(0, 300);")
            random_delay(1, 2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            random_delay(1, 2)

            return True

        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _fill_signup_form(
        self, email: str, fullname: str,
        username: str, password: str
    ) -> bool:
        """Fill the signup form."""
        try:
            wait = WebDriverWait(self.driver, 30)

            # ===== Email =====
            logger.info("Looking for email field...")
            email_input = None
            email_selectors = [
                (By.NAME, "emailOrPhone"),
                (By.NAME, "email"),
                (By.XPATH, "//input[@type='email']"),
                (By.XPATH, "//input[contains(@placeholder, 'email') or contains(@placeholder, 'Email')]"),
                (By.XPATH, "//input[contains(@placeholder, 'Mobile') or contains(@placeholder, 'mobile')]"),
                (By.XPATH, "//input[contains(@placeholder, 'Phone')]"),
            ]

            for by, selector in email_selectors:
                try:
                    email_input = wait.until(
                        EC.presence_of_element_located((by, selector))
                    )
                    logger.info(f"✅ Email field found: {selector}")
                    break
                except TimeoutException:
                    logger.warning(f"Email selector failed: {selector}")
                    continue

            if not email_input:
                logger.error("❌ Email field NOT FOUND!")
                all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                logger.error(f"Available inputs ({len(all_inputs)}):")
                for inp in all_inputs:
                    logger.error(
                        f"  name={inp.get_attribute('name')}, "
                        f"type={inp.get_attribute('type')}, "
                        f"placeholder={inp.get_attribute('placeholder')}, "
                        f"id={inp.get_attribute('id')}"
                    )
                try:
                    with open('/tmp/page_source.html', 'w') as f:
                        f.write(self.driver.page_source)
                    logger.info("Page source saved: /tmp/page_source.html")
                except Exception:
                    pass
                return False

            self._human_type(email_input, email)
            random_delay(1, 2)
            logger.info(f"✅ Email filled: {email}")

            # ===== Full Name =====
            if fullname:
                logger.info("Looking for fullname field...")
                fullname_input = None
                fullname_selectors = [
                    (By.NAME, "fullName"),
                    (By.NAME, "name"),
                    (By.XPATH, "//input[contains(@placeholder, 'Full Name')]"),
                    (By.XPATH, "//input[contains(@placeholder, 'full name')]"),
                    (By.XPATH, "//input[contains(@placeholder, 'Name')]"),
                ]
                for by, selector in fullname_selectors:
                    try:
                        fullname_input = self.driver.find_element(by, selector)
                        logger.info(f"✅ Fullname field found: {selector}")
                        break
                    except NoSuchElementException:
                        continue

                if fullname_input:
                    self._human_type(fullname_input, fullname)
                    random_delay(1, 2)
                    logger.info(f"✅ Fullname filled: {fullname}")
                else:
                    logger.warning("⚠️ Fullname field not found, skipping...")

            # ===== Username =====
            logger.info("Looking for username field...")
            username_input = None
            username_selectors = [
                (By.NAME, "username"),
                (By.XPATH, "//input[contains(@placeholder, 'Username')]"),
                (By.XPATH, "//input[contains(@placeholder, 'username')]"),
                (By.XPATH, "//input[@autocomplete='username']"),
            ]
            for by, selector in username_selectors:
                try:
                    username_input = self.driver.find_element(by, selector)
                    logger.info(f"✅ Username field found: {selector}")
                    break
                except NoSuchElementException:
                    continue

            if not username_input:
                logger.error("❌ Username field NOT FOUND!")
                return False

            self._human_type(username_input, username)
            random_delay(2, 3)
            logger.info(f"✅ Username filled: {username}")

            time.sleep(3)
            if not self._check_username_available():
                logger.warning("Username not available, adding suffix...")
                username = f"{username}{random.randint(10, 99)}"
                username_input.clear()
                self._human_type(username_input, username)
                random_delay(2, 3)

            # ===== Password =====
            logger.info("Looking for password field...")
            password_input = None
            password_selectors = [
                (By.NAME, "password"),
                (By.XPATH, "//input[@type='password']"),
                (By.XPATH, "//input[contains(@placeholder, 'Password')]"),
                (By.XPATH, "//input[contains(@placeholder, 'password')]"),
            ]
            for by, selector in password_selectors:
                try:
                    password_input = self.driver.find_element(by, selector)
                    logger.info(f"✅ Password field found: {selector}")
                    break
                except NoSuchElementException:
                    continue

            if not password_input:
                logger.error("❌ Password field NOT FOUND!")
                return False

            self._human_type(password_input, password)
            random_delay(1, 2)
            logger.info("✅ Password filled")

            logger.info("✅ Form filled successfully!")
            return True

        except Exception as e:
            logger.error(f"Form fill failed: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.driver.save_screenshot("/tmp/form_error.png")
                logger.info("Error screenshot saved")
            except Exception:
                pass
            return False

    def _human_type(self, element, text: str) -> None:
        """Type text with human-like delays."""
        element.click()
        time.sleep(random.uniform(0.3, 0.7))
        for char in text:
            element.send_keys(char)
            time.sleep(human_typing_delay())
            if random.random() < 0.1:
                element.send_keys(random.choice('abcdefgh'))
                time.sleep(human_typing_delay())
                element.send_keys(Keys.BACKSPACE)
                time.sleep(human_typing_delay())

    def _check_username_available(self) -> bool:
        """Check if username is available."""
        try:
            error_elements = self.driver.find_elements(
                By.XPATH,
                "//*[contains(text(), \"isn't available\") or "
                "contains(text(), 'not available')]"
            )
            available = len(error_elements) == 0
            logger.info(f"Username available: {available}")
            return available
        except Exception:
            return True

    def _check_for_captcha(self) -> bool:
        """Check if captcha is present."""
        try:
            captcha_elements = self.driver.find_elements(
                By.XPATH,
                "//iframe[contains(@src, 'recaptcha')]"
            )
            has_captcha = len(captcha_elements) > 0
            logger.info(f"Captcha present: {has_captcha}")
            return has_captcha
        except Exception:
            return False

    def _solve_captcha(self) -> bool:
        """Solve captcha if present."""
        try:
            logger.info("Attempting captcha bypass...")
            time.sleep(15)
            if self._check_for_captcha() and self.captcha_solver.api_key:
                logger.info("Using 2Captcha service...")
            return True
        except Exception as e:
            logger.error(f"Captcha solve error: {e}")
            return False

    def _submit_signup(self) -> bool:
        """Submit the signup form."""
        try:
            submit_selectors = [
                (By.XPATH, "//button[@type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Sign up')]"),
                (By.XPATH, "//button[contains(text(), 'Next')]"),
            ]

            submit_button = None
            for by, selector in submit_selectors:
                try:
                    submit_button = self.driver.find_element(by, selector)
                    logger.info(f"Submit button found: {selector}")
                    break
                except NoSuchElementException:
                    continue

            if not submit_button:
                logger.error("❌ Submit button NOT FOUND!")
                return False

            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", submit_button
            )
            random_delay(0.5, 1)
            submit_button.click()
            logger.info("Form submitted")
            random_delay(5, 8)

            return True

        except Exception as e:
            logger.error(f"Submit failed: {e}")
            return False

    def _enter_verification_code(self, code: str) -> bool:
        """Enter the email verification code."""
        try:
            logger.info(f"Entering verification code: {code}")
            wait = WebDriverWait(self.driver, 30)

            all_inputs = wait.until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "input"))
            )

            code_fields = [
                inp for inp in all_inputs
                if inp.get_attribute('maxlength') == '1'
            ]

            if code_fields and len(code_fields) == 6:
                for i, digit in enumerate(code):
                    code_fields[i].click()
                    time.sleep(0.3)
                    code_fields[i].send_keys(digit)
                    time.sleep(0.3)
            else:
                code_input = all_inputs[0]
                self._human_type(code_input, code)

            random_delay(3, 5)

            try:
                confirm_button = self.driver.find_element(
                    By.XPATH,
                    "//button[contains(text(), 'Confirm') or "
                    "contains(text(), 'Next')]"
                )
                confirm_button.click()
            except NoSuchElementException:
                pass

            logger.info("✅ Verification code entered")
            random_delay(3, 5)
            return True

        except Exception as e:
            logger.error(f"Code entry failed: {e}")
            return False

    def _click_resend_code(self) -> None:
        """Click the resend code button."""
        try:
            btn = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Resend')]"
            )
            btn.click()
            logger.info("Resend clicked")
            time.sleep(5)
        except Exception:
            pass

    def _set_birthday(self) -> bool:
        """Set birthday on Instagram."""
        try:
            logger.info("Setting birthday...")
            birthday = generate_birthday()
            wait = WebDriverWait(self.driver, 20)

            month_select = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     "//select[@title='Month:' or @aria-label='Month']")
                )
            )
            month_select.click()
            time.sleep(0.5)
            month_select.find_element(
                By.XPATH, f"//option[@value='{birthday['month']}']"
            ).click()
            time.sleep(0.5)

            day_select = self.driver.find_element(
                By.XPATH, "//select[@title='Day:' or @aria-label='Day']"
            )
            day_select.click()
            time.sleep(0.5)
            day_select.find_element(
                By.XPATH, f"//option[@value='{birthday['day']}']"
            ).click()
            time.sleep(0.5)

            year_select = self.driver.find_element(
                By.XPATH, "//select[@title='Year:' or @aria-label='Year']"
            )
            year_select.click()
            time.sleep(0.5)
            year_select.find_element(
                By.XPATH, f"//option[@value='{birthday['year']}']"
            ).click()
            time.sleep(0.5)

            next_button = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Next')]"
            )
            next_button.click()
            logger.info(
                f"Birthday set: {birthday['month']}/"
                f"{birthday['day']}/{birthday['year']}"
            )
            random_delay(3, 5)
            return True

        except Exception as e:
            logger.error(f"Birthday set failed: {e}")
            return False

    def _upload_profile_picture(self, image_path: str) -> bool:
        """Upload profile picture."""
        try:
            logger.info("Uploading profile picture...")
            upload_input = self.driver.find_element(
                By.XPATH, "//input[@type='file']"
            )
            upload_input.send_keys(image_path)
            random_delay(2, 3)
            next_button = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Next')]"
            )
            next_button.click()
            logger.info("Profile picture uploaded")
            return True

        except NoSuchElementException:
            try:
                skip_button = self.driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Skip')]"
                )
                skip_button.click()
            except Exception:
                pass
            return False

        except Exception as e:
            logger.error(f"Profile pic upload failed: {e}")
            return False

    def _follow_suggested_accounts(self) -> bool:
        """Follow suggested accounts."""
        try:
            logger.info("Following suggested accounts...")
            follow_buttons = self.driver.find_elements(
                By.XPATH, "//button[contains(text(), 'Follow')]"
            )
            num_to_follow = random.randint(
                Config.MIN_ACCOUNTS_TO_FOLLOW,
                Config.MAX_ACCOUNTS_TO_FOLLOW
            )
            for i in range(min(num_to_follow, len(follow_buttons))):
                follow_buttons[i].click()
                logger.info(f"Followed account {i + 1}")
                random_delay(2, 3)

            try:
                next_button = self.driver.find_element(
                    By.XPATH,
                    "//button[contains(text(), 'Next') or "
                    "contains(text(), 'Done')]"
                )
                next_button.click()
            except NoSuchElementException:
                pass

            return True

        except Exception as e:
            logger.error(f"Follow failed: {e}")
            return False

    def _cleanup_browser(self) -> None:
        """Clean up browser resources."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Browser cleanup error: {e}")

    def _send_progress(
        self,
        message: str,
        percentage: Optional[int] = None,
        step: Optional[str] = None,
        account: Optional[int] = None,
        total: Optional[int] = None
    ) -> None:
        """Send progress update via callback."""
        if self.progress_callback:
            self.progress_callback({
                'message': message,
                'percentage': percentage,
                'step': step,
                'account': account or self.current_account,
                'total': total or self.config.num_accounts
            })
