"""
Configuration for Instagram Account Creator Bot
Railway Production Ready
"""

import os
import logging

# ====================================================================
# 🔥 Bot Token (Configured)
# ====================================================================
BOT_TOKEN = "8751410316:AAHl_ERIaqzVGuA77tyVBIFuZG18s3E--ME"


class Config:
    """Global configuration settings."""
    
    # Token
    TELEGRAM_BOT_TOKEN: str = BOT_TOKEN
    
    # Captcha Configuration
    CAPTCHA_API_KEY: str = ""
    CAPTCHA_SERVICE: str = "2captcha"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "bot.log"
    
    # Retry Configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5
    
    # Instagram Configuration
    INSTAGRAM_SIGNUP_URL: str = "https://www.instagram.com/accounts/emailsignup/"
    INSTAGRAM_MIN_PASSWORD_LENGTH: int = 6
    
    # Email Provider Configuration
    EMAIL_CHECK_INTERVAL: int = 5
    EMAIL_CHECK_TIMEOUT: int = 120
    PROVIDER_COOLDOWN: int = 600
    PROVIDER_FAILURE_THRESHOLD: int = 3
    
    # Account Creation Limits
    MIN_ACCOUNTS: int = 1
    MAX_ACCOUNTS: int = 50
    
    # Timing Configuration (seconds)
    MIN_DELAY_BETWEEN_ACCOUNTS: int = 10
    MAX_DELAY_BETWEEN_ACCOUNTS: int = 30
    MIN_TYPING_DELAY: float = 0.05
    MAX_TYPING_DELAY: float = 0.2
    MIN_ACTION_DELAY: float = 0.5
    MAX_ACTION_DELAY: float = 1.0
    MIN_FIELD_DELAY: int = 2
    MAX_FIELD_DELAY: int = 5
    
    # Browser Configuration
    HEADLESS_MODE: bool = True
    BROWSER_TIMEOUT: int = 30
    
    # Storage Configuration
    CREDENTIALS_FILE: str = "credentials.json"
    TEMP_DIR: str = "/tmp"
    AVATARS_DIR: str = "/tmp/avatars"
    
    # Birthday Configuration
    MIN_BIRTH_YEAR: int = 1990
    MAX_BIRTH_YEAR: int = 2003
    
    # Anti-Suspension Configuration
    FOLLOW_SUGGESTED_ACCOUNTS: bool = True
    MIN_ACCOUNTS_TO_FOLLOW: int = 2
    MAX_ACCOUNTS_TO_FOLLOW: int = 3
    ENABLE_2FA: bool = False
    ADD_PROFILE_PICTURE: bool = True
    
    @classmethod
    def validate(cls):
        """Validate configuration settings."""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required!")
        
        print(f"✅ Token configured: {cls.TELEGRAM_BOT_TOKEN[:25]}...")
        return True
    
    @classmethod
    def setup_logging(cls):
        """Configure logging for the application."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL.upper()),
            format=log_format,
            handlers=[logging.StreamHandler()],
            force=True
        )
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist."""
        try:
            os.makedirs(cls.TEMP_DIR, exist_ok=True)
            os.makedirs(cls.AVATARS_DIR, exist_ok=True)
        except Exception as e:
            logging.warning(f"Could not create directories: {e}")


# Setup configuration
Config.setup_logging()
Config.create_directories()

print("="*60)
print("✅ Config Module Loaded Successfully")
print(f"✅ Bot Token: {BOT_TOKEN[:25]}...")
print("="*60)
