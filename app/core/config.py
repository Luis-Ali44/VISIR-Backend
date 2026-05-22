from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "Visir API"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000

    supabase_url: str
    supabase_public_key: str
    supabase_secret_key: str


settings = Settings()
