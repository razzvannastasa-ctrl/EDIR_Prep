import subprocess, sys
from pathlib import Path

subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"],
               cwd=Path(__file__).parent)
