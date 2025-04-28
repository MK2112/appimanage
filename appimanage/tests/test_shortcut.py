import tempfile
import shutil
import os
from pathlib import Path
import pytest
from appimanage.main import create_shortcut, remove_shortcut, get_appimage_icon

import pytest
from appimanage.main import update_shortcuts

@pytest.mark.parametrize('name', ['test', 'Test Space', '123', 'üñîçødë', 'test.AppImage'])
def test_create_and_remove_shortcut(tmp_path, name):
    appimage = tmp_path / f'{name}.AppImage'
    appimage.touch()
    shortcut_dir = tmp_path / 'shortcuts'
    shortcut_dir.mkdir()
    create_shortcut(appimage, shortcut_dir)
    shortcut = shortcut_dir / f'{appimage.stem}.desktop'
    assert shortcut.exists(), f'Shortcut should be created for {name}'
    remove_shortcut(appimage.stem, shortcut_dir)
    assert not shortcut.exists(), f'Shortcut should be removed for {name}'

def test_create_shortcut_force_overwrite(tmp_path):
    appimage = tmp_path / 'force.AppImage'
    appimage.touch()
    shortcut_dir = tmp_path / 'shortcuts'
    shortcut_dir.mkdir()
    create_shortcut(appimage, shortcut_dir)
    shortcut = shortcut_dir / 'force.desktop'
    shortcut.write_text('original')
    create_shortcut(appimage, shortcut_dir, force=True)
    assert shortcut.exists()
    assert 'original' not in shortcut.read_text()

def test_update_shortcuts_multiple(tmp_path):
    shortcut_dir = tmp_path / 'shortcuts'
    shortcut_dir.mkdir()
    old_dir = '/old/path'
    new_dir = '/new/path'
    for i in range(3):
        s = shortcut_dir / f'app{i}.desktop'
        s.write_text(f"[Desktop Entry]\nExec={old_dir}/app{i}.AppImage\nIcon={old_dir}/icon.png\n")
    update_shortcuts(old_dir, new_dir, shortcut_dir)
    for i in range(3):
        s = shortcut_dir / f'app{i}.desktop'
        content = s.read_text()
        assert new_dir in content
        assert old_dir not in content

def test_get_appimage_icon_fallback(tmp_path, monkeypatch):
    # Setup fake AppImage
    appimage = tmp_path / 'fake.AppImage'
    appimage.touch()
    # Patch subprocess.run to always fail
    monkeypatch.setattr('subprocess.run', lambda *a, **kw: (_ for _ in ()).throw(Exception('fail')))
    icon = get_appimage_icon(appimage)
    assert icon == 'application-x-executable'
