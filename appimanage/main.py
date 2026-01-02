#!/usr/bin/env python3

import os
import time
import shutil
import argparse
import logging
import subprocess
import configparser
import textwrap
import shlex
from pathlib import Path
from xdg_base_dirs import xdg_config_home, xdg_data_home


CONFIG_INI = Path(xdg_config_home()) / "appimanage" / "config.ini"
MENU_DIR = Path(xdg_data_home()) / "applications"
MENU_DIR.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger("appimanage")
logger.addHandler(logging.NullHandler())

ICON_EXTENSIONS = (".png", ".svg", ".xpm", ".ico")
SHORTCUT_KEYS_TO_UPDATE = ("Exec=", "Icon=", "TryExec=", "Path=", "X-AppImage-Path=")


def get_desktop_dir(max_attempts: int = 3, delay: float = 0.2) -> Path | None:
    """Resolve a user-writable desktop directory, retrying if necessary."""
    fallback = Path.home() / "Desktop"
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            resolved = subprocess.check_output(
                ["xdg-user-dir", "DESKTOP"], stderr=subprocess.STDOUT
            ).decode().strip()
            candidate = Path(resolved)
        except Exception as err:
            last_error = err
            logger.warning(
                "Attempt %s to resolve desktop directory via xdg-user-dir failed: %s",
                attempt,
                err,
            )
            candidate = fallback

        if not candidate.exists():
            try:
                candidate.mkdir(parents=True, exist_ok=True)
                logger.info("Created desktop directory at %s", candidate)
            except Exception as err:
                last_error = err
                logger.error("Failed to create desktop directory %s: %s", candidate, err)
                candidate = None

        if candidate and os.access(candidate, os.W_OK):
            return candidate

        if candidate:
            logger.warning(
                "Desktop directory %s is not writable; retrying...", candidate
            )

        time.sleep(delay)

    if last_error:
        logger.error(
            "Unable to determine a writable desktop directory after %s attempts: %s",
            max_attempts,
            last_error,
        )
    else:
        logger.error(
            "Unable to determine a writable desktop directory after %s attempts.",
            max_attempts,
        )
    return None

# pip uninstall appimanage -y
# pip cache purge
# pip install -e .


def read_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    if CONFIG_INI.exists():
        config.read(CONFIG_INI)
    return config


def _is_appimage_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == ".appimage"


def _iter_appimages(appimage_dir: Path):
    if not appimage_dir.exists():
        return
    for candidate in appimage_dir.rglob("*"):
        if _is_appimage_file(candidate):
            yield candidate


def get_appimages(appimage_dir: Path) -> list[Path]:
    return sorted(_iter_appimages(appimage_dir), key=lambda path: path.name.lower())


def _shortcut_filename(appimage_name: str) -> str:
    return f"{appimage_name}.desktop"


def _existing_icon_path(appimage_path: Path) -> str | None:
    for ext in ICON_EXTENSIONS:
        for candidate in (
            appimage_path.with_suffix(ext),
            appimage_path.with_name(f"{appimage_path.stem}_icon{ext}"),
        ):
            if candidate.exists():
                return str(candidate)
    return None


def _cleanup_icon_files(appimage_path: Path) -> None:
    for ext in ICON_EXTENSIONS:
        candidate = appimage_path.with_name(f"{appimage_path.stem}_icon{ext}")
        if candidate.exists():
            try:
                candidate.unlink()
            except Exception as err:
                logger.warning("Failed to remove icon artifact %s: %s", candidate, err)


def _build_desktop_entry(name: str, exec_path: Path, icon: str) -> str:
    quoted_exec = shlex.quote(str(exec_path))
    icon_value = icon or "application-x-executable"
    content = textwrap.dedent(
        f"""
        [Desktop Entry]
        Type=Application
        Name={name}
        Comment=AppImage managed by appimanage
        Exec={quoted_exec}
        TryExec={quoted_exec}
        Icon={icon_value}
        Terminal=false
        Categories=Utility;AppImage;
        X-AppImage-Path={quoted_exec}
        """
    ).strip()
    return f"{content}\n"


def write_config(config: configparser.ConfigParser) -> None:
    CONFIG_INI.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_INI, "w") as configfile:
        config.write(configfile)


def set_dir(new_dir: str, move: bool) -> None:
    config = read_config()
    old_dir = config.get("Settings", "AppImageDir", fallback=None)

    if old_dir == new_dir:
        print(f"[!] AppImage directory already set to {new_dir}")
        return

    try:
        Path(new_dir).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[!] Failed to create directory {new_dir}: {e}")
        return

    config["Settings"] = {"AppImageDir": new_dir}
    write_config(config)

    if old_dir and Path(old_dir).exists() and move:
        move_appimages(Path(old_dir), Path(new_dir))

    print(f"[~] AppImage directory set to {new_dir}")


def get_dir():
    config = read_config()
    appimage_dir = config.get("Settings", "AppImageDir", fallback=None)

    if not appimage_dir:
        print("[!] No AppImage directory set. Set with --set first.")
        return None

    appimage_dir = Path(appimage_dir)
    if not appimage_dir.exists():
        print(f"[!] AppImage directory {appimage_dir} does not exist.")
        return None

    return appimage_dir


def unset_dir():
    config = read_config()
    old_dir = config.get("Settings", "AppImageDir", fallback=None)

    if not old_dir:
        print("[!] No AppImage directory set. Set with --set first.")
        return

    config["Settings"] = {"AppImageDir": ""}
    write_config(config)

    print(f"[~] AppImage directory unset from {old_dir}")


def list_appimages():
    """List all managed AppImages in the configured directory."""
    config = read_config()
    appimage_dir = config.get("Settings", "AppImageDir", fallback=None)

    if not appimage_dir:
        print("[!] No AppImage directory set. Set with --set first.")
        return

    appimage_dir = Path(appimage_dir)
    if not appimage_dir.exists():
        print(f"[!] AppImage directory {appimage_dir} does not exist.")
        return

    appimages = get_appimages(appimage_dir)
    if not appimages:
        print("[~] No AppImages found in the directory.")
        return
    print("[~] AppImages:")
    for path in appimages:
        print(f"\t{path}")


def move_appimages(old_dir: Path, new_dir: Path):
    try:
        new_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[!] Failed to create new directory {new_dir}: {e}")
        return
    if not old_dir.exists():
        print(f"[!] Old directory {old_dir} does not exist.")
        return
    for file in _iter_appimages(old_dir):
        try:
            relative = file.relative_to(old_dir)
            destination = new_dir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(file), str(destination))
        except Exception as e:
            print(f"[!] Failed to move {file}: {e}")
    update_shortcuts(str(old_dir), str(new_dir), MENU_DIR)
    desktop_dir = get_desktop_dir()
    if desktop_dir:
        update_shortcuts(str(old_dir), str(new_dir), desktop_dir)
    else:
        logger.warning("Skipped desktop shortcut updates because no writable desktop directory was found.")
    print(f"[~] Moved AppImages from {old_dir} to {new_dir}")


def update_shortcuts(old_dir: str, new_dir: str, shortcut_dir: Path):
    for entry in shortcut_dir.glob("*.desktop"):
        updated = False
        lines = entry.read_text().splitlines()
        for i, line in enumerate(lines):
            if line.startswith(SHORTCUT_KEYS_TO_UPDATE) and old_dir in line:
                lines[i] = line.replace(old_dir, new_dir)
                updated = True
        if updated:
            entry.write_text("\n".join(lines) + "\n")


def get_appimage_icon(appimage_path: Path):
    """Extract icon from AppImage, fallback to default if extraction fails."""
    existing = _existing_icon_path(appimage_path)
    if existing:
        return existing
    icon = "application-x-executable"
    extract_dir = appimage_path.parent / "squashfs-root"
    try:
        subprocess.run(
            [str(appimage_path), "--appimage-extract"],
            check=True,
            capture_output=True,
            cwd=str(appimage_path.parent),
        )
        for ext in ICON_EXTENSIONS:
            icon_files = list(extract_dir.rglob(f"*{ext}")) + list(
                extract_dir.rglob(f"*{ext.upper()}")
            )
            if icon_files:
                actual_ext = icon_files[0].suffix
                icon_dest = appimage_path.with_name(f"{appimage_path.stem}_icon{actual_ext}")
                shutil.copy2(icon_files[0], icon_dest)
                icon = str(icon_dest)
                break
    except Exception as e:
        print(f"[!] Failed to extract AppImage icon for {appimage_path}: {e}. Fallback to default.")
    finally:
        if extract_dir.exists():
            try:
                shutil.rmtree(extract_dir)
            except Exception as e:
                print(f"[!] Failed to clean up extracted icon directory: {e}")
    return icon


def create_shortcut(appimage_path: Path, shortcut_dir: Path, force: bool = False):
    """Create a .desktop shortcut for the given AppImage in the given directory."""
    name = appimage_path.stem
    icon = _existing_icon_path(appimage_path) or get_appimage_icon(appimage_path)
    shortcut = shortcut_dir / _shortcut_filename(name)
    exec_path = appimage_path.resolve()
    entry_content = _build_desktop_entry(name, exec_path, icon)
    temporary_shortcut = shortcut.with_suffix(".desktop.tmp")
    try:
        shortcut_dir.mkdir(parents=True, exist_ok=True)
        if shortcut.exists():
            if force:
                shortcut.unlink()
            else:
                print(f"[~] Shortcut {shortcut} already exists. Use --force to overwrite.")
                return
        temporary_shortcut.write_text(entry_content)
        os.chmod(temporary_shortcut, 0o755)
        temporary_shortcut.replace(shortcut)
        print(f"[~] Created shortcut: {shortcut}")
    except Exception as e:
        print(f"[!] Failed to create shortcut for {appimage_path}: {e}")
        if temporary_shortcut.exists():
            temporary_shortcut.unlink(missing_ok=True)


def create_start_menu_shortcuts(force: bool = False):
    """Create start menu shortcuts for all AppImages."""
    appimage_dir = get_dir()
    if not appimage_dir:
        print("[!] No AppImage directory set.")
        return
    for appimage in get_appimages(appimage_dir):
        create_shortcut(appimage, MENU_DIR, force=force)


def create_desktop_shortcuts(force: bool = False):
    """Create desktop shortcuts for all AppImages."""
    appimage_dir = get_dir()
    if not appimage_dir:
        print("[!] No AppImage directory set.")
        return
    desktop_dir = get_desktop_dir()
    if not desktop_dir:
        print("[!] Could not determine a writable desktop directory.")
        return
    for appimage in get_appimages(appimage_dir):
        create_shortcut(appimage, desktop_dir, force=force)


def remove_shortcut(appimage: str, shortcut_dir: Path):
    """Remove a .desktop shortcut for the given appimage name from the directory."""
    shortcut = shortcut_dir / _shortcut_filename(appimage)
    try:
        if shortcut.exists():
            shortcut.unlink()
            print(f"[~] Removed shortcut: {shortcut}")
        else:
            print(f"[~] Shortcut {shortcut} does not exist.")
    except Exception as e:
        print(f"[!] Failed to remove shortcut {shortcut}: {e}")


def remove_appimage(appimage):
    """Remove the specified AppImage and its shortcuts."""
    appimage_dir = get_dir()
    if not appimage_dir:
        print("[!] No AppImage directory set.")
        return
    appimages = get_appimages(appimage_dir)
    found = False
    for path in appimages:
        if path.stem.lower() == appimage.lower():
            found = True
            appimage_name = path.stem
            try:
                path.unlink()
                print(f"[~] Removed AppImage: {path}")
                _cleanup_icon_files(path)
            except Exception as e:
                print(f"[!] Failed to remove AppImage {path}: {e}")
            
            try:
                remove_shortcut(appimage_name, MENU_DIR)
            except Exception as e:
                print(f"[!] Failed to remove menu shortcut: {e}")
            
            desktop_dir = get_desktop_dir()
            if desktop_dir:
                try:
                    remove_shortcut(appimage_name, desktop_dir)
                except Exception as e:
                    print(f"[!] Failed to remove desktop shortcut: {e}")
            else:
                logger.warning("Skipped removing desktop shortcut for %s because no writable desktop directory was found.", appimage_name)
            break
    if not found:
        print(f"{appimage} not found in AppImage directory")


def main():
    """Main CLI entrypoint for appimanage."""
    import logging
    parser = argparse.ArgumentParser(description="Unified managing for AppImages")
    parser.add_argument("--set", metavar="PATH", help="Set the AppImage directory")
    parser.add_argument(
        "--unset",
        action="store_true",
        help="Unset the AppImage directory",
    )
    parser.add_argument(
        "--list", action="store_true", help="List all currently managed AppImages"
    )
    parser.add_argument(
        "--startmenu",
        action="store_true",
        help="Create start menu entries for all AppImages",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Move AppImages from old directory to new one",
    )
    parser.add_argument(
        "--desktop", action="store_true", help="Create desktop shortcuts for all AppImages"
    )
    parser.add_argument(
        "--remove", metavar="APPIMAGE", help="Delete a specific AppImage and its links"
    )
    parser.add_argument(
        "--update", action="store_true", help="Update all managed AppImages (not implemented)"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force overwrite of existing shortcuts"
    )

    args, _ = parser.parse_known_args()

    # Setup logging
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format="[%(levelname)s] %(message)s")
    logger = logging.getLogger("appimanage")

    # Processing in order of occurrence
    for action, value in [
        (action, value) for action, value in vars(args).items() if value and action not in ("debug", "force")
    ]:
        actions = {
            "set": lambda: set_dir(value, args.move),
            "unset": unset_dir,
            "startmenu": lambda: create_start_menu_shortcuts(force=args.force),
            "desktop": lambda: create_desktop_shortcuts(force=args.force),
            "list": list_appimages,
            "remove": lambda: remove_appimage(value),
            "update": lambda: print("[!] --update is not implemented yet. See roadmap in README."),
        }
        if action in actions:
            try:
                actions[action]()
            except Exception as e:
                logger.error(f"Error during '{action}': {e}")


if __name__ == "__main__":
    main()
