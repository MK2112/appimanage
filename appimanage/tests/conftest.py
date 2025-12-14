import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def user_dirs(monkeypatch, tmp_path_factory):
    desktop_dir = tmp_path_factory.mktemp("desktop")
    menu_dir = tmp_path_factory.mktemp("applications")
    monkeypatch.setattr("appimanage.main.get_desktop_dir", lambda: desktop_dir)
    monkeypatch.setattr("appimanage.main.MENU_DIR", menu_dir)
    return desktop_dir, menu_dir
