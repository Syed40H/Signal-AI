"""Manual trigger for local testing: `python scripts/run_pipeline.py`."""

import sys
from pathlib import Path

# Let this run from anywhere without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
