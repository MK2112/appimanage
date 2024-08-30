#!/usr/bin/env python3

import os
import shutil
import argparse
import subprocess
import configparser
from pathlib import Path
from xdg_base_dirs import xdg_config_home, xdg_data_home

CONFIG_INI = Path(xdg_config_home()) / "appimanage" / "config.ini"
MENU_DIR = Path(xdg_data_home()) / "applications"

# pip uninstall appimanage
# pip cache purge

def read_config():
    config = configparser.ConfigParser()
    print(CONFIG_INI)
    if CONFIG_INI.exists():
        config.read(CONFIG_INI)
    return config


def write_config(config: configparser.ConfigParser):
    with open(CONFIG_INI, "w") as configfile:
        config.write(configfile)


def set_appimage_dir(new_dir: str):
    config = read_config()
    old_dir = config.get("Settings", "AppImageDir", fallback=None)

    if old_dir == new_dir:
        # Jokes on you
        print(f"AppImage directory is already set to {new_dir}")
        return

    config["Settings"] = {"AppImageDir": new_dir}
    write_config(config)

    if old_dir and Path(old_dir).exists():
        # Recover AppImages if exist, update their desktop entries
        move_appimages(Path(old_dir), Path(new_dir))
        update_desktop_entries(old_dir, new_dir)

    print(f"AppImage directory set to: {new_dir}")


def unset_appimage_dir():
    config = read_config()
    old_dir = config.get("Settings", "AppImageDir", fallback=None)

    if not old_dir:
        print("AppImage directory is not set.")
        return

    config["Settings"] = {"AppImageDir": ""}
    write_config(config)

    print(f"AppImage directory unset from: {old_dir}")


def move_appimages(old_dir: Path, new_dir: Path):
    new_dir.mkdir(parents=True, exist_ok=True)
    for file in old_dir.glob("*.AppImage"):
        shutil.move(str(file), str(new_dir / file.name))
    print(f"Moved AppImages from {old_dir} to {new_dir}")


def update_desktop_entries(old_dir: str, new_dir: str):
    for entry in MENU_DIR.glob("*.desktop"):
        updated = False
        lines = entry.read_text().splitlines()
        for i, line in enumerate(lines):
            if line.startswith("Exec=") and old_dir in line:
                lines[i] = line.replace(old_dir, new_dir)
                updated = (
                    True  # Mark as updated already, icon is next but not as important
                )
            elif line.startswith("Icon=") and old_dir in line:
                lines[i] = line.replace(old_dir, new_dir)
        if updated:
            entry.write_text("\n".join(lines))
    print("Updated desktop entries with new AppImage locations")


def create_desktop_entry(appimage_path: Path):
    name = appimage_path.stem
    icon = get_appimage_icon(appimage_path)
    desktop_file = MENU_DIR / f"{name}.desktop"

    if desktop_file.exists():
        print(f"Desktop entry for {name} already exists. Skipping.")
        return

    entry_content = f"""[Desktop Entry]
                    Name={name}
                    Exec={appimage_path}
                    Icon={icon}
                    Type=Application
                    Categories=Utility;
                    """

    desktop_file.write_text(entry_content)
    os.chmod(desktop_file, 0o755)
    print(f"Created menu entry for {name}")


def get_appimage_icon(appimage_path: Path):
    icon = "application-x-executable"
    extract_dir = appimage_path.parent / "squashfs-root"

    try:
        subprocess.run(
            [str(appimage_path), "--appimage-extract"],
            check=True,
            capture_output=True,
            cwd=str(appimage_path.parent),
        )

        for ext in [".png", ".svg", ".xpm", ".ico"]:
            icon_files = list(extract_dir.rglob(f"*{ext}"))
            if icon_files:
                icon_file = icon_files[0]
                icon_dest = appimage_path.with_name(f"{appimage_path.stem}_icon{ext}")
                shutil.copy2(icon_file, icon_dest)
                icon = str(icon_dest)
                break

    except subprocess.CalledProcessError:
        print(
            f"Failed to extract AppImage icon for {appimage_path}, fallback to default"
        )

    finally:
        if extract_dir.exists():
            shutil.rmtree(extract_dir)

    return icon


def create_start_menu_entries():
    config = read_config()
    appimage_dir = config.get("Settings", "AppImageDir", fallback=None)

    if not appimage_dir:
        print("AppImage directory not set. Use --set first.")
        return

    appimage_dir = Path(appimage_dir)
    if not appimage_dir.exists():
        print(f"AppImage directory {appimage_dir} does not exist.")
        return

    for appimage in appimage_dir.glob("*.AppImage"):
        create_desktop_entry(appimage)


def main():
    parser = argparse.ArgumentParser(description="Manage AppImage programs")
    parser.add_argument("--set", help="Set the AppImage directory")
    parser.add_argument(
        "--startmenu", action="store_true", help="Create start menu entries"
    )
    parser.add_argument(
        "--desktop", help="Create a desktop entry for an AppImage"
    )
    parser.add_argument(
        "--unset", help="Unset the AppImage directory", action="store_true"
    )
    args = parser.parse_args()

    # Make sure config dir exists
    CONFIG_INI.parent.mkdir(parents=True, exist_ok=True)

    # Allow for this to be valid too: "appimanage --set /path/to/dir --startmenu"
    if args.set:
        set_appimage_dir(args.set)

    if args.unset:
        unset_appimage_dir()

    if args.startmenu:
        create_start_menu_entries()


if __name__ == "__main__":
    main()
