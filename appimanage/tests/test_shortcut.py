import tempfile
import shutil
import os
from pathlib import Path
import pytest
from appimanage.main import create_shortcut, remove_shortcut, get_appimage_icon

def test_create_and_remove_shortcut(tmp_path):
    # Setup fake AppImage
    appimage = tmp_path / 'test.AppImage'
    appimage.touch()
    shortcut_dir = tmp_path / 'shortcuts'
    shortcut_dir.mkdir()
    # Create shortcut
    create_shortcut(appimage, shortcut_dir)
    shortcut = shortcut_dir / 'test.desktop'
    assert shortcut.exists(), 'Shortcut should be created'
    # Remove shortcut
    remove_shortcut('test', shortcut_dir)
    assert not shortcut.exists(), 'Shortcut should be removed'

def test_get_appimage_icon_fallback(tmp_path, monkeypatch):
    # Setup fake AppImage
    appimage = tmp_path / 'fake.AppImage'
    appimage.touch()
    # Patch subprocess.run to always fail
    monkeypatch.setattr('subprocess.run', lambda *a, **kw: (_ for _ in ()).throw(Exception('fail')))
    icon = get_appimage_icon(appimage)
    assert icon == 'application-x-executable'
