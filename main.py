#!/usr/bin/env python3
"""
Simple launcher for the application.
Usage: python3 main.py
"""

try:
    from gui_main import main as run_app
except Exception as e:
    # Provide a clearer error if import fails
    import sys, traceback
    sys.stderr.write(f"Failed to import gui_main: {e}\n")
    traceback.print_exc()
    raise


if __name__ == "__main__":
    run_app()

