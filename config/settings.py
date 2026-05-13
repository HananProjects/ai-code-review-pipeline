from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    github_token: str
    github_webhook_secret: str
    claude_model: str = "claude-sonnet-4-6"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
