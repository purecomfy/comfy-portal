# Comfy Portal

Portable Windows launcher for ComfyUI with:

- ComfyUI start/stop
- LocalTunnel main link
- friend links
- built-in setup page for Comfy, models, and nodes
- logs, settings, launch mode selection, and autorun

## Install

The easiest way to use Comfy Portal is from the GitHub Releases page:

1. Download `Comfy Portal Portable Release.zip`
2. Extract the folder anywhere
3. Run `Comfy Portal.exe`

No installer is required.

## First launch

On first launch, Comfy Portal can ask how ComfyUI should run:

- GPU / NVIDIA
- CPU

This can also be changed later in Settings.

## What Comfy Portal stores

Runtime config and state are stored in:

- `%LOCALAPPDATA%\\ComfyPortal`

That keeps the release portable and avoids writing config into the app folder.

## Setup page

The built-in setup page can:

- download a pinned portable ComfyUI package
- install ComfyUI Manager
- place required models into the correct folders
- install supported custom nodes
- create missing folders automatically

## Portable release

This repository includes source code.

For end users, the recommended download is the portable release zip from GitHub Releases.

## Build from source

Python 3.14 was used in the current project.

### One-file build with PyInstaller

```powershell
python -m PyInstaller --clean --noconfirm --onefile --windowed --name "Comfy Portal" --icon ".\\assets\\comfy_portal.ico" --add-data ".\\assets\\comfy_portal.ico;assets" --add-data ".\\assets\\comfy_portal_icon.png;assets" --add-data ".\\assets\\telegram_brand.png;assets" --add-data ".\\assets\\settings_brand.png;assets" --add-data ".\\assets\\telegram_button_icon.png;assets" --add-data ".\\assets\\telegram_button_round.png;assets" .\\comfy_portal.py
```

### Portable folder build with cx_Freeze

```powershell
python .\\setup_cxfreeze.py build_exe --build-exe .\\cxfreeze_dist
```

## Notes

- This project is currently Windows-focused.
- Unsigned one-file Windows executables can trigger heuristic antivirus detections even when the code is clean. Portable folder builds are often friendlier to antivirus tools.

## License

MIT
