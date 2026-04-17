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

    PRODUCTION_API_KEY: str = "replace-with-strong-api-key"
    DATABASE_URL: str = "sqlite:///./alshumookh.db"

    DEFAULT_WALLET_ADDRESS: str = "YOUR_DEFAULT_WALLET_ADDRESS"
    DEFAULT_NETWORK: str = "TRON"
    DEFAULT_TOKEN_SYMBOL: str = "USDT"
    USDT_CONTRACT: str = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    MIN_CONFIRMATIONS: int = 1

    PROVIDER_NAME: str = "onramper"
    PROVIDER_API_KEY: str = ""        # Onramper secret API key (server-to-server)
    PROVIDER_PUBLIC_KEY: str = ""     # Onramper public key (checkout URL)
    PROVIDER_WEBHOOK_SECRET: str = ""

    ALCHEMY_API_KEY: str = ""
    ALCHEMY_WEBHOOK_SECRET: str = ""
    ALCHEMY_CHAIN: str = "TRON"


settings = Settings()
