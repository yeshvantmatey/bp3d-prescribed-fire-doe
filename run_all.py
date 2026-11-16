"""Reproduce tabular analyses and corrected Figures 4--10 from CSV data."""
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parent
TASKS = ['analysis.py', 'verify_results.py', 'regenerate_fig4.py', 'regenerate_fig5.py',
         'regenerate_fig6.py', 'regenerate_fig7.py', 'regenerate_fig8.py', 'regenerate_fig9_fig10.py']
if __name__ == '__main__':
    for task in TASKS:
        print('Running '+task, flush=True)
        subprocess.run([sys.executable, str(ROOT/'scripts'/task)], cwd=ROOT, check=True)
    print('All calculations, checks and Figures 4--10 completed successfully.')
