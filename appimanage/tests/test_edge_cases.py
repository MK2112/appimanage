import os
import shutil
import tempfile
import stat
from pathlib import Path
import pytest
from appimanage.main import (
    create_shortcut, remove_shortcut, get_appimage_icon, set_dir, write_config, read_config,
    create_start_menu_shortcuts, create_desktop_shortcuts, remove_appimage, get_dir
)

# Test: Corrupted .desktop file handling
def test_corrupted_desktop_file(tmp_path):
    shortcut_dir = tmp_path / 'shortcuts'
    shortcut_dir.mkdir()
    shortcut = shortcut_dir / 'corrupt.desktop'
    shortcut.write_text('NOT A DESKTOP FILE')
    # Should not raise when updating shortcuts
    from appimanage.main import update_shortcuts
    update_shortcuts('/old/path', '/new/path', shortcut_dir)
    assert shortcut.exists()

# Test: Permission error when writing config
def test_write_config_permission_error(monkeypatch, tmp_path):
    config = read_config()
    config['Settings'] = {'AppImageDir': str(tmp_path)}
    # Make parent dir read-only
    config_dir = tmp_path / 'appimanage'
    config_dir.mkdir()
    config_file = config_dir / 'config.ini'
    config_file.touch()
    config_dir.chmod(0o400)
    monkeypatch.setattr('appimanage.main.CONFIG_INI', config_file)
    with pytest.raises(PermissionError):
        write_config(config)
    config_dir.chmod(0o700)

# Test: create_start_menu_shortcuts and create_desktop_shortcuts
@pytest.mark.parametrize('func', [create_start_menu_shortcuts, create_desktop_shortcuts])
def test_create_menu_and_desktop_shortcuts(tmp_path, func, monkeypatch):
    # Should not raise even if no AppImage dir is set
    monkeypatch.setattr('appimanage.main.get_dir', lambda: None)
    func()
    # Now set a dir with no AppImages
    set_dir(str(tmp_path), move=False)
    func()

# Test: remove_appimage when shortcut removal fails
def test_remove_appimage_shortcut_failure(tmp_path, monkeypatch):
    app_dir = tmp_path / 'apps'
    app_dir.mkdir()
    appimage = app_dir / 'fail.AppImage'
    appimage.touch()
    set_dir(str(app_dir), move=False)
    # Patch remove_shortcut to raise OSError
    monkeypatch.setattr('appimanage.main.remove_shortcut', lambda *a, **k: (_ for _ in ()).throw(OSError('fail')))
    # Should not raise
    remove_appimage('fail')

# Test: AppImage with special characters in name
def test_appimage_special_characters(tmp_path):
    app_dir = tmp_path / 'apps'
    app_dir.mkdir()
    special_name = 'üñîçødë space @!#.AppImage'
    appimage = app_dir / special_name
    appimage.touch()
    shortcut_dir = tmp_path / 'shortcuts'
    shortcut_dir.mkdir()
    create_shortcut(appimage, shortcut_dir)
    shortcut = shortcut_dir / f'{appimage.stem}.desktop'
    assert shortcut.exists()
    remove_shortcut(appimage.stem, shortcut_dir)
    assert not shortcut.exists()

# Test: Concurrent move and list (simulate by calling in quick succession)
def test_move_and_list_concurrent(tmp_path):
    old_dir = tmp_path / 'oldapps'
    new_dir = tmp_path / 'newapps'
    old_dir.mkdir()
    appimage = old_dir / 'move.AppImage'
    appimage.touch()
    from appimanage.main import move_appimages, list_appimages
    move_appimages(old_dir, new_dir)
    # Should not raise
    list_appimages()
