from __future__ import annotations

import shutil
import sys
import uuid
from pathlib import Path

import _pytest.pathlib
import _pytest.tmpdir
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
TEST_TMP_ROOT = WORKSPACE_ROOT / "runtime" / "unit_test_tmp"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def pytest_configure() -> None:
    # Windows in this workspace can make pytest basetemp directories unreadable
    # during session teardown. Disabling the dead-symlink cleanup keeps tmp_path
    # fixtures usable and avoids false negatives in self-check.
    _pytest.pathlib.cleanup_dead_symlinks = lambda root: None
    _pytest.tmpdir.cleanup_dead_symlinks = lambda root: None


@pytest.fixture
def tmp_path() -> Path:
    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    path = TEST_TMP_ROOT / f"case_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
