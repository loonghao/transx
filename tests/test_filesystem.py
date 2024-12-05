"""Test filesystem module."""
# Import built-in modules
import errno
import os
import shutil
import tempfile

# Import third-party modules
import pytest

# Import local modules
from transx.internal.filesystem import get_gitignore_patterns
from transx.internal.filesystem import is_ignored
from transx.internal.filesystem import walk_with_gitignore


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def mkdir_p(path):
    """Python 2 compatible makedirs with exist_ok behavior."""
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def create_files(base_dir, files):
    """Create test files in the given directory.

    Args:
        base_dir (str): Base directory to create files in
        files (list): List of file paths to create
    """
    for file_path in files:
        full_path = os.path.join(base_dir, file_path.replace("/", os.path.sep))
        mkdir_p(os.path.dirname(full_path))
        with open(full_path, "w") as f:
            f.write("Content of %s" % file_path)


def create_gitignore(base_dir, patterns):
    """Create a .gitignore file with given patterns.

    Args:
        base_dir (str): Base directory to create .gitignore in
        patterns (list): List of patterns to write to .gitignore
    """
    with open(os.path.join(base_dir, ".gitignore"), "w") as f:
        for pattern in patterns:
            f.write(pattern + "\n")


def test_get_gitignore_patterns(temp_dir):
    """Test get_gitignore_patterns function."""
    # Test with non-existent .gitignore
    patterns = get_gitignore_patterns(temp_dir)
    assert patterns == set()

    # Test with empty .gitignore
    create_gitignore(temp_dir, [])
    patterns = get_gitignore_patterns(temp_dir)
    assert patterns == set()

    # Test with patterns
    test_patterns = [
        "*.pyc",
        "__pycache__/",
        "venv/",
        "# Comment",
        "",
        "build/"
    ]
    create_gitignore(temp_dir, test_patterns)
    patterns = get_gitignore_patterns(temp_dir)
    assert patterns == {"*.pyc", "__pycache__/", "venv/", "build/"}


def test_is_ignored(temp_dir):
    """Test is_ignored function."""
    patterns = {"*.pyc", "__pycache__/", "venv/", "build/"}

    # Test file patterns
    assert is_ignored(os.path.join(temp_dir, "test.pyc"), temp_dir, patterns)
    assert not is_ignored(os.path.join(temp_dir, "test.py"), temp_dir, patterns)

    # Test directory patterns
    # Create directories to test with
    mkdir_p(os.path.join(temp_dir, "__pycache__"))
    mkdir_p(os.path.join(temp_dir, "venv"))
    mkdir_p(os.path.join(temp_dir, "src"))

    assert is_ignored(os.path.join(temp_dir, "__pycache__"), temp_dir, patterns)
    assert is_ignored(os.path.join(temp_dir, "venv"), temp_dir, patterns)
    assert not is_ignored(os.path.join(temp_dir, "src"), temp_dir, patterns)

    # Test nested paths
    nested_dir = os.path.join(temp_dir, "src", "__pycache__")
    mkdir_p(nested_dir)
    assert is_ignored(os.path.join(nested_dir, "test.py"), temp_dir, patterns)
    assert is_ignored(os.path.join(temp_dir, "src", "test.pyc"), temp_dir, patterns)
    assert not is_ignored(os.path.join(temp_dir, "src", "test.py"), temp_dir, patterns)


def test_walk_with_gitignore(temp_dir):
    """Test walk_with_gitignore function."""
    # Create test files
    test_files = [
        "src/main.py",
        "src/test.pyc",
        "src/__pycache__/cache.py",
        "src/subdir/module.py",
        "src/subdir/module.pyc",
        "venv/bin/python",
        "build/output.txt",
        "docs/index.md"
    ]
    create_files(temp_dir, test_files)

    # Create .gitignore
    gitignore_patterns = [
        "*.pyc",
        "__pycache__/",
        "venv/",
        "build/"
    ]
    create_gitignore(temp_dir, gitignore_patterns)

    # Test without file patterns
    files = walk_with_gitignore(temp_dir)
    expected_files = {
        os.path.join(temp_dir, "src", "main.py"),
        os.path.join(temp_dir, "src", "subdir", "module.py"),
        os.path.join(temp_dir, "docs", "index.md")
    }
    assert set(files) == expected_files

    # Test with Python file pattern
    files = walk_with_gitignore(temp_dir, ["*.py"])
    expected_files = {
        os.path.join(temp_dir, "src", "main.py"),
        os.path.join(temp_dir, "src", "subdir", "module.py")
    }
    assert set(files) == expected_files

    # Test with markdown file pattern
    files = walk_with_gitignore(temp_dir, ["*.md"])
    expected_files = {
        os.path.join(temp_dir, "docs", "index.md")
    }
    assert set(files) == expected_files

    # Test with non-matching pattern
    files = walk_with_gitignore(temp_dir, ["*.txt"])
    assert not files  # Should be empty list


def test_walk_with_gitignore_no_gitignore(temp_dir):
    """Test walk_with_gitignore function when .gitignore doesn't exist."""
    # Create test files
    test_files = [
        "src/main.py",
        "src/test.pyc",
        "src/__pycache__/cache.py"
    ]
    create_files(temp_dir, test_files)

    # Test without .gitignore file
    files = walk_with_gitignore(temp_dir, ["*.py"])
    expected_files = {
        os.path.join(temp_dir, "src", "main.py"),
        os.path.join(temp_dir, "src", "__pycache__", "cache.py")
    }
    assert set(files) == expected_files
