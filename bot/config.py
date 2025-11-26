from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Telegram
    bot_token: str = Field(..., env="BOT_TOKEN")
    
    # PostgreSQL
    postgres_host: str = Field("db", env="POSTGRES_HOST")
    postgres_port: int = Field(5432, env="POSTGRES_PORT")
    postgres_user: str = Field("vshu_bot", env="POSTGRES_USER")
    postgres_password: str = Field(..., env="POSTGRES_PASSWORD")
    postgres_db: str = Field("vshu_bot_db", env="POSTGRES_DB")
    
    # Напоминания
    reminder_hour: int = Field(9, env="REMINDER_HOUR")
    reminder_minute: int = Field(0, env="REMINDER_MINUTE")
    reminder_days_before: int = Field(3, env="REMINDER_DAYS_BEFORE")
    
    # Логирование
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def database_url_sync(self) -> str:
        """URL для синхронного подключения (для Alembic)"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

