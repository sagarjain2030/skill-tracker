import sys
from pathlib import Path

# Add project root to PYTHONPATH so "import app" works reliably
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
