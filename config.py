import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

class Config:
    # Gemini API Credentials
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    # ClickHouse Credentials (Partner Track)
    CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
    CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", 8443))
    CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
    CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")

    # System & Processing Configs
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp_uploads")

# Ensure temporary directory exists
os.makedirs(Config.TEMP_DIR, exist_ok=True)