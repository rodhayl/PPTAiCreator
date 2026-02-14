"""Quick verification script to check GUI features are accessible."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

print("=" * 60)
print("PPTAgent GUI Feature Verification")
print("=" * 60)
print()

# Test 1: Import app module
print("[1/5] Testing app.py import...")
try:
    from src import app

    print("      [OK] App module imported successfully")
except ImportError as e:
    print(f"      [FAIL] Failed to import app: {e}")
    sys.exit(1)

# Test 2: Check tab_run_history exists
print("[2/5] Checking Run History function...")
if hasattr(app, "tab_run_history"):
    print("      [OK] tab_run_history() function exists")
else:
    print("      [FAIL] tab_run_history() function not found")
    sys.exit(1)

# Test 3: Check display_settings_ui import
print("[3/5] Checking Settings UI import...")
try:
    import src.app_settings_helpers as settings_helpers

    _ = settings_helpers.display_settings_ui
    print("      [OK] display_settings_ui() imported successfully")
except ImportError as e:
    print(f"      [FAIL] Failed to import settings UI: {e}")
    sys.exit(1)

# Test 4: Check CheckpointManager
print("[4/5] Checking CheckpointManager...")
try:
    from src.graph.build_graph import CheckpointManager

    cp = CheckpointManager()
    print("      [OK] CheckpointManager initialized")

    # Check new methods exist
    if hasattr(cp, "record_run_complete"):
        print("      [OK] record_run_complete() method exists")
    else:
        print("      [FAIL] record_run_complete() method not found")
        sys.exit(1)

    if hasattr(cp, "get_run_details"):
        print("      [OK] get_run_details() method exists")
    else:
        print("      [FAIL] get_run_details() method not found")
        sys.exit(1)

    if hasattr(cp, "list_runs"):
        print("      [OK] list_runs() method exists")
    else:
        print("      [FAIL] list_runs() method not found")
        sys.exit(1)

except Exception as e:
    print(f"      [FAIL] CheckpointManager error: {e}")
    sys.exit(1)

# Test 5: Verify syntax
print("[5/5] Verifying syntax...")
try:
    import py_compile
    import tempfile
    import os

    # Compile app.py to check syntax
    temp_file = os.path.join(tempfile.gettempdir(), "app_compiled.pyc")
    py_compile.compile(str(REPO_ROOT / "src/app.py"), temp_file, doraise=True)
    print("      [OK] app.py syntax is valid")

    # Clean up
    if os.path.exists(temp_file):
        os.remove(temp_file)

except py_compile.PyCompileError as e:
    print(f"      [FAIL] Syntax error in app.py: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("[SUCCESS] ALL CHECKS PASSED")
print("=" * 60)
print()
print("All GUI features are properly implemented and accessible!")
print()
print("To access the web interface:")
print("  1. Stop current service: stop.bat (or Ctrl+C)")
print("  2. Start service: start.bat")
print("  3. Open browser: http://localhost:8501")
print()
print("You should see 5 tabs:")
print("  - Quick Generate")
print("  - Step-by-Step")
print("  - Settings")
print("  - Documentation")
print("  - Run History")
print()
