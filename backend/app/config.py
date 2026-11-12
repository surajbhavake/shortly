from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env",extra="ignore")

    redis_url:str = "redis://localhost:6379/0"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/shortly"
    base_url: str = "http://localhost:8000"
    link_ttl_seconds: int = 3600

settings = Settings()

    #basically here we are centralizing all the env url so in so use it from
    #one file