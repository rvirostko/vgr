import pathlib
import sys

# Ensure the project root is on sys.path for direct imports
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
