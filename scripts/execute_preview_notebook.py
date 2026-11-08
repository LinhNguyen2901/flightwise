"""Execute the editable M1.6 notebook from a fresh project-local Python kernel."""
import asyncio
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT / '.jupyter_runtime'
runtime.mkdir(exist_ok=True)
os.environ['JUPYTER_RUNTIME_DIR'] = str(runtime)
os.environ['IPYTHONDIR'] = str(runtime / 'ipython')
if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import nbformat
from nbclient import NotebookClient

path = ROOT / 'notebooks/dashboard_preview.ipynb'
notebook = nbformat.read(path, as_version=4)
try:
    NotebookClient(notebook, timeout=600, kernel_name='python3',
                   resources={'metadata': {'path': str(ROOT)}}).execute()
finally:
    nbformat.write(notebook, path)
print(f'Executed and saved {path}', flush=True)
