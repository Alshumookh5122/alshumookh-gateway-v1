from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "ALSHUMOOKH GLOBAL BANKING FINANCE AND CREDIT"
    APP_VERSION: str = "1.0.0"

    ALCHEMY_API_KEY: str = ""
    ALCHEMY_CHAIN: str = "TRON"
    ALCHEMY_WEBHOOK_SECRET: str = ""

    DEFAULT_WALLET_ADDRESS: str = ""
    DEFAULT_TOKEN_SYMBOL: str = "USDT"
    DEFAULT_NETWORK: str = "TRON"
    USDT_CONTRACT: str = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    MIN_CONFIRMATIONS: int = 1


settings = Settings()
