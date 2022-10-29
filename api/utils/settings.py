from os import getenv
from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "api"
    mode: str
    dbpath: str

    class Config:
        env_file = f"api/envs/{getenv('MODE')}.env"
