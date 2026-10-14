from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Inventory Manager API"
    database_url: str = "postgresql+psycopg://inventory:inventory@localhost:5432/inventory"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
