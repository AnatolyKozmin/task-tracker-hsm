from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Игнорировать лишние переменные окружения
    )
    
    # Telegram (опционально для веб-интерфейса)
    bot_token: str = Field(default="", validation_alias="BOT_TOKEN")
    
    # PostgreSQL
    postgres_host: str = Field("db", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(5432, validation_alias="POSTGRES_PORT")
    postgres_user: str = Field("vshu_bot", validation_alias="POSTGRES_USER")
    postgres_password: str = Field(..., validation_alias="POSTGRES_PASSWORD")
    postgres_db: str = Field("vshu_bot_db", validation_alias="POSTGRES_DB")
    
    # Логирование
    log_level: str = Field("INFO", validation_alias="LOG_LEVEL")
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def database_url_sync(self) -> str:
        """URL для синхронного подключения (для Alembic)"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


settings = Settings()

