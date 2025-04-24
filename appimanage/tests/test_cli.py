import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
import os
import pytest

APPIMANAGE = [sys.executable, '-m', 'appimanage.main']

@pytest.fixture
def temp_appimage_dir(tmp_path):
    # Create a temp directory and a fake AppImage file
    app_dir = tmp_path / 'apps'
    app_dir.mkdir()
    (app_dir / 'test.AppImage').touch()
    return app_dir

def run_cli(args, cwd=None, env=None):
    result = subprocess.run(
        ["appimanage"] + args,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result

def test_set_and_list(tmp_path, monkeypatch):
    config_dir = tmp_path / 'config_home'
    config_dir.mkdir()
    app_dir = tmp_path / 'apps'
    app_dir.mkdir()
    appimage = app_dir / 'test.AppImage'
    appimage.touch()
    # Patch XDG_CONFIG_HOME and XDG_DATA_HOME
    monkeypatch.setenv('XDG_CONFIG_HOME', str(config_dir))
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path / 'xdg_data'))
    # Set dir
    result = run_cli(['--set', str(app_dir)])
    assert 'AppImage directory set' in result.stdout
    # List
    result = run_cli(['--list'])
    assert str(appimage) in result.stdout

def test_unset_and_remove(tmp_path, monkeypatch):
    config_dir = tmp_path / 'config_home'
    config_dir.mkdir()
    app_dir = tmp_path / 'apps'
    app_dir.mkdir()
    appimage = app_dir / 'test.AppImage'
    appimage.touch()
    monkeypatch.setenv('XDG_CONFIG_HOME', str(config_dir))
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path / 'xdg_data'))
    run_cli(['--set', str(app_dir)])
    # Unset
    result = run_cli(['--unset'])
    assert 'AppImage directory unset' in result.stdout
    # Remove (should fail gracefully)
    result = run_cli(['--remove', 'test'])
    assert 'not found' in result.stdout or 'No AppImage directory' in result.stdout

def test_update_stub(tmp_path, monkeypatch):
    config_dir = tmp_path / 'config_home'
    config_dir.mkdir()
    monkeypatch.setenv('XDG_CONFIG_HOME', str(config_dir))
    result = run_cli(['--update'])
    assert '--update is not implemented yet' in result.stdout

def test_invalid_dir(monkeypatch):
    # Should fail gracefully if the dir is invalid
    monkeypatch.setenv('XDG_CONFIG_HOME', '/tmp/doesnotexist')
    result = run_cli(['--list'])
    assert 'No AppImage directory' in result.stdout or 'does not exist' in result.stdout
