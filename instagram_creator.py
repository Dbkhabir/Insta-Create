"""
Instagram Account Creator Module.
Playwright version - All issues fixed.
"""

import logging
import time
import random
import os
import json
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime

from playwright.sync_api import (
    sync_playwright, Page, BrowserContext, Browser,
    TimeoutError as PlaywrightTimeout
)

from config import Config
from user_config import UserConfig
from email_providers import EmailProviderManager
from captcha_solver import CaptchaSolver
from utils import (
    random_delay, human_typing_delay, generate_birthday,
    create_simple_avatar, save_credentials, generate_user_agent
)

logger = logging.getLogger(__name__)

SIGNUP_URL = "https://www.instagram.com/accounts/emailsignup/"
INSTAGRAM_HOME = "https://www.instagram.com/"


class InstagramCreator:
    """Instagram account creator - Playwright based."""

    def __init__(
        self,
        user_config: UserConfig,
        progress_callback: Optional[Callable] = None
    ):
        self.config = user_config
        self.progress_callback = progress_callback
        self.email_manager = EmailProviderManager()
        self.captcha_solver = CaptchaSolver()
        self.playwright = None
        self.browser = None
        self.current_account = 0
        self.successful_accounts = []
        self.failed_accounts = []

    # ========================================================
    # PUBLIC
    # ========================================================

    def create_accounts(self) -> Dict[str, Any]:
        """Create multiple Instagram accounts."""
        logger.info(
            f"Starting creation of {self.config.num_accounts} accounts..."
        )
        self._send_progress("🚀 Starting...", 0)
        start_time = time.time()

        for i in range(self.config.num_accounts):
            self.current_account = i + 1
            pct = int((i / self.config.num_accounts) * 100)

            logger.info(f"\n{'='*60}")
            logger.info(
                f"ACCOUNT {self.current_account}/"
                f"{self.config.num_accounts}"
            )
            logger.info(f"{'='*60}")

            self._send_progress(
                f"📝 Account {self.current_account}/"
                f"{self.config.num_accounts}...",
                pct,
                account=self.current_account,
                total=self.config.num_accounts
            )

            try:
                result = self._create_single_account(i)
                if result['success']:
                    self.successful_accounts.append(result)
                    self._send_progress(
                        f"✅ Account {self.current_account} created!"
                    )
                else:
                    self.failed_accounts.append(result)
                    self._send_progress(
                        f"❌ Failed: {result.get('error', 'Unknown')}"
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
                logger.info(f"Waiting {delay}s...")
                time.sleep(delay)

        elapsed = int(time.time() - start_time)
        summary = {
            'total': self.config.num_accounts,
            'successful': len(self.successful_accounts),
            'failed': len(self.failed_accounts),
            'elapsed_time': elapsed,
            'accounts': self.successful_accounts
        }
        self._send_progress("✨ Done!", 100)
        return summary

    # ========================================================
    # PRIVATE - MAIN FLOW
    # ========================================================

    def _create_single_account(self, index: int) -> Dict[str, Any]:
        """Create one Instagram account."""
        data = {
            'account_number': self.current_account,
            'success': False,
            'created_at': datetime.now().isoformat()
        }
        context = None
        page = None

        try:
            # Step 1: Browser
            self._send_progress("🌐 Step 1: Browser init...")
            logger.info("Step 1: Starting browser...")
            if not self._start_playwright():
                raise Exception("Browser init failed")
            logger.info("✅ Browser ready")

            # Step 2: Email
            self._send_progress("📧 Step 2: Creating email...")
            logger.info("Step 2: Creating email...")
            email_data = self.email_manager.create_email_with_rotation()
            if not email_data:
                raise Exception("Email creation failed")
            logger.info(f"✅ Email: {email_data['email']}")
            data['email'] = email_data['email']
            data['email_provider'] = email_data.get('provider', 'unknown')

            # Step 3: Details
            self._send_progress("🔧 Step 3: Generating details...")
            logger.info("Step 3: Generating details...")
            username = self.config.get_username(index)
            fullname = self.config.get_fullname(index)
            password = self.config.get_password(index)
            data['username'] = username
            data['fullname'] = fullname
            data['password'] = password
            logger.info(f"✅ Username: {username} | Name: {fullname}")

            # Step 4: New page
            self._send_progress("🔗 Step 4: Opening browser...")
            logger.info("Step 4: Creating page...")
            context, page = self._new_context_and_page()

            # Step 5: Load signup
            self._send_progress("📄 Step 5: Loading Instagram...")
            logger.info("Step 5: Loading signup page...")
            if not self._load_signup_page(page):
                raise Exception("Failed to load signup page")
            logger.info("✅ Signup page loaded")

            # Step 6: Fill form
            self._send_progress("✍️ Step 6: Filling form...")
            logger.info("Step 6: Filling form...")
            final_username = self._fill_form(
                page, email_data['email'],
                fullname, username, password
            )
            if not final_username:
                raise Exception("Failed to fill signup form")
            data['username'] = final_username
            logger.info("✅ Form filled")

            # Step 7: Submit
            self._send_progress("📤 Step 7: Submitting...")
            logger.info("Step 7: Submitting form...")
            if not self._submit_form(page):
                raise Exception("Failed to submit form")
            logger.info("✅ Submitted")

            # Step 8: Verification
            self._send_progress("📬 Step 8: Verification code...")
            logger.info("Step 8: Getting verification code...")
            code = self._get_verification_code(email_data, page)
            if not code:
                raise Exception("Verification code not received")
            logger.info(f"✅ Code: {code}")

            # Step 9: Birthday
            self._send_progress("🎂 Step 9: Setting birthday...")
            logger.info("Step 9: Setting birthday...")
            if not self._handle_birthday(page):
                raise Exception("Birthday setup failed")
            logger.info("✅ Birthday set")

            # Step 10: Finalize
            self._send_progress("✨ Step 10: Finalizing...")
            logger.info("Step 10: Finalizing...")
            self._finalize_account(page, final_username)

            data['success'] = True
            data['status'] = 'active'
            save_credentials(data)

            logger.info(f"✅ ACCOUNT {self.current_account} CREATED!")
            return data

        except Exception as e:
            logger.error(
                f"❌ ACCOUNT {self.current_account} FAILED: {e}"
            )
            import traceback
            traceback.print_exc()
            data['error'] = str(e)

            try:
                if page:
                    page.screenshot(path='/tmp/error_final.png')
                    logger.info("Error screenshot saved")
            except Exception:
                pass

            return data

        finally:
            try:
                if context:
                    context.close()
            except Exception:
                pass
            self._stop_playwright()

    # ========================================================
    # PRIVATE - BROWSER
    # ========================================================

    def _start_playwright(self) -> bool:
        """Start Playwright browser."""
        try:
            if self.playwright and self.browser:
                return True

            logger.info("Starting Playwright...")
            self.playwright = sync_playwright().start()

            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-zygote',
                    '--disable-extensions',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--window-size=1280,800',
                    '--lang=en-US',
                ],
                slow_mo=50
            )
            logger.info("✅ Browser started")
            return True

        except Exception as e:
            logger.error(f"Browser start failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _stop_playwright(self):
        """Stop Playwright."""
        try:
            if self.browser:
                self.browser.close()
                self.browser = None
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
            logger.info("✅ Browser stopped")
        except Exception as e:
            logger.error(f"Stop error: {e}")

    def _new_context_and_page(self):
        """Create browser context and page with stealth."""
        context = self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent=(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            locale='en-US',
            timezone_id='America/New_York',
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': (
                    'text/html,application/xhtml+xml,'
                    'application/xml;q=0.9,image/webp,*/*;q=0.8'
                ),
                'sec-ch-ua': (
                    '"Not_A Brand";v="8", '
                    '"Chromium";v="120", '
                    '"Google Chrome";v="120"'
                ),
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
            }
        )

        # Anti-detection
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {name: 'Chrome PDF Plugin'},
                    {name: 'Chrome PDF Viewer'},
                    {name: 'Native Client'}
                ]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            window.chrome = {
                runtime: {
                    connect: () => {},
                    sendMessage: () => {}
                }
            };
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({state: Notification.permission}) :
                    originalQuery(parameters)
            );
        """)

        page = context.new_page()
        page.set_default_timeout(30000)
        page.set_default_navigation_timeout(45000)

        return context, page

    # ========================================================
    # PRIVATE - PAGE LOADING
    # ========================================================

    def _load_signup_page(self, page: Page) -> bool:
        """
        Load Instagram signup page properly.
        Handles React SPA, cookies, redirects.
        """
        try:
            # ===== Step A: Homepage visit =====
            logger.info("A: Visiting Instagram homepage...")
            try:
                page.goto(
                    INSTAGRAM_HOME,
                    wait_until='domcontentloaded',
                    timeout=45000
                )
                time.sleep(4)
                logger.info(f"Homepage title: {page.title()}")
                logger.info(f"Homepage URL: {page.url}")
            except Exception as e:
                logger.warning(f"Homepage load warning: {e}")

            # ===== Step B: Cookie consent =====
            logger.info("B: Handling cookie consent...")
            self._handle_cookie_consent(page)
            time.sleep(2)

            # ===== Step C: Go to signup =====
            logger.info("C: Navigating to signup...")
            try:
                page.goto(
                    SIGNUP_URL,
                    wait_until='domcontentloaded',
                    timeout=45000
                )
            except Exception as e:
                logger.warning(f"Signup nav warning: {e}")

            # ===== Step D: Wait for JS render =====
            logger.info("D: Waiting for JS render...")
            time.sleep(6)

            logger.info(f"Current URL: {page.url}")
            logger.info(f"Current title: {page.title()}")

            # ===== Step E: Screenshot =====
            try:
                page.screenshot(
                    path='/tmp/signup_page.png',
                    full_page=True
                )
                logger.info("Screenshot: /tmp/signup_page.png")
            except Exception:
                pass

            # ===== Step F: Log all inputs =====
            self._log_all_inputs(page)

            # ===== Step G: Check redirects =====
            current_url = page.url
            if 'login' in current_url:
                logger.warning("Redirected to login, going back to signup...")
                page.goto(
                    SIGNUP_URL,
                    wait_until='domcontentloaded',
                    timeout=45000
                )
                time.sleep(6)
                self._log_all_inputs(page)

            if 'checkpoint' in current_url or 'challenge' in current_url:
                logger.error(f"Instagram blocking! URL: {current_url}")
                return False

            # ===== Step H: Wait for form =====
            logger.info("H: Waiting for form fields...")
            found = self._wait_for_any_input(page)

            if not found:
                # ===== Step I: Scroll and retry =====
                logger.warning("I: Scrolling and retrying...")
                page.evaluate("window.scrollTo(0, 300)")
                time.sleep(2)
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(2)
                found = self._wait_for_any_input(page)

            if not found:
                # ===== Step J: Full page reload =====
                logger.warning("J: Full reload...")
                page.reload(wait_until='networkidle', timeout=45000)
                time.sleep(6)
                self._handle_cookie_consent(page)
                time.sleep(2)
                self._log_all_inputs(page)
                found = self._wait_for_any_input(page)

            if not found:
                # Log full page source for debug
                content = page.content()
                logger.error("❌ Form NOT found!")
                logger.error(f"Page length: {len(content)}")
                logger.error(f"Page preview: {content[:3000]}")
                return False

            logger.info("✅ Signup form loaded!")
            return True

        except Exception as e:
            logger.error(f"Page load error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _wait_for_any_input(self, page: Page) -> bool:
        """Wait for any signup form input to appear."""
        selectors = [
            'input[name="emailOrPhone"]',
            'input[name="email"]',
            'input[type="email"]',
            'input[aria-label="Mobile Number or Email"]',
            'input[aria-label="Email"]',
            'input[aria-label*="email" i]',
            'input[aria-label*="Mobile" i]',
            'input[aria-label*="Phone" i]',
            'input[placeholder*="email" i]',
            'input[placeholder*="mobile" i]',
            'input[placeholder*="phone" i]',
            'input[placeholder*="Email" i]',
            'input[placeholder*="Mobile" i]',
            'input[placeholder*="Phone" i]',
        ]

        for selector in selectors:
            try:
                element = page.wait_for_selector(
                    selector,
                    timeout=5000,
                    state='visible'
                )
                if element:
                    logger.info(f"✅ Input found: {selector}")
                    return True
            except PlaywrightTimeout:
                continue
            except Exception as e:
                logger.debug(f"Selector {selector}: {e}")
                continue

        return False

    def _handle_cookie_consent(self, page: Page):
        """Handle cookie consent popup."""
        consent_selectors = [
            'button:has-text("Allow all cookies")',
            'button:has-text("Accept All")',
            'button:has-text("Accept")',
            'button:has-text("Allow essential and optional cookies")',
            '[data-testid="cookie-policy-manage-dialog-accept-button"]',
            'button:has-text("Only allow essential cookies")',
        ]
        for selector in consent_selectors:
            try:
                btn = page.wait_for_selector(selector, timeout=3000)
                if btn:
                    btn.click()
                    logger.info(f"Cookie accepted: {selector}")
                    time.sleep(1)
                    return
            except PlaywrightTimeout:
                continue
            except Exception:
                continue

    def _log_all_inputs(self, page: Page):
        """Log all input fields for debugging."""
        try:
            inputs = page.query_selector_all('input')
            logger.info(f"Total inputs on page: {len(inputs)}")
            for i, inp in enumerate(inputs):
                logger.info(
                    f"  [{i}] name={inp.get_attribute('name')}, "
                    f"type={inp.get_attribute('type')}, "
                    f"placeholder={inp.get_attribute('placeholder')}, "
                    f"aria-label={inp.get_attribute('aria-label')}, "
                    f"id={inp.get_attribute('id')}"
                )
        except Exception as e:
            logger.warning(f"Input log failed: {e}")

    # ========================================================
    # PRIVATE - FORM FILLING
    # ========================================================

    def _fill_form(
        self, page: Page,
        email: str, fullname: str,
        username: str, password: str
    ) -> Optional[str]:
        """Fill Instagram signup form. Returns final username."""
        try:
            # ===== EMAIL =====
            logger.info("Filling email...")
            email_selectors = [
                'input[name="emailOrPhone"]',
                'input[name="email"]',
                'input[type="email"]',
                'input[aria-label="Mobile Number or Email"]',
                'input[aria-label="Email"]',
                'input[aria-label*="email" i]',
                'input[aria-label*="Mobile" i]',
                'input[aria-label*="Phone" i]',
                'input[placeholder*="email" i]',
                'input[placeholder*="mobile" i]',
                'input[placeholder*="phone" i]',
            ]
            if not self._fill_field(
                page, email_selectors, email, "Email"
            ):
                return None
            self._sleep(1, 2)

            # ===== FULL NAME =====
            if fullname:
                logger.info("Filling fullname...")
                name_selectors = [
                    'input[name="fullName"]',
                    'input[aria-label="Full Name"]',
                    'input[aria-label*="Full Name" i]',
                    'input[aria-label*="Name" i]',
                    'input[placeholder*="Full Name" i]',
                    'input[placeholder*="name" i]',
                ]
                self._fill_field(
                    page, name_selectors,
                    fullname, "Fullname",
                    required=False
                )
                self._sleep(1, 2)

            # ===== USERNAME =====
            logger.info("Filling username...")
            username_selectors = [
                'input[name="username"]',
                'input[aria-label="Username"]',
                'input[aria-label*="Username" i]',
                'input[placeholder*="Username" i]',
                'input[autocomplete="username"]',
            ]
            if not self._fill_field(
                page, username_selectors,
                username, "Username"
            ):
                return None
            self._sleep(2, 3)

            # Username availability
            username = self._check_and_fix_username(
                page, username, username_selectors
            )
            if not username:
                return None

            # ===== PASSWORD =====
            logger.info("Filling password...")
            pass_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[aria-label="Password"]',
                'input[aria-label*="Password" i]',
                'input[placeholder*="Password" i]',
            ]
            if not self._fill_field(
                page, pass_selectors, password, "Password"
            ):
                return None
            self._sleep(1, 2)

            logger.info("✅ Form filled successfully!")
            return username

        except Exception as e:
            logger.error(f"Form fill error: {e}")
            import traceback
            traceback.print_exc()
            try:
                page.screenshot(path='/tmp/form_error.png')
            except Exception:
                pass
            return None

    def _fill_field(
        self, page: Page,
        selectors: List[str],
        value: str,
        field_name: str,
        required: bool = True
    ) -> bool:
        """Fill a single form field."""
        for selector in selectors:
            try:
                element = page.wait_for_selector(
                    selector,
                    timeout=5000,
                    state='visible'
                )
                if element:
                    element.scroll_into_view_if_needed()
                    time.sleep(0.3)
                    element.click()
                    time.sleep(0.5)
                    element.fill('')
                    time.sleep(0.3)
                    # Human typing
                    for char in value:
                        page.keyboard.type(
                            char,
                            delay=random.randint(50, 150)
                        )
                    time.sleep(0.5)
                    logger.info(f"✅ {field_name}: {selector}")
                    return True
            except PlaywrightTimeout:
                continue
            except Exception as e:
                logger.debug(f"{field_name} [{selector}]: {e}")
                continue

        if required:
            logger.error(f"❌ {field_name} NOT found!")
            self._log_all_inputs(page)
        else:
            logger.warning(f"⚠️ {field_name} not found, skipping")

        return not required

    def _check_and_fix_username(
        self, page: Page,
        username: str,
        selectors: List[str]
    ) -> Optional[str]:
        """Check username availability and fix if needed."""
        try:
            time.sleep(3)
            content = page.content().lower()

            unavailable = any(t.lower() in content for t in [
                "isn't available",
                "not available",
                "already taken",
                "username not available",
                "this username",
            ])

            if unavailable:
                new_username = f"{username}{random.randint(100, 999)}"
                logger.warning(
                    f"Username '{username}' taken! "
                    f"Trying: {new_username}"
                )
                for selector in selectors:
                    try:
                        element = page.query_selector(selector)
                        if element:
                            element.triple_click()
                            time.sleep(0.3)
                            element.fill('')
                            time.sleep(0.3)
                            for char in new_username:
                                page.keyboard.type(
                                    char,
                                    delay=random.randint(50, 150)
                                )
                            time.sleep(3)
                            return new_username
                    except Exception:
                        continue

            return username

        except Exception as e:
            logger.error(f"Username check error: {e}")
            return username

    # ========================================================
    # PRIVATE - FORM SUBMIT
    # ========================================================

    def _submit_form(self, page: Page) -> bool:
        """Submit signup form."""
        try:
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Sign up")',
                'button:has-text("Next")',
                'button:has-text("Continue")',
            ]

            for selector in submit_selectors:
                try:
                    btn = page.wait_for_selector(
                        selector,
                        timeout=5000,
                        state='visible'
                    )
                    if btn:
                        btn.scroll_into_view_if_needed()
                        time.sleep(0.5)
                        btn.click()
                        logger.info(f"✅ Submit: {selector}")
                        time.sleep(5)

                        # Check errors
                        for err_sel in [
                            '[role="alert"]',
                            '.error-container',
                            'p[data-testid*="error"]',
                        ]:
                            try:
                                err = page.query_selector(err_sel)
                                if err and err.is_visible():
                                    logger.warning(
                                        f"Error after submit: "
                                        f"{err.inner_text()}"
                                    )
                            except Exception:
                                pass

                        return True
                except PlaywrightTimeout:
                    continue
                except Exception:
                    continue

            logger.error("❌ Submit button not found!")
            return False

        except Exception as e:
            logger.error(f"Submit error: {e}")
            return False

    # ========================================================
    # PRIVATE - VERIFICATION
    # ========================================================

    def _get_verification_code(
        self,
        email_data: Dict,
        page: Page
    ) -> Optional[str]:
        """Get and enter verification code."""
        try:
            logger.info("Fetching verification code...")
            code = self.email_manager.fetch_instagram_code(
                email_data,
                timeout=Config.EMAIL_CHECK_TIMEOUT
            )

            if not code:
                logger.warning("No code, trying resend...")
                self._click_resend(page)
                code = self.email_manager.fetch_instagram_code(
                    email_data,
                    timeout=Config.EMAIL_CHECK_TIMEOUT
                )

            if not code:
                logger.error("❌ No verification code!")
                return None

            logger.info(f"✅ Code: {code}")

            if not self._enter_code(page, code):
                return None

            return code

        except Exception as e:
            logger.error(f"Code error: {e}")
            return None

    def _enter_code(self, page: Page, code: str) -> bool:
        """Enter verification code on page."""
        try:
            logger.info(f"Entering code: {code}")
            time.sleep(3)

            try:
                page.screenshot(path='/tmp/code_page.png')
            except Exception:
                pass

            # 6 digit inputs
            digit_inputs = page.query_selector_all(
                'input[maxlength="1"]'
            )
            if len(digit_inputs) >= 6:
                for i, digit in enumerate(code[:6]):
                    digit_inputs[i].click()
                    time.sleep(0.3)
                    digit_inputs[i].type(digit)
                    time.sleep(0.3)
                logger.info("✅ Code in digit fields")
            else:
                # Single input
                code_selectors = [
                    'input[name="confirmationCode"]',
                    'input[aria-label*="code" i]',
                    'input[aria-label*="Code" i]',
                    'input[placeholder*="code" i]',
                    'input[placeholder*="Code" i]',
                    'input[autocomplete="one-time-code"]',
                    'input[inputmode="numeric"]',
                ]
                entered = False
                for selector in code_selectors:
                    try:
                        element = page.wait_for_selector(
                            selector,
                            timeout=5000,
                            state='visible'
                        )
                        if element:
                            element.click()
                            time.sleep(0.5)
                            element.fill('')
                            for char in code:
                                page.keyboard.type(
                                    char,
                                    delay=random.randint(100, 200)
                                )
                            logger.info(f"✅ Code: {selector}")
                            entered = True
                            break
                    except PlaywrightTimeout:
                        continue
                    except Exception:
                        continue

                if not entered:
                    logger.error("❌ Code input not found!")
                    self._log_all_inputs(page)
                    return False

            time.sleep(2)

            # Confirm button
            for selector in [
                'button:has-text("Confirm")',
                'button:has-text("Next")',
                'button:has-text("Continue")',
                'button[type="submit"]',
            ]:
                try:
                    btn = page.query_selector(selector)
                    if btn and btn.is_visible():
                        btn.click()
                        logger.info(f"✅ Confirmed: {selector}")
                        break
                except Exception:
                    continue

            time.sleep(4)
            return True

        except Exception as e:
            logger.error(f"Code entry error: {e}")
            return False

    def _click_resend(self, page: Page):
        """Click resend code button."""
        try:
            for selector in [
                'button:has-text("Resend")',
                'button:has-text("Send again")',
                'a:has-text("Resend")',
                'button:has-text("Resend Code")',
            ]:
                try:
                    btn = page.query_selector(selector)
                    if btn and btn.is_visible():
                        btn.click()
                        logger.info("✅ Resend clicked")
                        time.sleep(5)
                        return
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Resend: {e}")

    # ========================================================
    # PRIVATE - BIRTHDAY
    # ========================================================

    def _handle_birthday(self, page: Page) -> bool:
        """Handle birthday page."""
        try:
            logger.info("Checking birthday page...")
            time.sleep(3)

            try:
                page.screenshot(path='/tmp/birthday_page.png')
            except Exception:
                pass

            logger.info(f"URL: {page.url}")

            birthday = generate_birthday()
            logger.info(
                f"Birthday: {birthday['month']}/"
                f"{birthday['day']}/{birthday['year']}"
            )

            # Check birthday page
            birthday_found = False
            for indicator in [
                'select[title="Month:"]',
                'select[aria-label="Month"]',
                'select[name="month"]',
                'text="Add your birthday"',
                'text="Birthday"',
                '[aria-label*="birthday" i]',
            ]:
                try:
                    element = page.wait_for_selector(
                        indicator, timeout=8000
                    )
                    if element:
                        birthday_found = True
                        logger.info(f"Birthday page: {indicator}")
                        break
                except PlaywrightTimeout:
                    continue

            if not birthday_found:
                logger.warning("Birthday page not found, skipping")
                return True

            # Set Month
            for selector in [
                'select[title="Month:"]',
                'select[aria-label="Month"]',
                'select[name="month"]',
            ]:
                try:
                    if page.query_selector(selector):
                        page.select_option(
                            selector, str(birthday['month'])
                        )
                        logger.info(f"✅ Month: {birthday['month']}")
                        time.sleep(0.5)
                        break
                except Exception:
                    continue

            # Set Day
            for selector in [
                'select[title="Day:"]',
                'select[aria-label="Day"]',
                'select[name="day"]',
            ]:
                try:
                    if page.query_selector(selector):
                        page.select_option(
                            selector, str(birthday['day'])
                        )
                        logger.info(f"✅ Day: {birthday['day']}")
                        time.sleep(0.5)
                        break
                except Exception:
                    continue

            # Set Year
            for selector in [
                'select[title="Year:"]',
                'select[aria-label="Year"]',
                'select[name="year"]',
            ]:
                try:
                    if page.query_selector(selector):
                        page.select_option(
                            selector, str(birthday['year'])
                        )
                        logger.info(f"✅ Year: {birthday['year']}")
                        time.sleep(0.5)
                        break
                except Exception:
                    continue

            # Next
            for selector in [
                'button:has-text("Next")',
                'button:has-text("Continue")',
                'button[type="submit"]',
            ]:
                try:
                    btn = page.query_selector(selector)
                    if btn and btn.is_visible():
                        btn.click()
                        logger.info(f"✅ Birthday next: {selector}")
                        time.sleep(3)
                        break
                except Exception:
                    continue

            return True

        except Exception as e:
            logger.error(f"Birthday error: {e}")
            return False

    # ========================================================
    # PRIVATE - FINALIZE
    # ========================================================

    def _finalize_account(self, page: Page, username: str):
        """Handle all post-signup steps."""
        try:
            time.sleep(5)
            logger.info(f"Finalizing... URL: {page.url}")

            # Profile picture
            if Config.ADD_PROFILE_PICTURE:
                try:
                    avatar_path = create_simple_avatar(username)
                    if avatar_path:
                        upload = page.query_selector(
                            'input[type="file"]'
                        )
                        if upload:
                            upload.set_input_files(avatar_path)
                            time.sleep(2)
                            btn = page.query_selector(
                                'button:has-text("Next")'
                            )
                            if btn:
                                btn.click()
                                time.sleep(2)
                            logger.info("✅ Profile picture uploaded")
                except Exception as e:
                    logger.warning(f"Profile pic: {e}")

            # Skip all optional steps
            skip_count = 0
            for _ in range(8):
                skipped = False
                for selector in [
                    'button:has-text("Skip")',
                    'button:has-text("Not Now")',
                    'button:has-text("Maybe Later")',
                    'button:has-text("Cancel")',
                ]:
                    try:
                        btn = page.query_selector(selector)
                        if btn and btn.is_visible():
                            btn.click()
                            skip_count += 1
                            logger.info(f"Skipped [{skip_count}]: {selector}")
                            time.sleep(2)
                            skipped = True
                            break
                    except Exception:
                        continue
                if not skipped:
                    break

            # Follow suggested
            if Config.FOLLOW_SUGGESTED_ACCOUNTS:
                try:
                    follow_btns = page.query_selector_all(
                        'button:has-text("Follow")'
                    )
                    num = random.randint(
                        Config.MIN_ACCOUNTS_TO_FOLLOW,
                        Config.MAX_ACCOUNTS_TO_FOLLOW
                    )
                    count = 0
                    for i in range(min(num, len(follow_btns))):
                        try:
                            follow_btns[i].click()
                            count += 1
                            time.sleep(random.uniform(1, 2))
                        except Exception:
                            continue
                    logger.info(f"✅ Followed {count} accounts")

                    # Next/Done
                    for selector in [
                        'button:has-text("Next")',
                        'button:has-text("Done")',
                    ]:
                        try:
                            btn = page.query_selector(selector)
                            if btn and btn.is_visible():
                                btn.click()
                                break
                        except Exception:
                            continue
                except Exception as e:
                    logger.warning(f"Follow: {e}")

            logger.info("✅ Account finalized!")

        except Exception as e:
            logger.warning(f"Finalize warning: {e}")

    # ========================================================
    # PRIVATE - HELPERS
    # ========================================================

    def _sleep(self, min_s: float, max_s: float):
        """Random sleep."""
        time.sleep(random.uniform(min_s, max_s))

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
