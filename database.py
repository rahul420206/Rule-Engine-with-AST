from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base

# Remove `convert_unicode` and update the connection string
engine = create_engine('sqlite:///your_database.db')

# Use sessionmaker to bind the engine and create a session
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

# Base class to define models
Base = declarative_base()
Base.query = db_session.query_property()

# Initialize the database
def init_db():
    import models  # Import your models here to register them
    Base.metadata.create_all(bind=engine)
