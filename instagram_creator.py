"""
Instagram Account Creator Module.
Playwright version - Production ready.
"""

import logging
import time
import random
import os
from typing import Optional, Dict, Any, Callable
from datetime import datetime

from playwright.sync_api import (
    sync_playwright, Page, BrowserContext,
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

    # ==================== PUBLIC ====================

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
                f"ACCOUNT {self.current_account}/{self.config.num_accounts}"
            )
            logger.info(f"{'='*60}")

            self._send_progress(
                f"📝 Account {self.current_account}/{self.config.num_accounts}...",
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

    # ==================== PRIVATE ====================

    def _create_single_account(self, index: int) -> Dict[str, Any]:
        """Create one Instagram account."""
        data = {
            'account_number': self.current_account,
            'success': False,
            'created_at': datetime.now().isoformat()
        }

        context = None

        try:
            # Step 1: Browser
            self._send_progress("🌐 Step 1: Browser init...")
            if not self._start_playwright():
                raise Exception("Browser init failed")

            # Step 2: Email
            self._send_progress("📧 Step 2: Creating email...")
            email_data = self.email_manager.create_email_with_rotation()
            if not email_data:
                raise Exception("Email creation failed")
            logger.info(f"✅ Email: {email_data['email']}")
            data['email'] = email_data['email']
            data['email_provider'] = email_data.get('provider', 'unknown')

            # Step 3: Details
            self._send_progress("🔧 Step 3: Generating details...")
            username = self.config.get_username(index)
            fullname = self.config.get_fullname(index)
            password = self.config.get_password(index)
            data['username'] = username
            data['fullname'] = fullname
            data['password'] = password
            logger.info(f"✅ User: {username} | Name: {fullname}")

            # Step 4: New page
            self._send_progress("🔗 Step 4: Opening Instagram...")
            context, page = self._new_context_and_page()

            # Step 5: Load signup page
            self._send_progress("📄 Step 5: Loading signup page...")
            if not self._load_signup_page(page):
                raise Exception("Failed to load signup page")

            # Step 6: Fill form
            self._send_progress("✍️ Step 6: Filling form...")
            username = self._fill_form(
                page, email_data['email'], fullname, username, password
            )
            if not username:
                raise Exception("Failed to fill signup form")
            data['username'] = username
            logger.info("✅ Form filled")

            # Step 7: Submit
            self._send_progress("📤 Step 7: Submitting...")
            if not self._submit_form(page):
                raise Exception("Failed to submit form")
            logger.info("✅ Submitted")

            # Step 8: Verification code
            self._send_progress("📬 Step 8: Verification code...")
            code = self._get_verification_code(email_data, page)
            if not code:
                raise Exception("Verification code not received")
            logger.info(f"✅ Code: {code}")

            # Step 9: Birthday
            self._send_progress("🎂 Step 9: Birthday...")
            if not self._handle_birthday(page):
                raise Exception("Birthday setup failed")
            logger.info("✅ Birthday set")

            # Step 10: Finalize
            self._send_progress("✨ Step 10: Finalizing...")
            self._finalize_account(page, username)

            data['success'] = True
            data['status'] = 'active'
            save_credentials(data)

            logger.info(f"✅ ACCOUNT {self.current_account} CREATED!")
            return data

        except Exception as e:
            logger.error(f"❌ ACCOUNT {self.current_account} FAILED: {e}")
            import traceback
            traceback.print_exc()
            data['error'] = str(e)

            # Debug screenshot
            try:
                if 'page' in locals() and page:
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

    def _start_playwright(self) -> bool:
        """Start Playwright browser."""
        try:
            if self.playwright:
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
                ],
                slow_mo=100
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
        """Create browser context and page."""
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
            }
        )

        # Anti-detection script
        context.add_init_script("""
            // webdriver flag remove
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // plugins fake
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    return [
                        {name: 'Chrome PDF Plugin'},
                        {name: 'Chrome PDF Viewer'},
                        {name: 'Native Client'}
                    ];
                }
            });

            // languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });

            // chrome object
            window.chrome = {
                runtime: {
                    connect: () => {},
                    sendMessage: () => {}
                }
            };

            // permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

        page = context.new_page()

        # Request interception - speed up
        page.route(
            "**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,otf}",
            lambda route: route.abort()
            if 'instagram' not in route.request.url
            else route.continue_()
        )

        return context, page

    def _load_signup_page(self, page: Page) -> bool:
        """Load Instagram signup page properly."""
        try:
            logger.info(f"Loading: {SIGNUP_URL}")

            # First visit homepage to get cookies
            logger.info("Step 1: Visiting homepage first...")
            page.goto(
                "https://www.instagram.com/",
                wait_until='domcontentloaded',
                timeout=30000
            )
            time.sleep(3)

            # Cookie consent যদি থাকে
            self._handle_cookie_consent(page)
            time.sleep(2)

            # Now go to signup
            logger.info("Step 2: Going to signup page...")
            page.goto(
                SIGNUP_URL,
                wait_until='domcontentloaded',
                timeout=30000
            )
            time.sleep(3)

            logger.info(f"URL: {page.url}")
            logger.info(f"Title: {page.title()}")

            # Screenshot
            try:
                page.screenshot(path='/tmp/signup_page.png')
                logger.info("Screenshot: /tmp/signup_page.png")
            except Exception:
                pass

            # Wait for form
            logger.info("Waiting for signup form...")
            form_loaded = self._wait_for_signup_form(page)

            if not form_loaded:
                logger.warning("Form not found, trying mobile URL...")

                # Try mobile version
                page.goto(
                    "https://www.instagram.com/accounts/emailsignup/",
                    wait_until='networkidle',
                    timeout=30000
                )
                time.sleep(5)
                form_loaded = self._wait_for_signup_form(page)

            if not form_loaded:
                # Log what we have
                logger.error("Form still not found!")
                source = page.content()
                logger.error(f"Page length: {len(source)}")
                logger.error(f"Page preview: {source[:2000]}")

                inputs = page.query_selector_all('input')
                logger.error(f"Total inputs: {len(inputs)}")
                for inp in inputs:
                    logger.error(
                        f"  name={inp.get_attribute('name')}, "
                        f"type={inp.get_attribute('type')}, "
                        f"placeholder={inp.get_attribute('placeholder')}, "
                        f"aria-label={inp.get_attribute('aria-label')}"
                    )
                return False

            logger.info("✅ Signup form loaded!")
            return True

        except Exception as e:
            logger.error(f"Page load failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _handle_cookie_consent(self, page: Page):
        """Handle cookie consent popup."""
        try:
            consent_selectors = [
                'button:has-text("Allow all cookies")',
                'button:has-text("Accept All")',
                'button:has-text("Accept")',
                'button:has-text("Allow essential and optional cookies")',
                '[data-testid="cookie-policy-manage-dialog-accept-button"]',
            ]
            for selector in consent_selectors:
                try:
                    btn = page.wait_for_selector(selector, timeout=3000)
                    if btn:
                        btn.click()
                        logger.info(f"Cookie consent accepted: {selector}")
                        time.sleep(1)
                        return
                except PlaywrightTimeout:
                    continue
        except Exception as e:
            logger.debug(f"Cookie consent: {e}")

    def _wait_for_signup_form(self, page: Page) -> bool:
        """Wait for signup form to appear."""
        selectors = [
            'input[name="emailOrPhone"]',
            'input[name="email"]',
            'input[type="email"]',
            'input[aria-label="Mobile Number or Email"]',
            'input[aria-label="Email"]',
            'input[aria-label*="email"]',
            'input[aria-label*="Email"]',
            'input[aria-label*="Mobile"]',
            'input[aria-label*="Phone"]',
        ]

        for selector in selectors:
            try:
                element = page.wait_for_selector(
                    selector, timeout=8000, state='visible'
                )
                if element:
                    logger.info(f"✅ Form found with: {selector}")
                    return True
            except PlaywrightTimeout:
                continue
            except Exception:
                continue

        return False

    def _fill_form(
        self, page: Page,
        email: str, fullname: str,
        username: str, password: str
    ) -> Optional[str]:
        """
        Fill Instagram signup form.
        Returns final username or None on failure.
        """
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

            if not self._fill_field(page, email_selectors, email, "Email"):
                return None

            self._random_sleep(1, 2)

            # ===== FULL NAME =====
            if fullname:
                logger.info("Filling fullname...")
                name_selectors = [
                    'input[name="fullName"]',
                    'input[aria-label="Full Name"]',
                    'input[aria-label*="Full Name" i]',
                    'input[placeholder*="Full Name" i]',
                    'input[placeholder*="name" i]',
                ]
                self._fill_field(
                    page, name_selectors, fullname, "Fullname", required=False
                )
                self._random_sleep(1, 2)

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
                page, username_selectors, username, "Username"
            ):
                return None

            self._random_sleep(2, 3)

            # Check username availability
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

            if not self._fill_field(page, pass_selectors, password, "Password"):
                return None

            self._random_sleep(1, 2)

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
        selectors: list,
        value: str,
        field_name: str,
        required: bool = True
    ) -> bool:
        """Fill a single form field."""
        for selector in selectors:
            try:
                element = page.wait_for_selector(
                    selector, timeout=5000, state='visible'
                )
                if element:
                    element.click()
                    time.sleep(0.5)
                    element.fill('')
                    time.sleep(0.3)
                    # Human-like typing
                    for char in value:
                        page.keyboard.type(char, delay=random.randint(50, 150))
                    logger.info(f"✅ {field_name} filled: {selector}")
                    return True
            except PlaywrightTimeout:
                continue
            except Exception as e:
                logger.debug(f"{field_name} selector {selector} failed: {e}")
                continue

        if required:
            logger.error(f"❌ {field_name} field NOT found!")
            # Debug: show all inputs
            inputs = page.query_selector_all('input')
            logger.error(f"Available inputs ({len(inputs)}):")
            for inp in inputs:
                logger.error(
                    f"  name={inp.get_attribute('name')}, "
                    f"type={inp.get_attribute('type')}, "
                    f"placeholder={inp.get_attribute('placeholder')}, "
                    f"aria-label={inp.get_attribute('aria-label')}, "
                    f"id={inp.get_attribute('id')}"
                )
        else:
            logger.warning(f"⚠️ {field_name} field not found, skipping")

        return not required

    def _check_and_fix_username(
        self, page: Page,
        username: str,
        selectors: list
    ) -> Optional[str]:
        """Check username availability and fix if needed."""
        try:
            # Wait for availability check
            time.sleep(3)

            unavailable_texts = [
                "isn't available",
                "not available",
                "already taken",
                "Username not available",
            ]

            page_text = page.content().lower()
            is_unavailable = any(
                text.lower() in page_text for text in unavailable_texts
            )

            if is_unavailable:
                logger.warning(f"Username '{username}' not available!")
                new_username = f"{username}{random.randint(100, 999)}"
                logger.info(f"Trying: {new_username}")

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
                                    char, delay=random.randint(50, 150)
                                )
                            logger.info(f"✅ New username: {new_username}")
                            time.sleep(3)
                            return new_username
                    except Exception:
                        continue

            return username

        except Exception as e:
            logger.error(f"Username check error: {e}")
            return username

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
                        selector, timeout=5000, state='visible'
                    )
                    if btn:
                        btn.scroll_into_view_if_needed()
                        time.sleep(0.5)
                        btn.click()
                        logger.info(f"✅ Submitted: {selector}")
                        time.sleep(5)

                        # Check for errors
                        error_selectors = [
                            '[role="alert"]',
                            '.error-container',
                            'p[data-testid*="error"]',
                        ]
                        for err_sel in error_selectors:
                            err = page.query_selector(err_sel)
                            if err and err.is_visible():
                                logger.warning(
                                    f"Submit error: {err.inner_text()}"
                                )

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

    def _get_verification_code(
        self, email_data: Dict, page: Page
    ) -> Optional[str]:
        """Get verification code from email."""
        try:
            logger.info("Waiting for verification code...")
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
                return None

            logger.info(f"✅ Code received: {code}")

            # Enter code
            if not self._enter_code(page, code):
                return None

            return code

        except Exception as e:
            logger.error(f"Code retrieval error: {e}")
            return None

    def _enter_code(self, page: Page, code: str) -> bool:
        """Enter verification code."""
        try:
            logger.info(f"Entering code: {code}")
            time.sleep(3)

            # Screenshot for debug
            try:
                page.screenshot(path='/tmp/code_page.png')
            except Exception:
                pass

            # 6 separate digit inputs
            digit_inputs = page.query_selector_all('input[maxlength="1"]')
            if len(digit_inputs) >= 6:
                for i, digit in enumerate(code[:6]):
                    digit_inputs[i].click()
                    time.sleep(0.3)
                    digit_inputs[i].type(digit)
                    time.sleep(0.3)
                logger.info("✅ Code entered in digit fields")
            else:
                # Single input field
                code_selectors = [
                    'input[name="confirmationCode"]',
                    'input[aria-label*="code" i]',
                    'input[aria-label*="Code" i]',
                    'input[placeholder*="code" i]',
                    'input[autocomplete="one-time-code"]',
                    'input[inputmode="numeric"]',
                ]

                code_entered = False
                for selector in code_selectors:
                    try:
                        element = page.wait_for_selector(
                            selector, timeout=5000, state='visible'
                        )
                        if element:
                            element.click()
                            time.sleep(0.5)
                            element.fill('')
                            for char in code:
                                page.keyboard.type(
                                    char, delay=random.randint(100, 200)
                                )
                            logger.info(f"✅ Code entered: {selector}")
                            code_entered = True
                            break
                    except PlaywrightTimeout:
                        continue
                    except Exception:
                        continue

                if not code_entered:
                    logger.error("❌ Code input not found!")
                    inputs = page.query_selector_all('input')
                    for inp in inputs:
                        logger.error(
                            f"  name={inp.get_attribute('name')}, "
                            f"placeholder={inp.get_attribute('placeholder')}, "
                            f"aria-label={inp.get_attribute('aria-label')}"
                        )
                    return False

            time.sleep(2)

            # Confirm
            confirm_selectors = [
                'button:has-text("Confirm")',
                'button:has-text("Next")',
                'button:has-text("Continue")',
                'button[type="submit"]',
            ]
            for selector in confirm_selectors:
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
            resend_selectors = [
                'button:has-text("Resend")',
                'button:has-text("Send again")',
                'a:has-text("Resend")',
            ]
            for selector in resend_selectors:
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

    def _handle_birthday(self, page: Page) -> bool:
        """Handle birthday page."""
        try:
            logger.info("Looking for birthday page...")
            time.sleep(3)

            # Screenshot
            try:
                page.screenshot(path='/tmp/birthday_page.png')
            except Exception:
                pass

            birthday = generate_birthday()
            logger.info(
                f"Birthday: {birthday['month']}/"
                f"{birthday['day']}/{birthday['year']}"
            )

            # Check if birthday page exists
            birthday_indicators = [
                'select[title="Month:"]',
                'select[aria-label="Month"]',
                'select[name="month"]',
                'text="Add your birthday"',
                'text="Birthday"',
            ]

            birthday_page = False
            for indicator in birthday_indicators:
                try:
                    element = page.wait_for_selector(
                        indicator, timeout=8000
                    )
                    if element:
                        birthday_page = True
                        logger.info(
                            f"✅ Birthday page found: {indicator}"
                        )
                        break
                except PlaywrightTimeout:
                    continue

            if not birthday_page:
                logger.warning(
                    "Birthday page not found, might be on different step"
                )
                # Check current URL/page
                logger.info(f"Current URL: {page.url}")
                return True

            # Set Month
            month_selectors = [
                'select[title="Month:"]',
                'select[aria-label="Month"]',
                'select[name="month"]',
            ]
            for selector in month_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        page.select_option(
                            selector, str(birthday['month'])
                        )
                        logger.info(f"✅ Month set: {birthday['month']}")
                        time.sleep(0.5)
                        break
                except Exception:
                    continue

            # Set Day
            day_selectors = [
                'select[title="Day:"]',
                'select[aria-label="Day"]',
                'select[name="day"]',
            ]
            for selector in day_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        page.select_option(
                            selector, str(birthday['day'])
                        )
                        logger.info(f"✅ Day set: {birthday['day']}")
                        time.sleep(0.5)
                        break
                except Exception:
                    continue

            # Set Year
            year_selectors = [
                'select[title="Year:"]',
                'select[aria-label="Year"]',
                'select[name="year"]',
            ]
            for selector in year_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        page.select_option(
                            selector, str(birthday['year'])
                        )
                        logger.info(f"✅ Year set: {birthday['year']}")
                        time.sleep(0.5)
                        break
                except Exception:
                    continue

            # Next button
            next_selectors = [
                'button:has-text("Next")',
                'button:has-text("Continue")',
                'button[type="submit"]',
            ]
            for selector in next_selectors:
                try:
                    btn = page.query_selector(selector)
                    if btn and btn.is_visible():
                        btn.click()
                        logger.info(f"✅ Next after birthday: {selector}")
                        time.sleep(3)
                        break
                except Exception:
                    continue

            return True

        except Exception as e:
            logger.error(f"Birthday error: {e}")
            return False

    def _finalize_account(self, page: Page, username: str):
        """Handle post-signup steps."""
        try:
            time.sleep(5)
            logger.info(f"Finalizing... URL: {page.url}")

            # Profile picture
            if Config.ADD_PROFILE_PICTURE:
                try:
                    avatar_path = create_simple_avatar(username)
                    if avatar_path:
                        upload = page.query_selector('input[type="file"]')
                        if upload:
                            upload.set_input_files(avatar_path)
                            time.sleep(2)
                            next_btn = page.query_selector(
                                'button:has-text("Next")'
                            )
                            if next_btn:
                                next_btn.click()
                                time.sleep(2)
                            logger.info("✅ Profile picture uploaded")
                except Exception as e:
                    logger.warning(f"Profile pic: {e}")

            # Skip optional steps
            skip_selectors = [
                'button:has-text("Skip")',
                'button:has-text("Not Now")',
                'button:has-text("Cancel")',
            ]
            for _ in range(5):
                skipped = False
                for selector in skip_selectors:
                    try:
                        btn = page.query_selector(selector)
                        if btn and btn.is_visible():
                            btn.click()
                            logger.info(f"Skipped: {selector}")
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
                    for i in range(min(num, len(follow_btns))):
                        follow_btns[i].click()
                        time.sleep(random.uniform(1, 2))
                    logger.info(f"✅ Followed {min(num, len(follow_btns))}")
                except Exception as e:
                    logger.warning(f"Follow: {e}")

            logger.info("✅ Account finalized!")

        except Exception as e:
            logger.warning(f"Finalize warning: {e}")

    def _random_sleep(self, min_s: float, max_s: float):
        """Sleep random time."""
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
