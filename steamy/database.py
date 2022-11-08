from sqlalchemy import LargeBinary, create_engine, Column, Integer, String
from sqlalchemy.engine.url import URL as database_uri
from sqlalchemy.ext.declarative import declarative_base

db_uri = database_uri.create(
    drivername='postgresql+psycopg2',
    username='samicrusader',
    password='password',
    database='steamy',
    host='127.0.0.1',
    port=5432
)

engine = create_engine(db_uri)
Modal = declarative_base()


# https://developer.valvesoftware.com/wiki/SteamID
class User(Modal):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)  # FIXME: This should be changed to use the Steam ID format
    username = Column(String(32))  # Account name FIXME: This should be changed to 63
    nickname = Column(String(32))  # Community name
    iv = Column(LargeBinary)


Modal.metadata.create_all(engine)