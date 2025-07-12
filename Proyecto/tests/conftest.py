import sys
from pathlib import Path

# Ensure the project root directory is on sys.path so that `import models` and other
# top-level modules can be imported inside the test suite, even when tests are
# executed from within the `tests/` directory.
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
