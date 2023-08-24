import string
from typing import Literal

import pydantic
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # application settings
    manager_ip_addresses: list[str] = []
    participate_max_attempts: pydantic.PositiveInt = 3
    participate_ticket_pool: pydantic.PositiveInt = 10
    verification_code_allowed_characters: str = string.ascii_uppercase
    verification_code_crypt_algorithm: Literal["bf", "des", "md5", "xdes"] = "bf"
    verification_code_length: pydantic.PositiveInt = 8

    # database settings
    db_database: str = Field(alias="PGDATABASE")
    db_host: str = Field(alias="PGHOST")
    db_password: pydantic.SecretStr = Field(alias="PGPASSWORD")
    db_port: str = Field(alias="PGPORT")
    db_user: str = Field(alias="PGUSER")

    model_config = SettingsConfigDict(env_file=".env")

    def __hash__(self):
        return hash(repr(self))

    @property
    def db_url(self) -> str:
        return (
            "postgresql://"
            f"{self.db_user}:{self.db_password.get_secret_value()}@"
            f"{self.db_host}:{self.db_port}/{self.db_database}"
        )


def load_settings(**kwargs) -> Settings:
    return Settings(**kwargs)
