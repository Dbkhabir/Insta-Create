"""
Configuration module for Instagram Account Creator Bot.
Handles environment variables and global settings.
"""

import os
import logging
from typing import Optional

# Railway/Production environment detection
IS_RAILWAY = os.getenv('RAILWAY_ENVIRONMENT') is not None
IS_HEROKU = os.getenv('DYNO') is not None
IS_RENDER = os.getenv('RENDER') is not None
IS_PRODUCTION = IS_RAILWAY or IS_HEROKU or IS_RENDER

# Load .env only in local development
if not IS_PRODUCTION:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env file loaded (local development)")
    except ImportError:
        print("⚠️ python-dotenv not installed")
    except Exception as e:
        print(f"⚠️ Could not load .env: {e}")
else:
    print("✅ Running in production mode (Railway/Heroku/Render)")


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
    HEADLESS_MODE: bool = os.getenv('HEADLESS_MODE', 'true').lower() == 'true'
    BROWSER_TIMEOUT: int = 30
    
    # Railway specific: Force headless on production
    if IS_PRODUCTION:
        HEADLESS_MODE = True
    
    # Storage Configuration
    CREDENTIALS_FILE: str = 'credentials.json'
    TEMP_DIR: str = '/tmp' if IS_PRODUCTION else 'temp'
    AVATARS_DIR: str = '/tmp/avatars' if IS_PRODUCTION else 'avatars'
    
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
    def validate(cls) -> bool:
        """Validate configuration settings."""
        if not cls.TELEGRAM_BOT_TOKEN:
            error_msg = (
                "\n" + "="*60 + "\n"
                "❌ TELEGRAM_BOT_TOKEN is required!\n"
                "\n📝 Railway Setup Instructions:\n"
                "1. Go to https://railway.app/dashboard\n"
                "2. Select your project\n"
                "3. Click 'Variables' tab\n"
                "4. Click 'New Variable'\n"
                "5. Add:\n"
                "   Variable: TELEGRAM_BOT_TOKEN\n"
                "   Value: <your_bot_token_from_@BotFather>\n"
                "\n🤖 Get Token from @BotFather:\n"
                "1. Open Telegram → Search @BotFather\n"
                "2. Send: /newbot\n"
                "3. Follow instructions\n"
                "4. Copy the token (looks like: 1234567890:ABC...)\n"
                "\n🔄 After adding variable in Railway:\n"
                "   It will automatically redeploy\n"
                "="*60
            )
            raise ValueError(error_msg)
        
        if cls.MAX_ACCOUNTS > 50:
            logging.warning("MAX_ACCOUNTS exceeds recommended limit of 50")
        
        return True
    
    @classmethod
    def setup_logging(cls) -> None:
        """Configure logging for the application."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        handlers = [logging.StreamHandler()]
        
        if not IS_PRODUCTION:
            try:
                handlers.append(logging.FileHandler(cls.LOG_FILE))
            except:
                pass
        
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL.upper()),
            format=log_format,
            handlers=handlers,
            force=True
        )
    
    @classmethod
    def create_directories(cls) -> None:
        """Create necessary directories if they don't exist."""
        try:
            os.makedirs(cls.TEMP_DIR, exist_ok=True)
            os.makedirs(cls.AVATARS_DIR, exist_ok=True)
        except Exception as e:
            logging.warning(f"Could not create directories: {e}")


# ==========================================
# ⚠️ DO NOT CALL validate() HERE!
# ⚠️ Validation happens in bot.py main()
# ==========================================

# Only setup logging and directories
Config.setup_logging()
Config.create_directories()

# Print info
print("="*60)
print("Config Module Loaded")
print(f"Environment: {'Production' if IS_PRODUCTION else 'Local'}")
print(f"Token: {'✅ Present' if Config.TELEGRAM_BOT_TOKEN else '❌ Missing'}")
print("="*60)
