import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
API_KEY = os.getenv("PRINTFUL_API_KEY", "")
BASE_URL = "https://api.printful.com"

# Directory Configuration
ROOT_DIR = Path(__file__).parent.absolute()

# UI Configuration
APP_TITLE = "Printful API Fetcher for Products, Variants, Templates and Mockups"
APP_sICON = "🎨"
PRIMARY_COLOR = "#2E7D32"
SECONDARY_COLOR = "#4CAF50"
BACKGROUND_COLOR = "#F5F5F5"

# Cache Configuration
CACHE_EXPIRY = 3600  # Cache expiry in seconds (1 hour)