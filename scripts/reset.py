"""
System Reset and Data Cleanup Script for TwinGuard-OT.
Clears SQLite records and resets models/results to return project to clean state.
Does NOT delete source code.
"""

import sys
from pathlib import Path

# Configure utf-8 stdout for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add src to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "src"))

from twinguard.utils.config import load_system_config, get_project_root
from twinguard.database.db import DatabaseManager


def reset_system():
    print("=== TwinGuard-OT: Resetting System State ===")
    config = load_system_config()
    root = get_project_root()

    # 1. Reset SQLite Database
    db_path = config["storage"]["db_path_resolved"]
    db = DatabaseManager(db_path)
    db.reset_all_data()
    print(f"  [+] SQLite database tables cleared at: {db_path}")

    # 2. Clear generated result CSVs and JSONs (preserving directory)
    results_dir = root / config["storage"].get("results_dir", "data/results")
    if results_dir.exists():
        for f in results_dir.glob("*.*"):
            if f.name != ".gitkeep":
                f.unlink()
        print(f"  [+] Cleared results in: {results_dir}")

    # 3. Clear processed baseline CSVs
    processed_dir = root / config["storage"].get("processed_dir", "data/processed")
    if processed_dir.exists():
        for f in processed_dir.glob("*.csv"):
            f.unlink()
        print(f"  [+] Cleared processed baselines in: {processed_dir}")

    print("\nTwinGuard-OT system successfully reset to clean state.")


if __name__ == "__main__":
    reset_system()
