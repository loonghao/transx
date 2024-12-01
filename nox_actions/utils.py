# Import built-in modules
from pathlib import Path


PACKAGE_NAME = ""
THIS_ROOT = Path(__file__).parent.parent
PROJECT_ROOT = THIS_ROOT.parent
PYTHON_VERSIONS = [ 
        "2.7",
        "3.2",
        "3.3",
        "3.4",
        "3.5",
        "3.6",
        "3.7",
        "3.8",
        "3.9",
        "3.10",
        "3.11",
        "3.12",
        "3.13"
]

def _assemble_env_paths(*paths):
    """Assemble environment paths separated by a semicolon.

    Args:
        *paths: Paths to be assembled.

    Returns:
        str: Assembled paths separated by a semicolon.
    """
    return ";".join(paths)
