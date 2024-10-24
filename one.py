from database import engine, Base
from models import UserInput

# Create all tables in the database
Base.metadata.create_all(engine)
