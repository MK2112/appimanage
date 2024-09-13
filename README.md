# appimanage

A CLI tool for integration and management of AppImage programs on Linux systems.

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

Tested on Debian-based distributions.

## Roadmap

- [x] `--set` to set the AppImage directory 
- [x] `--unset` to forget the AppImage directory
- [x] `--list` to display all managed AppImages
- [x] `--startmenu` to link all managed AppImages to the start menu
- [x] `--desktop` to create a desktop shortcut for a specific AppImage
- [x] `--remove` to set the AppImage directory
- [x] `--move` to enable auto moving of AppImages and link updates
- [ ] Implement automated testing
- [ ] Expand distribution compatibility
- [ ] `--update` to update all managed AppImages (requiring some sort of versioning and web referencing)
- [ ] (Optional) Publish to PyPI (ease of use, UX or whatever)
