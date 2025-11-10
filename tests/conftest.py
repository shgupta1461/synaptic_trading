# tests/conftest.py
import os, sys
# Add project root (the folder that contains `src/` and `tests/`) to sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
