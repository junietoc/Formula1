import os
from dotenv import load_dotenv

load_dotenv()

# Use SQLite for better Python 3.13 compatibility
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///vecirun.db") 