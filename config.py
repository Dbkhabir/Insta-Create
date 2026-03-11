"""
Instagram Account Creator Bot - Configuration
Token: Hardcoded for Railway deployment
"""

import os
import logging

# Direct token configuration
TELEGRAM_BOT_TOKEN = "8751410316:AAHl_ERIaqzVGuA77tyVBIFuZG18s3E--ME"


class Config:
    """Configuration class."""
    
    # Bot Token
    TELEGRAM_BOT_TOKEN: str = TELEGRAM_BOT_TOKEN
    
    # Other settings
    CAPTCHA_API_KEY: str = ""
    CAPTCHA_SERVICE: str = "2captcha"
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "bot.log"
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5
    INSTAGRAM_SIGNUP_URL: str = "https://www.instagram.com/accounts/emailsignup/"
    INSTAGRAM_MIN_PASSWORD_LENGTH: int = 6
    EMAIL_CHECK_INTERVAL: int = 5
    EMAIL_CHECK_TIMEOUT: int = 120
    PROVIDER_COOLDOWN: int = 600
    PROVIDER_FAILURE_THRESHOLD: int = 3
    MIN_ACCOUNTS: int = 1
    MAX_ACCOUNTS: int = 50
    MIN_DELAY_BETWEEN_ACCOUNTS: int = 10
    MAX_DELAY_BETWEEN_ACCOUNTS: int = 30
    MIN_TYPING_DELAY: float = 0.05
    MAX_TYPING_DELAY: float = 0.2
    MIN_ACTION_DELAY: float = 0.5
    MAX_ACTION_DELAY: float = 1.0
    MIN_FIELD_DELAY: int = 2
    MAX_FIELD_DELAY: int = 5
    HEADLESS_MODE: bool = True
    BROWSER_TIMEOUT: int = 30
    CREDENTIALS_FILE: str = "credentials.json"
    TEMP_DIR: str = "/tmp"
    AVATARS_DIR: str = "/tmp/avatars"
    MIN_BIRTH_YEAR: int = 1990
    MAX_BIRTH_YEAR: int = 2003
    FOLLOW_SUGGESTED_ACCOUNTS: bool = True
    MIN_ACCOUNTS_TO_FOLLOW: int = 2
    MAX_ACCOUNTS_TO_FOLLOW: int = 3
    ENABLE_2FA: bool = False
    ADD_PROFILE_PICTURE: bool = True
    
    @classmethod
    def validate(cls):
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("Token missing!")
        print(f"TOKEN FOUND: {cls.TELEGRAM_BOT_TOKEN[:30]}...")
        return True
    
    @classmethod
    def setup_logging(cls):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()],
            force=True
        )
    
    @classmethod
    def create_directories(cls):
        os.makedirs(cls.TEMP_DIR, exist_ok=True)
        os.makedirs(cls.AVATARS_DIR, exist_ok=True)


Config.setup_logging()
Config.create_directories()
print("="*70)
print("CONFIG LOADED - TOKEN HARDCODED")
print(f"Token: {TELEGRAM_BOT_TOKEN}")
print("="*70)
