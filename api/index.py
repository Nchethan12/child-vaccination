import os
import sys

# Ensure repo root is importable
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from project.main import app  # noqa: E402

# Vercel looks for a top-level variable named `app`
