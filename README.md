# appimanage

A CLI-based helper for integration and management of AppImage programs on Linux systems.

## Features

- Set a dedicated directory for AppImage files
- Create `.desktop` entries for AppImages for easy application launching
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

Tested on Debian-based distributions (Debian, Ubuntu, Mint, Kali).

## Roadmap

- [x] `--set` to set the AppImage directory 
- [x] `--unset` to forget the AppImage directory
- [x] `--list` to display all managed AppImages
- [x] `--startmenu` to link all managed AppImages to the start menu
- [x] `--desktop` to create desktop shortcuts for all AppImages
- [x] `--remove` to delete a specific AppImage and its shortcuts
- [x] `--move` to enable auto moving of AppImages and link updates
