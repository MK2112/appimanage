# appimanage

A CLI tool for seamless integration and management of AppImage programs on Linux systems.

## Features

- Set a dedicated directory for AppImage files
- Create .desktop entries for AppImages for easy application launching
- Manage and update AppImage integrations

## Installation (WIP)

```bash
git clone https://github.com/MK2112/appimanage.git
cd appimanage
pip install -e .
```

## Usage

Set AppImage directory:
```bash
appimanage --set /path/to/appimages-directory
```

With a directory set, create start menu entries:
```bash
appimanage --startmenu
```

## Supported Distributions

- Tested on Debian-based distributions (Ubuntu, Linux Mint, etc.)

## Roadmap

- [x] `--list` to display all managed AppImages
- [ ] `--add` and `--remove` for specific AppImage (de-)listing
- [ ] `--startmenu` to link all managed AppImages to the start menu
- [ ] `--update` for bulk AppImage integration updates
- [ ] Expand distribution compatibility
- [ ] Implement automated testing
- [ ] (Optional) Publish to PyPI for easier installation