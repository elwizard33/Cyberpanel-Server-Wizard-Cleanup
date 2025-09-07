import sys
from pathlib import Path

# Ensure project root on path for tests without installing package
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
