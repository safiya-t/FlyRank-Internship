from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    GEMINI_VISION_MODEL: str = "gemini-2.5-flash"
    CONFIDENCE_THRESHOLD: float = 0.70
    DATABASE_URL: str = "postgresql://image_user:123456@localhost:5432/image_db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
