"""
Password Manager for Instagram Account Creator Bot.
Handles password generation and storage based on user preferences.
"""

import logging
from typing import Optional
from utils import generate_strong_password

logger = logging.getLogger(__name__)


class PasswordMode:
    """Password mode constants."""
    CUSTOM = "custom"
    RANDOM = "random"


class PasswordManager:
    """
    Manages password generation and retrieval for account creation.
    
    Attributes:
        mode: Password mode ('custom' or 'random')
        custom_password: The single password to use for all accounts (if custom mode)
    """
    
    def __init__(self, mode: str = PasswordMode.RANDOM, custom_password: Optional[str] = None):
        """
        Initialize password manager.
        
        Args:
            mode: Password mode ('custom' or 'random')
            custom_password: Custom password for all accounts (required if mode is 'custom')
        
        Raises:
            ValueError: If custom mode is selected but no password provided
        """
        self.mode = mode
        self.custom_password = custom_password
        
        if self.mode == PasswordMode.CUSTOM:
            if not self.custom_password:
                raise ValueError("Custom password is required when mode is 'custom'")
            
            if len(self.custom_password) < 6:
                raise ValueError("Custom password must be at least 6 characters")
            
            logger.info("Password Manager initialized in CUSTOM mode")
        else:
            self.mode = PasswordMode.RANDOM
            logger.info("Password Manager initialized in RANDOM mode")
    
    def get_password(self, account_index: Optional[int] = None) -> str:
        """
        Get password for an account.
        
        Args:
            account_index: Index of account being created (for logging purposes)
            
        Returns:
            str: Password to use for the account
        """
        try:
            if self.mode == PasswordMode.CUSTOM:
                # Return the SAME password for ALL accounts
                logger.info(f"Account {account_index}: Using custom password (same for all)")
                return self.custom_password
            else:
                # Generate a NEW unique password for THIS account
                password = generate_strong_password(12)
                logger.info(f"Account {account_index}: Generated unique random password")
                return password
                
        except Exception as e:
            logger.error(f"Error getting password: {e}")
            # Fallback to random password
            return generate_strong_password(12)
    
    def set_mode(self, mode: str, custom_password: Optional[str] = None) -> bool:
        """
        Change password mode.
        
        Args:
            mode: New password mode
            custom_password: Custom password (if switching to custom mode)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if mode == PasswordMode.CUSTOM:
                if not custom_password:
                    logger.error("Custom password required for custom mode")
                    return False
                
                if len(custom_password) < 6:
                    logger.error("Custom password must be at least 6 characters")
                    return False
                
                self.mode = PasswordMode.CUSTOM
                self.custom_password = custom_password
                logger.info("Password mode changed to CUSTOM")
                
            else:
                self.mode = PasswordMode.RANDOM
                self.custom_password = None
                logger.info("Password mode changed to RANDOM")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting password mode: {e}")
            return False
    
    def get_mode_description(self) -> str:
        """
        Get human-readable description of current mode.
        
        Returns:
            str: Mode description
        """
        if self.mode == PasswordMode.CUSTOM:
            return f"🔒 Custom Password Mode: Same password for all accounts"
        else:
            return f"🎲 Random Password Mode: Unique password for each account"
    
    def validate_password(self, password: str) -> tuple[bool, str]:
        """
        Validate a password against Instagram requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        
        if len(password) > 100:
            return False, "Password must be less than 100 characters"
        
        # Check for at least one letter and one number (recommended)
        has_letter = any(c.isalpha() for c in password)
        has_number = any(c.isdigit() for c in password)
        
        if not has_letter or not has_number:
            logger.warning("Password doesn't contain both letters and numbers (not enforced but recommended)")
        
        return True, ""
