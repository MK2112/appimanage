import os
import shutil
import subprocess
from pathlib import Path
import pytest
from appimanage.main import (
    set_dir, get_dir, unset_dir, list_appimages, move_appimages, create_shortcut, remove_shortcut,
    get_appimages, update_shortcuts, remove_appimage, create_start_menu_shortcuts, create_desktop_shortcuts
)

def test_full_lifecycle(tmp_path, monkeypatch):
    # Set up dirs
    app_dir = tmp_path / 'apps'
    app_dir.mkdir()
    appimage = app_dir / 'sample.AppImage'
    appimage.touch()
    # Set dir
    set_dir(str(app_dir), move=False)
    assert get_dir() == app_dir
    # List
    appimages = get_appimages(app_dir)
    assert len(appimages) == 1
    # Create shortcut
    shortcut_dir = tmp_path / 'shortcuts'
    create_shortcut(appimage, shortcut_dir, force=True)
    shortcut = shortcut_dir / 'sample.desktop'
    assert shortcut.exists()
    # Remove shortcut
    remove_shortcut('sample', shortcut_dir)
    assert not shortcut.exists()
    # Unset dir
    unset_dir()
    assert get_dir() is None

def test_move_appimages_and_update_shortcuts(tmp_path, monkeypatch):
    old_dir = tmp_path / 'oldapps'
    new_dir = tmp_path / 'newapps'
    old_dir.mkdir()
    appimage = old_dir / 'move.AppImage'
    appimage.touch()
    # Create a dummy shortcut referencing old_dir
    shortcut_dir = tmp_path / 'shortcuts'
    shortcut_dir.mkdir()
    shortcut = shortcut_dir / 'move.desktop'
    shortcut.write_text(f"[Desktop Entry]\nName=move\nExec={old_dir}/move.AppImage\nIcon={old_dir}/icon.png\nType=Application\n")
    # Move and update
    move_appimages(old_dir, new_dir)
    assert (new_dir / 'move.AppImage').exists()
    update_shortcuts(str(old_dir), str(new_dir), shortcut_dir)
    updated = shortcut.read_text()
    assert str(new_dir) in updated
    assert str(old_dir) not in updated

def test_remove_appimage_removes_shortcuts(tmp_path, monkeypatch):
    app_dir = tmp_path / 'apps'
    app_dir.mkdir()
    appimage = app_dir / 'remove.AppImage'
    appimage.touch()
    set_dir(str(app_dir), move=False)
    # Create a shortcut
    shortcut_dir = tmp_path / 'shortcuts'
    shortcut_dir.mkdir()
    create_shortcut(appimage, shortcut_dir)
    # Patch MENU_DIR and desktop_dir to our shortcut_dir
    monkeypatch.setattr('appimanage.main.MENU_DIR', shortcut_dir)
    monkeypatch.setattr('subprocess.check_output', lambda *a, **k: str(shortcut_dir).encode())
    # Remove appimage
    remove_appimage('remove')
    assert not (app_dir / 'remove.AppImage').exists()
    assert not (shortcut_dir / 'remove.desktop').exists()
