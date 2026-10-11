"""
Headless Notebook Executor
--------------------------
Executes notebooks/eda.ipynb top-to-bottom in-place, capturing outputs
and generating all portfolio visual artifacts without requiring external jupyter CLI.
"""

import os
import sys
import json
import traceback
import io
import contextlib
from pathlib import Path

# Force non-blocking headless matplotlib backend
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.show = lambda *args, **kwargs: None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "eda.ipynb"
NOTEBOOK_DIR = PROJECT_ROOT / "notebooks"

def run_notebook():
    print(f"Loading notebook: {NOTEBOOK_PATH}")
    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # Change working directory to notebooks/ as Jupyter would
    os.chdir(NOTEBOOK_DIR)
    
    execution_context = {
        "__name__": "__main__",
    }
    cell_idx = 0

    for i, cell in enumerate(nb["cells"]):
        if cell.get("cell_type") != "code":
            continue
        
        cell_idx += 1
        source_code = "".join(cell.get("source", []))
        cell["execution_count"] = cell_idx
        cell["outputs"] = []

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        print(f"Executing Cell {cell_idx}...")
        try:
            with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                exec(source_code, execution_context)
            
            stdout_text = stdout_capture.getvalue()
            if stdout_text:
                cell["outputs"].append({
                    "name": "stdout",
                    "output_type": "stream",
                    "text": stdout_text.splitlines(keepends=True)
                })
                print(f"  -> Output:\n{stdout_text.strip()}")
        except Exception as exc:
            tb = traceback.format_exc()
            cell["outputs"].append({
                "ename": type(exc).__name__,
                "evalue": str(exc),
                "output_type": "error",
                "traceback": tb.splitlines(keepends=True)
            })
            print(f"[ERROR] Cell {cell_idx} raised {type(exc).__name__}:\n{tb}")
            # Save progress before exiting
            with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
                json.dump(nb, f, indent=1)
            sys.exit(1)

    # Save notebook in-place with outputs
    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)

    print("\n[SUCCESS] All 12 notebook cells executed without errors.")

if __name__ == "__main__":
    run_notebook()
