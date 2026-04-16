from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "ALSHUMOOKH GLOBAL BANKING FINANCE & CREDIT"
    ALCHEMY_API_KEY: str = ""
    WALLET_ADDRESS: str = ""


settings = Settings()
