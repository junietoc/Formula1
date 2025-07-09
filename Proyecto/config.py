import os
from dotenv import load_dotenv

load_dotenv()

# Force SQLite for better compatibility and to avoid encoding issues
DATABASE_URL = "sqlite:///vecirun.db" 