import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import configparser
import tempfile
import random
import shutil
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from appimanage.main import (
    read_config,
    write_config,
    get_appimages,
    set_dir,
    get_dir,
    unset_dir,
    list_appimages,
    move_appimages,
    update_shortcuts,
    get_appimage_icon,
    create_shortcut,
    remove_shortcut,
    remove_appimage,
)

# pip install -e .
# pip install pytest
# pytest appimanage/tests

class TestAppimanage(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_path = Path(self.test_dir) / "config.ini"
        # Mock Config 
        patcher = patch("appimanage.main.CONFIG_INI", self.config_path)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_read_write_config(self):
        config = configparser.ConfigParser()
        config["Settings"] = {"AppImageDir": "/test/path"}
        write_config(config)
        read_config_result = read_config()
        self.assertEqual(read_config_result["Settings"]["AppImageDir"], "/test/path")

    def test_get_appimages(self):
        app_dir = Path(self.test_dir) / "apps"
        app_dir.mkdir()
        (app_dir / "app1.AppImage").touch()
        (app_dir / "app2.AppImage").touch()
        (app_dir / "not_an_appimage.txt").touch()
        appimages = get_appimages(app_dir)
        self.assertEqual(len(appimages), 2)
        self.assertTrue(all(str(a).endswith(".AppImage") for a in appimages))

    def test_set_dir(self):
        with patch('appimanage.main.read_config') as mock_read_config, \
             patch('appimanage.main.write_config') as mock_write_config, \
             patch('appimanage.main.move_appimages') as mock_move_appimages:
            
            mock_config = configparser.ConfigParser()
            tmp_path_old, tmp_path_new = [tempfile.mkdtemp(), tempfile.mkdtemp()]
            mock_config['Settings'] = {'AppImageDir': tmp_path_old}
            mock_read_config.return_value = mock_config

            set_dir(tmp_path_new, move=True)

            mock_write_config.assert_called_once()
            self.assertEqual(mock_config['Settings']['AppImageDir'], tmp_path_new)
            mock_move_appimages.assert_called_once_with(Path(tmp_path_old), Path(tmp_path_new))

    def test_get_dir_error(self):
        with patch('appimanage.main.read_config', return_value=configparser.ConfigParser()):
            self.assertIsNone(get_dir())

    def test_unset_dir_error(self):
        with patch('appimanage.main.read_config', return_value=configparser.ConfigParser()):
            # Should not raise
            unset_dir()

    def test_move_appimages_error(self):
        # Should print error if old_dir does not exist
        from appimanage.main import move_appimages
        tmp = Path(self.test_dir) / 'idontexist'
        new = Path(self.test_dir) / 'new'
        move_appimages(tmp, new)
        # Should not raise

    def test_update_shortcuts_logic(self):
        from appimanage.main import update_shortcuts
        shortcut_dir = Path(self.test_dir) / 'shortcuts'
        shortcut_dir.mkdir()
        shortcut = shortcut_dir / 'test.desktop'
        old_dir = '/old/path'
        new_dir = '/new/path'
        shortcut.write_text(f"[Desktop Entry]\nExec={old_dir}/foo\nIcon={old_dir}/icon.png\n")
        update_shortcuts(old_dir, new_dir, shortcut_dir)
        content = shortcut.read_text()
        self.assertIn(new_dir, content)
        self.assertNotIn(old_dir, content)

    def test_remove_appimage_not_found(self):
        from appimanage.main import remove_appimage
        # Should print not found, not raise
        remove_appimage('notfound')

if __name__ == "__main__":
    unittest.main()