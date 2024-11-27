import logging
from typing import List, Optional

from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Settings class for the application."""
    # Discord Bot Settings
    DISCORD_TOKEN: str
    DISCORD_GUILD_ID: Optional[str] = None
    LOG_LEVEL: str = "INFO"

    # OpenAI Settings
    OPENAI_API_KEY: str
    OPENAI_DEFAULT_MODEL: str = "gpt-3.5-turbo"
    OPENAI_AVAILABLE_MODELS: List[str] = ["gpt-3.5-turbo", "gpt-4"]
    OPENAI_MAX_HISTORY: int = 10
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.7

    # MongoDB Settings
    MONGODB_URI: str
    MONGODB_DB_NAME: str

    @validator("LOG_LEVEL")
    def validate_log_level(self, v: str) -> str:
        """Validate log level."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in levels:
            raise ValueError(f"Log level must be one of {levels}")
        return v.upper()

    @validator("DISCORD_GUILD_ID")
    def validate_guild_id(self, v: Optional[str]) -> Optional[int]:
        """Validate guild ID."""
        if v is None:
            return None
        try:
            return int(v)
        except ValueError:
            raise ValueError("DISCORD_GUILD_ID must be a valid integer if provided")

    class Config:
        """Configuration for pydantic."""
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

def get_settings() -> Settings:
    """Get application settings.

    Returns:
        Settings: Application settings instance
    
    Raises:
        pydantic.error_wrappers.ValidationError: If environment variables are invalid
    """
    return Settings()

# Configure logging
def setup_logging(level: str = "INFO") -> None:
    """Setup application logging.

    Args:
        level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

# Create settings instance
settings = get_settings()

# Setup logging with configured level
setup_logging(settings.LOG_LEVEL)

if __name__ == "__main__":
    print(f"Settings loaded successfully: {settings.dict()}")