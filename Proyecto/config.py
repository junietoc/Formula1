import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Resolve absolute path to ensure consistent DB file regardless of cwd
BASE_DIR = Path(__file__).resolve().parent
DB_FILENAME = BASE_DIR / "vecirun.db"

# SQLite database URL with absolute path.
# Use three slashes before the path string because the absolute path already starts with "/".
# Example result: sqlite:////Users/yourname/project/vecirun.db
DATABASE_URL = f"sqlite:///{DB_FILENAME}"
