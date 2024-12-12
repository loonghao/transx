# Import built-in modules
import os

# Import third-party modules
import nox
from nox_actions.utils import PACKAGE_NAME
from nox_actions.utils import THIS_ROOT


def pytest(session: nox.Session) -> None:
    """Run the test suite."""
    session.install(".")
    session.install("pytest", "pytest_cov", "pytest_mock", "pytest-benchmark")
    test_root = os.path.join(THIS_ROOT, "tests")
    session.run("pytest", f"--cov={PACKAGE_NAME}",
                "--cov-report=xml:coverage.xml",
                f"--rootdir={test_root}",
                "--cov-report=term-missing",
                env={"PYTHONPATH": THIS_ROOT.as_posix()})


def benchmark(session: nox.Session) -> None:
    """Run benchmarks."""
    session.install(".")
    session.install("pytest", "pytest-benchmark")
    session.run(
        "pytest",
        "tests/benchmarks/",
        "--benchmark-only",
        "--benchmark-json=output.json",
        env={"PYTHONPATH": THIS_ROOT.as_posix()},
    )
