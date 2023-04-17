import os
from pydantic import BaseModel as pydBaseModel, BaseSettings, validator, Extra
from typing import Optional


class BaseModel(pydBaseModel):
    listen_ip: str
    listen_port: int


class NetworkKeyModel(pydBaseModel):
    n: int
    d: int


class DatabaseModel(pydBaseModel):
    driver: Optional[str] = 'postgresql'
    host: str
    port: int
    database: str
    username: str
    password: str


class Global(pydBaseModel):
    network_key: NetworkKeyModel
    primary_key: NetworkKeyModel
    database: DatabaseModel


class DirectoryBase(BaseModel):
    servers: dict


class ConfigServer(BaseModel):
    pdr_path: str
    cdr_path: str

    @validator('pdr_path', allow_reuse=True)
    @validator('cdr_path', allow_reuse=True)
    def path_exists(cls, path):
        if not os.path.exists(path):
            raise ValueError(f'Path {path} does not exist')
        return path

class Settings(BaseSettings):
    directory_server: DirectoryBase
    config_server: ConfigServer
    content_list_server: DirectoryBase
    cser: BaseModel
    auth_server: BaseModel
    universe: Global # What the fuck is Python on?

    class Config(BaseSettings.Config):
        extra = Extra.allow
