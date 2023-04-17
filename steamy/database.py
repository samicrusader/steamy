import yaml
from .configparser import Settings
from sqlalchemy import Boolean, create_engine, Column, Integer, LargeBinary, String
from sqlalchemy.engine.url import URL as database_uri
from sqlalchemy.ext.declarative import declarative_base

settings = Settings.parse_obj(yaml.safe_load(open('config.yaml')))

db_uri = database_uri.create(
    drivername=settings.universe.database.driver,
    username=settings.universe.database.username,
    password=settings.universe.database.password,
    database=settings.universe.database.database,
    host=settings.universe.database.host,
    port=settings.universe.database.port
)

engine = create_engine(db_uri)
Modal = declarative_base()


# https://developer.valvesoftware.com/wiki/SteamID
class User(Modal):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False, unique=True)  # FIXME: This should be changed to use the Steam ID format
    username = Column(String(64), nullable=False, unique=True)  # Account name
    nickname = Column(String(32), nullable=True, unique=False)  # Community nickname TODO: Implement
    email = Column(String(65), nullable=False, unique=True)
    disabled = Column(Boolean, nullable=False, unique=False)
    key = Column(LargeBinary, nullable=False, unique=False)
    salt = Column(LargeBinary, nullable=False, unique=False)
    password = Column(LargeBinary, nullable=False, unique=False)
    recovery_question = Column(LargeBinary, nullable=False, unique=False)
    recovery_answer = Column(LargeBinary, nullable=False, unique=False)
    unknown_data = Column(LargeBinary, nullable=False, unique=False)  # ??


Modal.metadata.create_all(engine)