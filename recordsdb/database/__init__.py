from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from recordsdb import config

engine = create_engine(
    'postgresql://{username}:{password}@{ip_address}:{port}/{db_name}'.format(**config['db_params'])
)

# Session factory for flask
SessionMaker = sessionmaker(engine)