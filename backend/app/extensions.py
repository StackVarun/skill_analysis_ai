"""Re-export extensions for convenience."""
import os
import sys

# Ensure backend root is on python path
_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from extensions import db, migrate, jwt, cors

__all__ = ["db", "migrate", "jwt", "cors"]
