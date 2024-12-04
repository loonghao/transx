# Import built-in modules
import os
import sys


# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

# Run all workflow scripts
workflow_scripts = [
    "01_extract_messages.py",
    "02_update_translations.py",
    "03_translate_messages.py",
    "04_compile_translations.py"
]

root = os.path.dirname(__file__)
workflow_root = os.path.join(root, "workflow")
sys.path.insert(0, workflow_root)

for script in workflow_scripts:
    full_path = os.path.join(root, "workflow", script)
    print("\nRunning {}...".format(full_path))
    with open(full_path) as f:
        exec(f.read())
