"""
Instagram Account Creator Module.
Playwright version - Railway optimized.
"""

import logging
import time
import random
import os
import asyncio
from typing import Optional, Dict, Any, Callable
from datetime import datetime

from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PlaywrightTimeout

from config import Config
from user_config import UserConfig
from email_providers import EmailProviderManager
from captcha_solver import CaptchaSolver
from utils import (
    random_delay, human_typing_delay, generate_birthday,
    create_simple_avatar, save_credentials, generate_user_agent
)

logger = logging.getLogger(__name__)


class InstagramCreator:
    """Handles Instagram account creation - Playwright version."""

    def __init__(
        self,
        user_config: UserConfig,
        progress_callback: Optional[Callable] = None
    ):
        self.config = user_config
        self.progress_callback = progress_callback
        self.email_manager = EmailProviderManager()
        self.captcha_solver = CaptchaSolver()
        self.browser: Optional[Browser] = None
        self.playwright = None
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

            logger.info(f"\n{'='*60}")
            logger.info(f"ACCOUNT {self.current_account}/{self.config.num_accounts}")
            logger.info(f"{'='*60}\n")

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
                        f"❌ Account {self.current_account} failed: "
                        f"{result.get('error', 'Unknown')}",
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
                logger.info(f"Waiting {delay}s before next...")
                time.sleep(delay)

        elapsed_time = int(time.time() - start_time)

        summary = {
            'total': self.config.num_accounts,
            'successful': len(self.successful_accounts),
            'failed': len(self.failed_accounts),
            'elapsed_time': elapsed_time,
            'accounts': self.successful_accounts
        }

        self._send_progress("✨ All done!", 100)
        return summary

    def _create_single_account(self, index: int) -> Dict[str, Any]:
        """Create single Instagram account."""
        account_data = {
            'account_number': self.current_account,
            'success': False,
            'created_at': datetime.now().isoformat()
        }

        try:
            # Step 1: Browser
            self._send_progress("🌐 Step 1/10: Initializing browser...", step="browser")
            logger.info("Step 1: Browser init...")
            if not self._init_browser():
                raise Exception("Browser initialization failed")
            logger.info("✅ Browser ready")

            # Step 2: Email
            self._send_progress("📧 Step 2/10: Creating email...", step="email")
            logger.info("Step 2: Email creation...")
            email_data = self.email_manager.create_email_with_rotation()
            if not email_data:
                raise Exception("Email creation failed")
            logger.info(f"✅ Email: {email_data['email']}")
            account_data['email'] = email_data['email']
            account_data['email_provider'] = email_data.get('provider', 'unknown')

            # Step 3: Details
            self._send_progress("🔧 Step 3/10: Generating details...", step="details")
            username = self.config.get_username(index)
            fullname = self.config.get_fullname(index)
            password = self.config.get_password(index)
            account_data['username'] = username
            account_data['fullname'] = fullname
            account_data['password'] = password
            logger.info(f"✅ Username: {username} | Fullname: {fullname}")

            # Step 4: Open Instagram
            self._send_progress("🔗 Step 4/10: Opening Instagram...", step="navigate")
            logger.info("Step 4: Opening Instagram...")
            page = self._new_page()
            if not self._navigate_to_signup(page):
                raise Exception("Failed to open Instagram")
            logger.info("✅ Instagram opened")

            # Step 5: Fill form
            self._send_progress("✍️ Step 5/10: Filling signup form...", step="form")
            logger.info("Step 5: Filling form...")
            if not self._fill_signup_form(
                page, email_data['email'], fullname, username, password
            ):
                raise Exception("Failed to fill signup form")
            logger.info("✅ Form filled")

            # Step 6: Submit
            self._send_progress("📤 Step 6/10: Submitting form...", step="submit")
            logger.info("Step 6: Submitting...")
            if not self._submit_signup(page):
                raise Exception("Form submission failed")
            logger.info("✅ Submitted")

            # Step 7: Verification
            self._send_progress(
                "📬 Step 7/10: Waiting for verification code...",
                step="verification"
            )
            logger.info("Step 7: Waiting for code...")
            verification_code = self.email_manager.fetch_instagram_code(
                email_data,
                timeout=Config.EMAIL_CHECK_TIMEOUT
            )
            if not verification_code:
                logger.warning("No code, trying resend...")
                self._click_resend_code(page)
                verification_code = self.email_manager.fetch_instagram_code(
                    email_data,
                    timeout=Config.EMAIL_CHECK_TIMEOUT
                )
            if not verification_code:
                raise Exception("Verification code not received")
            logger.info(f"✅ Code: {verification_code}")
            if not self._enter_verification_code(page, verification_code):
                raise Exception("Failed to enter verification code")

            # Step 8: Birthday
            self._send_progress("🎂 Step 8/10: Setting birthday...", step="birthday")
            logger.info("Step 8: Birthday...")
            if not self._set_birthday(page):
                raise Exception("Failed to set birthday")
            logger.info("✅ Birthday set")

            # Step 9: Profile picture
            self._send_progress("🖼 Step 9/10: Profile picture...", step="picture")
            if Config.ADD_PROFILE_PICTURE:
                avatar_path = create_simple_avatar(username)
                if avatar_path:
                    self._upload_profile_picture(page, avatar_path)

            # Step 10: Follow
            self._send_progress("✨ Step 10/10: Finalizing...", step="finalize")
            if Config.FOLLOW_SUGGESTED_ACCOUNTS:
                self._follow_suggested_accounts(page)

            account_data['success'] = True
            account_data['status'] = 'active'
            save_credentials(account_data)

            logger.info(f"✅ ACCOUNT {self.current_account} CREATED!")
            return account_data

        except Exception as e:
            logger.error(f"❌ ACCOUNT {self.current_account} FAILED: {e}")
            import traceback
            traceback.print_exc()
            account_data['error'] = str(e)
            return account_data

        finally:
            self._cleanup_browser()

    def _init_browser(self) -> bool:
        """Initialize Playwright browser."""
        try:
            logger.info("Starting Playwright...")
            self.playwright = sync_playwright().start()

            launch_args = [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-zygote',
                '--single-process',
                '--disable-extensions',
                '--disable-blink-features=AutomationControlled',
            ]

            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=launch_args,
                slow_mo=50
            )

            logger.info("✅ Playwright browser started!")
            return True

        except Exception as e:
            logger.error(f"❌ Browser init failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _new_page(self) -> Page:
        """Create new browser page with stealth settings."""
        context = self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent=generate_user_agent(),
            locale='en-US',
            timezone_id='America/New_York',
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
            }
        )

        # Stealth script
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            window.chrome = {
                runtime: {},
            };
        """)

        page = context.new_page()
        return page

    def _navigate_to_signup(self, page: Page) -> bool:
        """Navigate to Instagram signup."""
        try:
            url = "https://www.instagram.com/accounts/emailsignup/"
            logger.info(f"Opening: {url}")

            page.goto(url, wait_until='networkidle', timeout=60000)
            time.sleep(3)

            logger.info(f"Title: {page.title()}")
            logger.info(f"URL: {page.url}")

            # Screenshot
            try:
                page.screenshot(path='/tmp/instagram_signup.png')
                logger.info("Screenshot saved")
            except Exception as e:
                logger.warning(f"Screenshot failed: {e}")

            # Log all inputs
            try:
                inputs = page.query_selector_all('input')
                logger.info(f"Found {len(inputs)} inputs:")
                for inp in inputs:
                    logger.info(
                        f"  name={inp.get_attribute('name')}, "
                        f"type={inp.get_attribute('type')}, "
                        f"placeholder={inp.get_attribute('placeholder')}"
                    )
            except Exception as e:
                logger.warning(f"Input scan failed: {e}")

            return True

        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _fill_signup_form(
        self, page: Page,
        email: str, fullname: str,
        username: str, password: str
    ) -> bool:
        """Fill signup form."""
        try:
            # Email
            logger.info("Filling email...")
            email_selectors = [
                'input[name="emailOrPhone"]',
                'input[name="email"]',
                'input[type="email"]',
                'input[placeholder*="Email"]',
                'input[placeholder*="Mobile"]',
                'input[placeholder*="Phone"]',
            ]

            email_filled = False
            for selector in email_selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    page.click(selector)
                    time.sleep(0.5)
                    self._playwright_type(page, selector, email)
                    logger.info(f"✅ Email filled with: {selector}")
                    email_filled = True
                    break
                except PlaywrightTimeout:
                    logger.warning(f"Email selector timeout: {selector}")
                    continue
                except Exception as e:
                    logger.warning(f"Email selector failed {selector}: {e}")
                    continue

            if not email_filled:
                logger.error("❌ Could not fill email!")
                # Log page state
                inputs = page.query_selector_all('input')
                logger.error(f"Available inputs: {len(inputs)}")
                for inp in inputs:
                    logger.error(
                        f"  name={inp.get_attribute('name')}, "
                        f"placeholder={inp.get_attribute('placeholder')}"
                    )
                return False

            time.sleep(1)

            # Full name
            if fullname:
                logger.info("Filling fullname...")
                fullname_selectors = [
                    'input[name="fullName"]',
                    'input[name="name"]',
                    'input[placeholder*="Full Name"]',
                    'input[placeholder*="Name"]',
                ]
                for selector in fullname_selectors:
                    try:
                        element = page.query_selector(selector)
                        if element:
                            page.click(selector)
                            time.sleep(0.5)
                            self._playwright_type(page, selector, fullname)
                            logger.info(f"✅ Fullname filled: {selector}")
                            break
                    except Exception:
                        continue
                time.sleep(1)

            # Username
            logger.info("Filling username...")
            username_selectors = [
                'input[name="username"]',
                'input[placeholder*="Username"]',
                'input[autocomplete="username"]',
            ]

            username_filled = False
            for selector in username_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        page.click(selector)
                        time.sleep(0.5)
                        self._playwright_type(page, selector, username)
                        logger.info(f"✅ Username filled: {selector}")
                        username_filled = True
                        break
                except Exception:
                    continue

            if not username_filled:
                logger.error("❌ Could not fill username!")
                return False

            time.sleep(3)

            # Username availability check
            error_text = page.query_selector(
                'text="This username isn\'t available"'
            )
            if error_text:
                logger.warning("Username taken, adding suffix...")
                username = f"{username}{random.randint(10, 99)}"
                for selector in username_selectors:
                    try:
                        element = page.query_selector(selector)
                        if element:
                            element.triple_click()
                            self._playwright_type(page, selector, username)
                            break
                    except Exception:
                        continue
                time.sleep(2)

            # Password
            logger.info("Filling password...")
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[placeholder*="Password"]',
            ]

            password_filled = False
            for selector in password_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        page.click(selector)
                        time.sleep(0.5)
                        self._playwright_type(page, selector, password)
                        logger.info(f"✅ Password filled: {selector}")
                        password_filled = True
                        break
                except Exception:
                    continue

            if not password_filled:
                logger.error("❌ Could not fill password!")
                return False

            time.sleep(1)
            logger.info("✅ Form filled successfully!")
            return True

        except Exception as e:
            logger.error(f"Form fill failed: {e}")
            import traceback
            traceback.print_exc()
            try:
                page.screenshot(path='/tmp/form_error.png')
            except Exception:
                pass
            return False

    def _playwright_type(self, page: Page, selector: str, text: str) -> None:
        """Type with human-like speed."""
        for char in text:
            page.type(selector, char, delay=random.randint(50, 150))

    def _submit_signup(self, page: Page) -> bool:
        """Submit signup form."""
        try:
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Sign up")',
                'button:has-text("Next")',
            ]

            for selector in submit_selectors:
                try:
                    btn = page.query_selector(selector)
                    if btn:
                        btn.scroll_into_view_if_needed()
                        time.sleep(0.5)
                        btn.click()
                        logger.info(f"✅ Submit clicked: {selector}")
                        time.sleep(5)
                        return True
                except Exception:
                    continue

            logger.error("❌ Submit button not found!")
            return False

        except Exception as e:
            logger.error(f"Submit failed: {e}")
            return False

    def _enter_verification_code(self, page: Page, code: str) -> bool:
        """Enter verification code."""
        try:
            logger.info(f"Entering code: {code}")
            time.sleep(3)

            # 6 individual digit inputs
            digit_inputs = page.query_selector_all('input[maxlength="1"]')

            if len(digit_inputs) == 6:
                for i, digit in enumerate(code):
                    digit_inputs[i].click()
                    time.sleep(0.3)
                    digit_inputs[i].type(digit)
                    time.sleep(0.3)
                logger.info("✅ Code entered in digit fields")
            else:
                # Single input
                code_selectors = [
                    'input[name="confirmationCode"]',
                    'input[placeholder*="code"]',
                    'input[placeholder*="Code"]',
                    'input[autocomplete="one-time-code"]',
                ]
                for selector in code_selectors:
                    try:
                        element = page.query_selector(selector)
                        if element:
                            element.click()
                            time.sleep(0.5)
                            self._playwright_type(page, selector, code)
                            logger.info(f"✅ Code entered: {selector}")
                            break
                    except Exception:
                        continue

            time.sleep(2)

            # Confirm button
            confirm_selectors = [
                'button:has-text("Confirm")',
                'button:has-text("Next")',
                'button[type="submit"]',
            ]
            for selector in confirm_selectors:
                try:
                    btn = page.query_selector(selector)
                    if btn:
                        btn.click()
                        logger.info(f"✅ Confirm clicked: {selector}")
                        break
                except Exception:
                    continue

            time.sleep(3)
            return True

        except Exception as e:
            logger.error(f"Code entry failed: {e}")
            return False

    def _click_resend_code(self, page: Page) -> None:
        """Click resend code."""
        try:
            btn = page.query_selector('button:has-text("Resend")')
            if btn:
                btn.click()
                logger.info("Resend clicked")
                time.sleep(5)
        except Exception:
            pass

    def _set_birthday(self, page: Page) -> bool:
        """Set birthday."""
        try:
            logger.info("Setting birthday...")
            birthday = generate_birthday()
            time.sleep(3)

            # Month
            month_selectors = [
                'select[title="Month:"]',
                'select[aria-label="Month"]',
                'select[name="month"]',
            ]
            for selector in month_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        page.select_option(selector, str(birthday['month']))
                        logger.info(f"✅ Month set: {birthday['month']}")
                        break
                except Exception:
                    continue

            time.sleep(0.5)

            # Day
            day_selectors = [
                'select[title="Day:"]',
                'select[aria-label="Day"]',
                'select[name="day"]',
            ]
            for selector in day_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        page.select_option(selector, str(birthday['day']))
                        logger.info(f"✅ Day set: {birthday['day']}")
                        break
                except Exception:
                    continue

            time.sleep(0.5)

            # Year
            year_selectors = [
                'select[title="Year:"]',
                'select[aria-label="Year"]',
                'select[name="year"]',
            ]
            for selector in year_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        page.select_option(selector, str(birthday['year']))
                        logger.info(f"✅ Year set: {birthday['year']}")
                        break
                except Exception:
                    continue

            time.sleep(0.5)

            # Next button
            next_selectors = [
                'button:has-text("Next")',
                'button[type="submit"]',
            ]
            for selector in next_selectors:
                try:
                    btn = page.query_selector(selector)
                    if btn:
                        btn.click()
                        logger.info("✅ Next clicked after birthday")
                        break
                except Exception:
                    continue

            time.sleep(3)
            return True

        except Exception as e:
            logger.error(f"Birthday failed: {e}")
            return False

    def _upload_profile_picture(self, page: Page, image_path: str) -> bool:
        """Upload profile picture."""
        try:
            logger.info("Uploading profile picture...")
            upload = page.query_selector('input[type="file"]')
            if upload:
                upload.set_input_files(image_path)
                time.sleep(2)
                next_btn = page.query_selector('button:has-text("Next")')
                if next_btn:
                    next_btn.click()
                logger.info("✅ Profile picture uploaded")
                return True
            else:
                skip_btn = page.query_selector('button:has-text("Skip")')
                if skip_btn:
                    skip_btn.click()
                return False

        except Exception as e:
            logger.error(f"Profile pic failed: {e}")
            return False

    def _follow_suggested_accounts(self, page: Page) -> bool:
        """Follow suggested accounts."""
        try:
            logger.info("Following suggested accounts...")
            follow_buttons = page.query_selector_all('button:has-text("Follow")')

            num_to_follow = random.randint(
                Config.MIN_ACCOUNTS_TO_FOLLOW,
                Config.MAX_ACCOUNTS_TO_FOLLOW
            )

            for i in range(min(num_to_follow, len(follow_buttons))):
                follow_buttons[i].click()
                logger.info(f"Followed {i + 1}")
                time.sleep(random.uniform(2, 3))

            next_btn = page.query_selector(
                'button:has-text("Next"), button:has-text("Done")'
            )
            if next_btn:
                next_btn.click()

            return True

        except Exception as e:
            logger.error(f"Follow failed: {e}")
            return False

    def _cleanup_browser(self) -> None:
        """Cleanup browser."""
        try:
            if self.browser:
                self.browser.close()
                self.browser = None
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
            logger.info("✅ Browser closed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def _send_progress(
        self,
        message: str,
        percentage: Optional[int] = None,
        step: Optional[str] = None,
        account: Optional[int] = None,
        total: Optional[int] = None
    ) -> None:
        """Send progress update."""
        if self.progress_callback:
            self.progress_callback({
                'message': message,
                'percentage': percentage,
                'step': step,
                'account': account or self.current_account,
                'total': total or self.config.num_accounts
            })
