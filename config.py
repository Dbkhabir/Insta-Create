"""
Configuration module for Instagram Account Creator Bot.
Handles environment variables and global settings.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Global configuration settings."""
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    
    # Captcha Configuration
    CAPTCHA_API_KEY: Optional[str] = os.getenv('CAPTCHA_API_KEY', None)
    CAPTCHA_SERVICE: str = os.getenv('CAPTCHA_SERVICE', '2captcha')
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = 'bot.log'
    
    # Retry Configuration
    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY: int = int(os.getenv('RETRY_DELAY', '5'))
    
    # Instagram Configuration
    INSTAGRAM_SIGNUP_URL: str = 'https://www.instagram.com/accounts/emailsignup/'
    INSTAGRAM_MIN_PASSWORD_LENGTH: int = 6
    
    # Email Provider Configuration
    EMAIL_CHECK_INTERVAL: int = 5  # seconds
    EMAIL_CHECK_TIMEOUT: int = 120  # seconds
    PROVIDER_COOLDOWN: int = 600  # 10 minutes in seconds
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
    HEADLESS_MODE: bool = os.getenv('HEADLESS_MODE', 'true').lower() == 'true'
    BROWSER_TIMEOUT: int = 30
    
    # Storage Configuration
    CREDENTIALS_FILE: str = 'credentials.json'
    TEMP_DIR: str = 'temp'
    AVATARS_DIR: str = 'avatars'
    
    # Birthday Configuration (for realistic accounts)
    MIN_BIRTH_YEAR: int = 1990
    MAX_BIRTH_YEAR: int = 2003
    
    # Anti-Suspension Configuration
    FOLLOW_SUGGESTED_ACCOUNTS: bool = True
    MIN_ACCOUNTS_TO_FOLLOW: int = 2
    MAX_ACCOUNTS_TO_FOLLOW: int = 3
    ENABLE_2FA: bool = False
    ADD_PROFILE_PICTURE: bool = True
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate configuration settings.
        
        Returns:
            bool: True if configuration is valid
            
        Raises:
            ValueError: If required configuration is missing
        """
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required in environment variables")
        
        if cls.MAX_ACCOUNTS > 50:
            logging.warning("MAX_ACCOUNTS exceeds recommended limit of 50")
        
        return True
    
    @classmethod
    def setup_logging(cls) -> None:
        """Configure logging for the application."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL.upper()),
            format=log_format,
            handlers=[
                logging.FileHandler(cls.LOG_FILE),
                logging.StreamHandler()
            ]
        )
    
    @classmethod
    def create_directories(cls) -> None:
        """Create necessary directories if they don't exist."""
        os.makedirs(cls.TEMP_DIR, exist_ok=True)
        os.makedirs(cls.AVATARS_DIR, exist_ok=True)

# Validate configuration on import
Config.validate()
Config.setup_logging()
Config.create_directories()
