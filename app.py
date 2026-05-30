"""Entrypoint to run the Phase 5 Streamlit Dashboard."""
from __future__ import annotations

import sys
from pathlib import Path

# Add current directory to path just in case
sys.path.insert(0, str(Path(__file__).resolve().parent))

from phase5.dashboard import main

if __name__ == "__main__":
    main()
