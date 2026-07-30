"""
Configuration settings for the Pinterest to YouTube Shorts automation agent.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# YouTube API Configuration
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN", "")
YOUTUBE_API_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Pinterest API Configuration
PINTEREST_ACCESS_TOKEN = os.getenv("PINTEREST_ACCESS_TOKEN", "")
PINTEREST_API_BASE_URL = "https://api.pinterest.com/v5"

# Upload Settings
VIDEOS_PER_DAY = 3
MAX_VIDEO_DURATION_SECONDS = 60  # YouTube Shorts max duration
MIN_VIDEO_DURATION_SECONDS = 15  # Minimum recommended duration

# Video Specifications for YouTube Shorts
SHORTS_ASPECT_RATIO = (9, 16)  # Height:Width
SHORTS_MAX_RESOLUTION = (1080, 1920)  # Width:Height
SHORTS_MIN_RESOLUTION = (720, 1280)  # Width:Height

# Optimal Upload Times (in user's timezone)
# These are peak times when people watch Shorts
OPTIMAL_UPLOAD_TIMES = [
    "08:00",  # Breakfast time
    "12:00",  # Lunch break
    "19:00",  # Evening peak
]

# Timezone for scheduling
TIMEZONE = os.getenv("TIMEZONE", "America/New_York")

# Food-related search keywords for Pinterest
FOOD_KEYWORDS = [
    "easy recipes",
    "quick meals",
    "food hacks",
    "cooking tips",
    "dessert recipes",
    "healthy food",
    "street food",
    "baking recipes",
    "pasta recipes",
    "chicken recipes",
    "vegetarian recipes",
    "breakfast ideas",
    "snack recipes",
    "smoothie recipes",
    "pizza recipes",
]

# Default hashtags for food content
DEFAULT_HASHTAGS = [
    "#food",
    "#foodie",
    "#recipe",
    "#cooking",
    "#foodlover",
    "#yummy",
    "#delicious",
    "#homemade",
    "#foodporn",
    "#instafood",
    "#shorts",
    "#foodshorts",
    "#recipeshorts",
    "#cookingshorts",
    "#easyrecipes",
    "#quickrecipes",
]

# Video file paths
TEMP_DIR = "/tmp/pinterest_youtube_agent"
DOWNLOADED_VIDEOS_DIR = f"{TEMP_DIR}/downloaded"
PROCESSED_VIDEOS_DIR = f"{TEMP_DIR}/processed"

# Ensure directories exist
os.makedirs(DOWNLOADED_VIDEOS_DIR, exist_ok=True)
os.makedirs(PROCESSED_VIDEOS_DIR, exist_ok=True)

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
