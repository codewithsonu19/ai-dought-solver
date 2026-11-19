"""
AI Doubt Solver - One-Click IDLE / Python Runner.

This script allows school students and teachers to run "AI Doubt Solver"
directly from Python IDLE without needing to open PowerShell or Command Prompt.

How to run in Python IDLE:
1. Right-click this file (`run_app.py`) and select "Edit with IDLE"
2. In the IDLE editor window, press F5 (or click Run -> Run Module)
3. Your browser will automatically launch with AI Doubt Solver!
"""

import sys
import os
import subprocess

def launch():
    # Ensure current directory is the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    app_path = os.path.join(script_dir, "app.py")

    print("=" * 60)
    print("🎓 AI Doubt Solver - Launching via Python IDLE...")
    print(f"📁 Working Directory: {script_dir}")
    print("🚀 Starting Web Interface at: http://localhost:8501")
    print("=" * 60)

    try:
        from streamlit.web import cli as stcli
        sys.argv = ["streamlit", "run", app_path, "--server.headless=false"]
        sys.exit(stcli.main())
    except ImportError:
        # Fallback to subprocess if streamlit is in another python path
        print("Note: Starting Streamlit via Python subprocess...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])

if __name__ == "__main__":
    launch()
