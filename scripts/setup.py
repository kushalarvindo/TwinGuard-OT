"""
Setup and Environment Verification Script for TwinGuard-OT.
Verifies dependencies, initializes directory hierarchy, and performs database smoke tests.
"""

import sys
from pathlib import Path

# Configure utf-8 stdout for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure src is importable
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "src"))

from twinguard.utils.config import load_system_config, get_project_root
from twinguard.database.db import DatabaseManager


def verify_dependencies():
    print("=== TwinGuard-OT: Verifying Dependencies ===")
    required_packages = [
        "pymodbus",
        "numpy",
        "pandas",
        "sklearn",
        "scipy",
        "yaml",
        "streamlit",
        "plotly",
        "joblib",
        "pytest",
    ]
    all_ok = True
    for pkg in required_packages:
        try:
            mod = __import__(pkg)
            version = getattr(mod, "__version__", "unknown")
            print(f"  [+] {pkg:<12}: OK (version {version})")
        except ImportError as e:
            print(f"  [!] {pkg:<12}: MISSING ({e})")
            all_ok = False

    if not all_ok:
        print("\nError: Missing dependencies. Please run: pip install -r requirements.txt")
        sys.exit(1)
    print("All required packages are installed and functional.\n")


def setup_workspace():
    print("=== TwinGuard-OT: Setting Up Workspace & Storage ===")
    root = get_project_root()
    config = load_system_config()

    # Ensure directories
    for dir_key in ["raw_dir", "processed_dir", "models_dir", "results_dir"]:
        p = root / config["storage"][dir_key]
        p.mkdir(parents=True, exist_ok=True)
        print(f"  [+] Directory verified: {p}")

    # Initialize SQLite database
    db_path = config["storage"]["db_path_resolved"]
    db = DatabaseManager(db_path)
    print(f"  [+] SQLite Database initialized at: {db_path}")

    # Self-test: Tank & Physics smoke check
    from twinguard.process.tank import WaterTank
    tank = WaterTank(initial_level=50.0)
    state = tank.step(dt=0.1)
    assert abs(state["true_level"] - 50.0) < 1.0
    print("  [+] Physical simulation smoke test passed.")

    print("\nTwinGuard-OT environment is ready to run!")


if __name__ == "__main__":
    verify_dependencies()
    setup_workspace()
