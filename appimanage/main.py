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

# pip uninstall appimanage -y
# pip cache purge
# pip install -e .


def read_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    if CONFIG_INI.exists():
        config.read(CONFIG_INI)
    return config


def write_config(config: configparser.ConfigParser) -> None:
    with open(CONFIG_INI, "w") as configfile:
        config.write(configfile)


def get_appimages(appimage_dir: Path) -> list:
    appimages = []
    for root, _, files in os.walk(appimage_dir):
        for file in files:
            if file.endswith(".AppImage"):
                appimages.append(os.path.join(root, file))
    return appimages


def set_dir(new_dir: str, move: bool) -> None:
    config = read_config()
    old_dir = config.get("Settings", "AppImageDir", fallback=None)

    if old_dir == new_dir:
        # very funny
        print(f"[!] AppImage directory already set to {new_dir}")
        return

    config["Settings"] = {"AppImageDir": new_dir}
    write_config(config)

    if old_dir and Path(old_dir).exists() and move:
        # Recover AppImages if exist, update their desktop entries
        move_appimages(Path(old_dir), Path(new_dir))

    print(f"[~] AppImage directory set to {new_dir}")


def get_dir():
    config = read_config()
    appimage_dir = config.get("Settings", "AppImageDir", fallback=None)

    if not appimage_dir:
        print("[!] No AppImage directory not set. Set with --set first.")
        return

    appimage_dir = Path(appimage_dir)
    if not appimage_dir.exists():
        print(f"[!] AppImage directory {appimage_dir} does not exist.")
        return

    return appimage_dir


def unset_dir():
    config = read_config()
    old_dir = config.get("Settings", "AppImageDir", fallback=None)

    if not old_dir:
        print("[!] No AppImage directory not set. Set with --set first.")
        return

    config["Settings"] = {"AppImageDir": ""}
    write_config(config)

    print(f"[~] AppImage directory unset from {old_dir}")


def list_appimages():
    config = read_config()
    appimage_dir = config.get("Settings", "AppImageDir", fallback=None)

    if not appimage_dir:
        print("[!] No AppImage directory not set. Set with --set first.")
        return

    appimage_dir = Path(appimage_dir)
    if not appimage_dir.exists():
        print(f"[!] AppImage directory {appimage_dir} does not exist.")
        return

    print("[~] AppImages:")
    print(f"\t{path}" for path in get_appimages(appimage_dir))


def move_appimages(old_dir: Path, new_dir: Path):
    new_dir.mkdir(parents=True, exist_ok=True)
    for file in old_dir.glob("*.AppImage"):
        shutil.move(str(file), str(new_dir / file.name))
    # Update start menu entries
    update_shortcuts(str(old_dir), str(new_dir), MENU_DIR)
    # Update desktop entries
    update_shortcuts(
        str(old_dir),
        str(new_dir),
        Path(subprocess.check_output(["xdg-user-dir", "DESKTOP"]).decode().strip()),
    )
    print(f"[~] Moved AppImages from {old_dir} to {new_dir}")


def update_shortcuts(old_dir: str, new_dir: str, shortcut_dir: Path):
    for entry in shortcut_dir.glob("*.desktop"):
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
            icon_files = list(extract_dir.rglob(f"*{ext}")) + list(
                extract_dir.rglob(f"*{ext.upper()}")
            )
            if icon_files:
                icon_dest = appimage_path.with_name(f"{appimage_path.stem}_icon{ext}")
                shutil.copy2(icon_files[0], icon_dest)
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


def create_shortcut(appimage_path: Path, shortcut_dir: Path):
    name = appimage_path.stem
    icon = get_appimage_icon(appimage_path)
    shortcut = shortcut_dir / f"{name}.desktop"
    if shortcut.exists():
        return
    entry_content = f"""[Desktop Entry]
                    Name={name}
                    Exec={appimage_path}
                    Icon={icon}
                    Type=Application
                    Categories=Utility;
                    """
    shortcut.write_text(entry_content)
    os.chmod(shortcut, 0o755)


def create_start_menu_shortcuts():
    appimage_dir = get_dir()
    # Keeping track of this history-wise is not really needed, just override
    for appimage in get_appimages(appimage_dir):
        create_shortcut(appimage, MENU_DIR)


def create_desktop_shortcuts():
    appimage_dir = get_dir()
    desktop_dir = Path(
        subprocess.check_output(["xdg-user-dir", "DESKTOP"]).decode().strip()
    )
    # Keeping track of this history-wise is not really needed, we just override
    for appimage in get_appimages(appimage_dir):
        create_shortcut(appimage, desktop_dir)


def remove_shortcut(appimage: str, shortcut_dir: Path):
    shortcut = shortcut_dir / f"{appimage}.desktop"
    if shortcut.exists():
        shortcut.unlink()


def remove_appimage(appimage):
    appimage_dir = get_dir()
    appimages = get_appimages(appimage_dir)

    for path in appimages:
        # path.stem :: /path/to/XYZ.AppImage -> XYZ
        if path.stem.lower() == appimage.lower():
            # Remove .AppImage
            appimage = path.stem
            path.unlink()
            # Remove links from start menu and desktop
            remove_shortcut(appimage, MENU_DIR)
            remove_shortcut(
                appimage,
                Path(
                    subprocess.check_output(["xdg-user-dir", "DESKTOP"])
                    .decode()
                    .strip()
                ),
            )
            print(f"Removed {appimage}")
            break

    print(f"{appimage} not found in AppImage directory")


def main():
    parser = argparse.ArgumentParser(description="Manage AppImage programs")
    parser.add_argument("--set", metavar="PATH", help="Set the AppImage directory")
    parser.add_argument(
        "--unset",
        action="store_true",
        help="Unset the previously set AppImage directory",
    )
    parser.add_argument(
        "--list", action="store_true", help="List all currently managed AppImages"
    )
    parser.add_argument(
        "--startmenu",
        action="store_true",
        help="Create start menu entries, remove for AppImages not existing anymore",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Move AppImages from old directory to new one",
    )
    parser.add_argument(
        "--desktop", action="store_true", help="Create desktop icons for all AppImages"
    )
    parser.add_argument(
        "--remove", metavar="APPIMAGE", help="Remove an AppImage and its links"
    )

    args, _ = parser.parse_known_args()

    # Processing in order of occurrence
    for action, value in [
        (action, value) for action, value in vars(args).items() if value
    ]:
        {
            "set": lambda: set_dir(value, args.move),
            "unset": unset_dir,
            "startmenu": create_start_menu_shortcuts,
            "desktop": create_desktop_shortcuts,
            "list": list_appimages,
            "remove": lambda: remove_appimage(value),
        }[action]()


if __name__ == "__main__":
    main()
