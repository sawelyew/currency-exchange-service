from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "ce_core_db"
    # Для Docker - db, для локального - localhost
    DB_HOST: str = "db"
    DB_PORT: int = 5432

    PROJECT_NAME: str = "Currency Exchange Service"
    NBRB_API_URL: str = "https://www.nbrb.by/api/exrates/rates?periodicity=0"
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()