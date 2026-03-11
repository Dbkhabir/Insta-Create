"""
Utility functions for Instagram Account Creator Bot.
Includes name database, random generators, and helper functions.
"""

import random
import string
import time
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Comprehensive name database (500+ names)
FIRST_NAMES = [
    # Male names
    "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
    "Thomas", "Charles", "Christopher", "Daniel", "Matthew", "Anthony", "Mark", "Donald",
    "Steven", "Paul", "Andrew", "Joshua", "Kenneth", "Kevin", "Brian", "George",
    "Edward", "Ronald", "Timothy", "Jason", "Jeffrey", "Ryan", "Jacob", "Gary",
    "Nicholas", "Eric", "Jonathan", "Stephen", "Larry", "Justin", "Scott", "Brandon",
    "Benjamin", "Samuel", "Raymond", "Gregory", "Frank", "Alexander", "Patrick", "Jack",
    "Dennis", "Jerry", "Tyler", "Aaron", "Jose", "Adam", "Henry", "Nathan",
    "Douglas", "Zachary", "Peter", "Kyle", "Walter", "Ethan", "Jeremy", "Harold",
    "Keith", "Christian", "Roger", "Noah", "Gerald", "Carl", "Terry", "Sean",
    "Austin", "Arthur", "Lawrence", "Jesse", "Dylan", "Bryan", "Joe", "Jordan",
    "Billy", "Bruce", "Albert", "Willie", "Gabriel", "Logan", "Alan", "Juan",
    "Wayne", "Roy", "Ralph", "Randy", "Eugene", "Vincent", "Russell", "Elijah",
    "Louis", "Bobby", "Philip", "Johnny", "Bradley", "Connor", "Travis", "Mason",
    
    # Female names
    "Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth", "Susan", "Jessica",
    "Sarah", "Karen", "Nancy", "Lisa", "Betty", "Margaret", "Sandra", "Ashley",
    "Dorothy", "Kimberly", "Emily", "Donna", "Michelle", "Carol", "Amanda", "Melissa",
    "Deborah", "Stephanie", "Rebecca", "Laura", "Sharon", "Cynthia", "Kathleen", "Amy",
    "Shirley", "Angela", "Helen", "Anna", "Brenda", "Pamela", "Nicole", "Emma",
    "Samantha", "Katherine", "Christine", "Debra", "Rachel", "Catherine", "Carolyn", "Janet",
    "Ruth", "Maria", "Heather", "Diane", "Virginia", "Julie", "Joyce", "Victoria",
    "Olivia", "Kelly", "Christina", "Lauren", "Joan", "Evelyn", "Judith", "Megan",
    "Cheryl", "Andrea", "Hannah", "Jacqueline", "Martha", "Gloria", "Teresa", "Ann",
    "Sara", "Madison", "Frances", "Kathryn", "Janice", "Jean", "Abigail", "Alice",
    "Sophia", "Grace", "Denise", "Judy", "Isabella", "Charlotte", "Mia", "Ava",
    "Amber", "Alexis", "Danielle", "Brittany", "Rose", "Diana", "Natalie", "Theresa",
    "Kayla", "Doris", "Lori", "Tiffany", "Julia", "Anna", "Kathy", "Emily",
    "Emma", "Chloe", "Ella", "Avery", "Scarlett", "Aria", "Luna", "Riley",
    "Lily", "Zoe", "Nora", "Hazel", "Ellie", "Violet", "Aurora", "Savannah",
    
    # Unisex names
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Quinn",
    "Peyton", "Skylar", "Cameron", "Dakota", "Jessie", "River", "Sage", "Blake",
    "Rowan", "Charlie", "Drew", "Emerson", "Finley", "Hayden", "Jamie", "Justice",
    "Kendall", "London", "Parker", "Reagan", "Reese", "Rory", "Sawyer", "Spencer"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
    "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey",
    "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson",
    "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza",
    "Ruiz", "Hughes", "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers",
    "Long", "Ross", "Foster", "Jimenez", "Powell", "Jenkins", "Perry", "Russell",
    "Sullivan", "Bell", "Coleman", "Butler", "Henderson", "Barnes", "Gonzales", "Fisher",
    "Vasquez", "Simmons", "Romero", "Jordan", "Patterson", "Alexander", "Hamilton", "Graham",
    "Reynolds", "Griffin", "Wallace", "Moreno", "West", "Cole", "Hayes", "Bryant",
    "Herrera", "Gibson", "Ellis", "Tran", "Medina", "Aguilar", "Stevens", "Murray",
    "Ford", "Castro", "Marshall", "Owens", "Harrison", "Fernandez", "McDonald", "Woods",
    "Washington", "Kennedy", "Wells", "Vargas", "Henry", "Chen", "Freeman", "Webb",
    "Tucker", "Guzman", "Burns", "Crawford", "Olson", "Simpson", "Porter", "Hunter"
]

USERNAME_BASES = [
    "alex", "sam", "chris", "jordan", "taylor", "morgan", "casey", "riley",
    "avery", "quinn", "blake", "drew", "sage", "river", "sky", "ocean",
    "phoenix", "ace", "raven", "storm", "winter", "summer", "autumn", "spring",
    "leo", "max", "charlie", "bailey", "cooper", "hunter", "chase", "parker",
    "tyler", "mason", "logan", "lucas", "ethan", "noah", "liam", "oliver",
    "emma", "ava", "sophia", "mia", "luna", "ella", "aria", "grace",
    "chloe", "lily", "zoe", "ruby", "ivy", "jade", "rose", "violet",
    "star", "nova", "luna", "sky", "rain", "cloud", "thunder", "lightning",
    "fire", "ice", "shadow", "light", "dark", "bright", "swift", "quick",
    "lucky", "happy", "sunny", "moon", "star", "cosmic", "galactic", "stellar",
    "blue", "red", "green", "gold", "silver", "bronze", "crystal", "diamond",
    "royal", "noble", "epic", "legend", "myth", "dream", "vision", "spirit",
    "soul", "heart", "mind", "zen", "calm", "peace", "warrior", "knight"
]


def generate_random_name() -> str:
    """
    Generate a random full name.
    
    Returns:
        str: Random first and last name combination
    """
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return f"{first} {last}"


def generate_username(mode: str = "random", prefix: str = "", custom_list: Optional[List[str]] = None, index: int = 0) -> str:
    """
    Generate username based on specified mode.
    
    Args:
        mode: Generation mode ('random', 'prefix', or 'list')
        prefix: Custom prefix for 'prefix' mode
        custom_list: List of custom usernames for 'list' mode
        index: Index for selecting from custom list
        
    Returns:
        str: Generated username
    """
    try:
        if mode == "list" and custom_list and index < len(custom_list):
            username = custom_list[index].lower().strip()
            # Remove spaces and special characters except underscore
            username = ''.join(c if c.isalnum() or c == '_' else '_' for c in username)
            return username
        
        elif mode == "prefix" and prefix:
            clean_prefix = prefix.lower().strip()
            clean_prefix = ''.join(c if c.isalnum() or c == '_' else '_' for c in clean_prefix)
            random_suffix = ''.join(random.choices(string.digits, k=4))
            return f"{clean_prefix}_{random_suffix}"
        
        else:  # random mode
            base = random.choice(USERNAME_BASES)
            random_suffix = ''.join(random.choices(string.digits, k=4))
            return f"{base}_{random_suffix}"
            
    except Exception as e:
        logger.error(f"Error generating username: {e}")
        # Fallback to random
        base = random.choice(USERNAME_BASES)
        random_suffix = ''.join(random.choices(string.digits, k=4))
        return f"{base}_{random_suffix}"


def generate_strong_password(length: int = 12) -> str:
    """
    Generate a strong random password.
    
    Args:
        length: Password length (default 12)
        
    Returns:
        str: Strong password with letters, numbers, and special characters
    """
    if length < 6:
        length = 6
    
    # Ensure password has at least one of each type
    password_chars = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice('!@#$%^&*')
    ]
    
    # Fill the rest randomly
    remaining_length = length - len(password_chars)
    all_chars = string.ascii_letters + string.digits + '!@#$%^&*'
    password_chars.extend(random.choices(all_chars, k=remaining_length))
    
    # Shuffle to avoid predictable pattern
    random.shuffle(password_chars)
    
    return ''.join(password_chars)


def generate_birthday() -> Dict[str, int]:
    """
    Generate a random realistic birthday (age 18-34).
    
    Returns:
        dict: Dictionary with 'year', 'month', 'day'
    """
    from config import Config
    
    year = random.randint(Config.MIN_BIRTH_YEAR, Config.MAX_BIRTH_YEAR)
    month = random.randint(1, 12)
    
    # Handle different month lengths
    if month in [4, 6, 9, 11]:
        day = random.randint(1, 30)
    elif month == 2:
        day = random.randint(1, 28)
    else:
        day = random.randint(1, 31)
    
    return {"year": year, "month": month, "day": day}


def random_delay(min_seconds: float, max_seconds: float) -> None:
    """
    Sleep for a random duration.
    
    Args:
        min_seconds: Minimum sleep duration
        max_seconds: Maximum sleep duration
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def human_typing_delay() -> float:
    """
    Get a random human-like typing delay.
    
    Returns:
        float: Delay in seconds
    """
    from config import Config
    
    # Occasionally add thinking pauses
    if random.random() < 0.1:  # 10% chance
        return random.uniform(0.3, 0.8)
    
    return random.uniform(Config.MIN_TYPING_DELAY, Config.MAX_TYPING_DELAY)


def save_credentials(credentials: Dict[str, Any], filename: Optional[str] = None) -> bool:
    """
    Save account credentials to JSON file.
    
    Args:
        credentials: Dictionary containing account information
        filename: Optional custom filename
        
    Returns:
        bool: True if successful, False otherwise
    """
    from config import Config
    
    if filename is None:
        filename = Config.CREDENTIALS_FILE
    
    try:
        # Load existing credentials
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                all_credentials = json.load(f)
        else:
            all_credentials = []
        
        # Add timestamp
        credentials['saved_at'] = datetime.now().isoformat()
        
        # Append new credentials
        all_credentials.append(credentials)
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_credentials, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Credentials saved successfully to {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving credentials: {e}")
        return False


def load_credentials(filename: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load credentials from JSON file.
    
    Args:
        filename: Optional custom filename
        
    Returns:
        list: List of credential dictionaries
    """
    from config import Config
    
    if filename is None:
        filename = Config.CREDENTIALS_FILE
    
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
        
    except Exception as e:
        logger.error(f"Error loading credentials: {e}")
        return []


def format_time(seconds: int) -> str:
    """
    Format seconds into human-readable time string.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        str: Formatted time string
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def estimate_creation_time(num_accounts: int) -> int:
    """
    Estimate total time to create accounts.
    
    Args:
        num_accounts: Number of accounts to create
        
    Returns:
        int: Estimated time in seconds
    """
    # Average time per account: ~90 seconds
    avg_time_per_account = 90
    # Add delay between accounts
    delay_time = (num_accounts - 1) * 20  # Average 20s delay
    
    total_seconds = (num_accounts * avg_time_per_account) + delay_time
    return total_seconds


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    return filename


def generate_user_agent() -> str:
    """
    Generate a realistic random user agent.
    
    Returns:
        str: User agent string
    """
    chrome_versions = ['120.0.0.0', '119.0.0.0', '118.0.0.0', '117.0.0.0']
    windows_versions = ['10.0', '11.0']
    
    chrome_version = random.choice(chrome_versions)
    windows_version = random.choice(windows_versions)
    
    user_agents = [
        f'Mozilla/5.0 (Windows NT {windows_version}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36',
        f'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36',
        f'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36',
    ]
    
    return random.choice(user_agents)


def get_random_resolution() -> tuple:
    """
    Get a random realistic screen resolution.
    
    Returns:
        tuple: (width, height)
    """
    resolutions = [
        (1920, 1080),
        (1366, 768),
        (1440, 900),
        (1536, 864),
        (1600, 900),
        (2560, 1440),
    ]
    
    return random.choice(resolutions)


def create_simple_avatar(username: str) -> str:
    """
    Create a simple avatar image with initials.
    
    Args:
        username: Username to create avatar for
        
    Returns:
        str: Path to created avatar image
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        from config import Config
        
        # Create image
        size = (200, 200)
        background_colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
            '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52B788'
        ]
        
        bg_color = random.choice(background_colors)
        image = Image.new('RGB', size, bg_color)
        draw = ImageDraw.Draw(image)
        
        # Get initials (first 2 characters of username)
        initials = username[:2].upper()
        
        # Draw text
        try:
            font = ImageFont.truetype("arial.ttf", 80)
        except:
            font = ImageFont.load_default()
        
        # Center text
        bbox = draw.textbbox((0, 0), initials, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
        
        draw.text(position, initials, fill='white', font=font)
        
        # Save image
        filename = os.path.join(Config.AVATARS_DIR, f"{username}_avatar.png")
        image.save(filename)
        
        logger.info(f"Avatar created: {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"Error creating avatar: {e}")
        return ""


def extract_verification_code(text: str) -> Optional[str]:
    """
    Extract 6-digit verification code from email text.
    
    Args:
        text: Email body text
        
    Returns:
        str: 6-digit code or None if not found
    """
    import re
    
    # Search for 6-digit code
    match = re.search(r'\b(\d{6})\b', text)
    
    if match:
        return match.group(1)
    
    return None


def mask_email(email: str) -> str:
    """
    Mask email address for privacy.
    
    Args:
        email: Full email address
        
    Returns:
        str: Masked email (e.g., ab***@example.com)
    """
    try:
        username, domain = email.split('@')
        
        if len(username) <= 2:
            masked_username = username[0] + '*'
        else:
            masked_username = username[:2] + '*' * (len(username) - 2)
        
        return f"{masked_username}@{domain}"
        
    except Exception:
        return email


def mask_password(password: str) -> str:
    """
    Mask password for privacy.
    
    Args:
        password: Full password
        
    Returns:
        str: Masked password (e.g., ab******)
    """
    if len(password) <= 2:
        return '*' * len(password)
    
    return password[:2] + '*' * (len(password) - 2)


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_username(username: str) -> bool:
    """
    Validate Instagram username format.
    
    Args:
        username: Username to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    import re
    
    # Instagram username rules:
    # - 1-30 characters
    # - Letters, numbers, periods, underscores only
    # - Cannot start or end with period
    
    if not username or len(username) < 1 or len(username) > 30:
        return False
    
    if username.startswith('.') or username.endswith('.'):
        return False
    
    pattern = r'^[a-zA-Z0-9._]+$'
    return bool(re.match(pattern, username))


def get_progress_bar(current: int, total: int, length: int = 20) -> str:
    """
    Generate a text-based progress bar.
    
    Args:
        current: Current progress value
        total: Total value
        length: Length of progress bar
        
    Returns:
        str: Progress bar string
    """
    if total == 0:
        percent = 0
    else:
        percent = (current / total) * 100
    
    filled = int(length * current / total) if total > 0 else 0
    bar = '█' * filled + '░' * (length - filled)
    
    return f"[{bar}] {percent:.1f}%"


class RateLimiter:
    """Simple rate limiter to prevent API abuse."""
    
    def __init__(self, max_calls: int, time_window: int):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def is_allowed(self) -> bool:
        """
        Check if a call is allowed.
        
        Returns:
            bool: True if call is allowed, False otherwise
        """
        now = time.time()
        
        # Remove old calls outside time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        # Check if we can make another call
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False
    
    def time_until_next_call(self) -> float:
        """
        Get time until next call is allowed.
        
        Returns:
            float: Seconds until next call
        """
        if not self.calls:
            return 0
        
        oldest_call = min(self.calls)
        now = time.time()
        time_passed = now - oldest_call
        
        return max(0, self.time_window - time_passed)
