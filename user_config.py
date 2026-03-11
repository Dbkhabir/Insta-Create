"""
User Configuration Manager for Instagram Account Creator Bot.
Stores and manages user preferences for account creation.
"""

import logging
from typing import Optional, List, Dict, Any
from password_manager import PasswordManager, PasswordMode
from utils import generate_username, generate_random_name

logger = logging.getLogger(__name__)


class UsernameMode:
    """Username mode constants."""
    RANDOM = "random"
    PREFIX = "prefix"
    LIST = "list"


class FullNameMode:
    """Full name mode constants."""
    RANDOM = "random"
    SAME = "same"
    LIST = "list"
    EMPTY = "empty"


class UserConfig:
    """
    Manages user configuration for account creation.
    
    Attributes:
        num_accounts: Number of accounts to create
        username_mode: Username generation mode
        username_prefix: Custom prefix for usernames
        username_list: List of custom usernames
        fullname_mode: Full name generation mode
        fullname_same: Same name to use for all accounts
        fullname_list: List of custom full names
        password_manager: Password manager instance
    """
    
    def __init__(self):
        """Initialize user configuration with defaults."""
        # Account quantity
        self.num_accounts: int = 1
        
        # Username configuration
        self.username_mode: str = UsernameMode.RANDOM
        self.username_prefix: str = ""
        self.username_list: List[str] = []
        
        # Full name configuration
        self.fullname_mode: str = FullNameMode.RANDOM
        self.fullname_same: str = ""
        self.fullname_list: List[str] = []
        
        # Password configuration
        self.password_manager: PasswordManager = PasswordManager(mode=PasswordMode.RANDOM)
        
        logger.info("UserConfig initialized with default settings")
    
    def set_account_quantity(self, num: int) -> bool:
        """
        Set number of accounts to create.
        
        Args:
            num: Number of accounts
            
        Returns:
            bool: True if successful, False otherwise
        """
        from config import Config
        
        try:
            if num < Config.MIN_ACCOUNTS or num > Config.MAX_ACCOUNTS:
                logger.error(f"Invalid account quantity: {num} (must be {Config.MIN_ACCOUNTS}-{Config.MAX_ACCOUNTS})")
                return False
            
            self.num_accounts = num
            logger.info(f"Account quantity set to {num}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting account quantity: {e}")
            return False
    
    def set_username_mode(self, mode: str, prefix: str = "", custom_list: Optional[List[str]] = None) -> bool:
        """
        Set username generation mode.
        
        Args:
            mode: Username mode ('random', 'prefix', or 'list')
            prefix: Custom prefix (required for 'prefix' mode)
            custom_list: List of usernames (required for 'list' mode)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if mode == UsernameMode.PREFIX:
                if not prefix:
                    logger.error("Prefix required for prefix mode")
                    return False
                
                self.username_mode = UsernameMode.PREFIX
                self.username_prefix = prefix
                logger.info(f"Username mode set to PREFIX with prefix: {prefix}")
                
            elif mode == UsernameMode.LIST:
                if not custom_list:
                    logger.error("Custom list required for list mode")
                    return False
                
                if len(custom_list) < self.num_accounts:
                    logger.error(f"Username list has {len(custom_list)} items but {self.num_accounts} accounts requested")
                    return False
                
                self.username_mode = UsernameMode.LIST
                self.username_list = custom_list
                logger.info(f"Username mode set to LIST with {len(custom_list)} usernames")
                
            else:
                self.username_mode = UsernameMode.RANDOM
                logger.info("Username mode set to RANDOM")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting username mode: {e}")
            return False
    
    def set_fullname_mode(self, mode: str, same_name: str = "", custom_list: Optional[List[str]] = None) -> bool:
        """
        Set full name generation mode.
        
        Args:
            mode: Full name mode ('random', 'same', 'list', or 'empty')
            same_name: Name to use for all accounts (required for 'same' mode)
            custom_list: List of names (required for 'list' mode)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if mode == FullNameMode.SAME:
                if not same_name:
                    logger.error("Name required for same mode")
                    return False
                
                self.fullname_mode = FullNameMode.SAME
                self.fullname_same = same_name
                logger.info(f"Full name mode set to SAME: {same_name}")
                
            elif mode == FullNameMode.LIST:
                if not custom_list:
                    logger.error("Custom list required for list mode")
                    return False
                
                if len(custom_list) < self.num_accounts:
                    logger.error(f"Name list has {len(custom_list)} items but {self.num_accounts} accounts requested")
                    return False
                
                self.fullname_mode = FullNameMode.LIST
                self.fullname_list = custom_list
                logger.info(f"Full name mode set to LIST with {len(custom_list)} names")
                
            elif mode == FullNameMode.EMPTY:
                self.fullname_mode = FullNameMode.EMPTY
                logger.info("Full name mode set to EMPTY")
                
            else:
                self.fullname_mode = FullNameMode.RANDOM
                logger.info("Full name mode set to RANDOM")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting full name mode: {e}")
            return False
    
    def set_password_config(self, mode: str, custom_password: Optional[str] = None) -> bool:
        """
        Set password configuration.
        
        Args:
            mode: Password mode ('custom' or 'random')
            custom_password: Custom password (required for 'custom' mode)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if mode == PasswordMode.CUSTOM:
                if not custom_password:
                    logger.error("Custom password required for custom mode")
                    return False
                
                self.password_manager = PasswordManager(mode=PasswordMode.CUSTOM, custom_password=custom_password)
                logger.info("Password mode set to CUSTOM")
                
            else:
                self.password_manager = PasswordManager(mode=PasswordMode.RANDOM)
                logger.info("Password mode set to RANDOM")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting password config: {e}")
            return False
    
    def get_username(self, index: int) -> str:
        """
        Get username for a specific account.
        
        Args:
            index: Account index
            
        Returns:
            str: Generated username
        """
        return generate_username(
            mode=self.username_mode,
            prefix=self.username_prefix,
            custom_list=self.username_list,
            index=index
        )
    
    def get_fullname(self, index: int) -> str:
        """
        Get full name for a specific account.
        
        Args:
            index: Account index
            
        Returns:
            str: Generated full name
        """
        try:
            if self.fullname_mode == FullNameMode.SAME:
                return self.fullname_same
            
            elif self.fullname_mode == FullNameMode.LIST:
                if index < len(self.fullname_list):
                    return self.fullname_list[index]
                return generate_random_name()
            
            elif self.fullname_mode == FullNameMode.EMPTY:
                return ""
            
            else:  # RANDOM
                return generate_random_name()
                
        except Exception as e:
            logger.error(f"Error getting full name: {e}")
            return generate_random_name()
    
    def get_password(self, index: int) -> str:
        """
        Get password for a specific account.
        
        Args:
            index: Account index
            
        Returns:
            str: Password for account
        """
        return self.password_manager.get_password(index)
    
    def get_summary(self) -> str:
        """
        Get human-readable configuration summary.
        
        Returns:
            str: Configuration summary
        """
        summary = f"📊 Configuration Summary:\n\n"
        summary += f"🔢 Accounts: {self.num_accounts}\n\n"
        
        # Username config
        if self.username_mode == UsernameMode.RANDOM:
            summary += f"👤 Username: Fully Random (e.g., alex_8492)\n"
        elif self.username_mode == UsernameMode.PREFIX:
            summary += f"👤 Username: Custom Prefix '{self.username_prefix}_####'\n"
        else:
            summary += f"👤 Username: Custom List ({len(self.username_list)} usernames)\n"
        
        # Full name config
        if self.fullname_mode == FullNameMode.RANDOM:
            summary += f"📝 Full Name: Random Names\n"
        elif self.fullname_mode == FullNameMode.SAME:
            summary += f"📝 Full Name: Same for All ('{self.fullname_same}')\n"
        elif self.fullname_mode == FullNameMode.LIST:
            summary += f"📝 Full Name: Custom List ({len(self.fullname_list)} names)\n"
        else:
            summary += f"📝 Full Name: Empty\n"
        
        # Password config
        summary += f"\n{self.password_manager.get_mode_description()}"
        
        return summary
    
    def validate(self) -> tuple[bool, str]:
        """
        Validate current configuration.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # Validate account quantity
        from config import Config
        
        if self.num_accounts < Config.MIN_ACCOUNTS or self.num_accounts > Config.MAX_ACCOUNTS:
            return False, f"Invalid account quantity: {self.num_accounts}"
        
        # Validate username config
        if self.username_mode == UsernameMode.PREFIX and not self.username_prefix:
            return False, "Username prefix is required for prefix mode"
        
        if self.username_mode == UsernameMode.LIST:
            if not self.username_list:
                return False, "Username list is required for list mode"
            if len(self.username_list) < self.num_accounts:
                return False, f"Username list has {len(self.username_list)} items but {self.num_accounts} accounts requested"
        
        # Validate full name config
        if self.fullname_mode == FullNameMode.SAME and not self.fullname_same:
            return False, "Full name is required for same mode"
        
        if self.fullname_mode == FullNameMode.LIST:
            if not self.fullname_list:
                return False, "Full name list is required for list mode"
            if len(self.fullname_list) < self.num_accounts:
                return False, f"Full name list has {len(self.fullname_list)} items but {self.num_accounts} accounts requested"
        
        return True, ""
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            dict: Configuration dictionary
        """
        return {
            'num_accounts': self.num_accounts,
            'username_mode': self.username_mode,
            'username_prefix': self.username_prefix,
            'username_list': self.username_list,
            'fullname_mode': self.fullname_mode,
            'fullname_same': self.fullname_same,
            'fullname_list': self.fullname_list,
            'password_mode': self.password_manager.mode
        }
