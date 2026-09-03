import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()

    # Reverse image search
    SERP_API_KEY = os.getenv("SERP_API_KEY", "").strip()
    IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "").strip()

    # ClickHouse is OPTIONAL until credentials are configured.
    CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "").strip()
    CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8443"))
    CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default").strip()
    CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "").strip()
    CLICKHOUSE_DATABASE = os.getenv("CLICKHOUSE_DATABASE", "default").strip()

    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp_uploads")

    @classmethod
    def clickhouse_configured(cls) -> bool:
        return bool(cls.CLICKHOUSE_HOST and cls.CLICKHOUSE_PASSWORD)


os.makedirs(Config.TEMP_DIR, exist_ok=True)
