import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import configparser
import tempfile
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

class TestAppimanage(unittest.TestCase):

    def setUp(self):
        # Create testing dir
        self.test_dir = tempfile.mkdtemp()
        self.config_path = Path(self.test_dir) / "config.ini"
        
        # Mock CONFIG_INI constant
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

if __name__ == "__main__":
    unittest.main()