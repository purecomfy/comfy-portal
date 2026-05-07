## Comfy Portal v1.1.10

### Added
- Added LocalTunnel / Cloudflare tunnel provider selection.
- Added Cloudflare Quick Tunnel support with automatic `cloudflared.exe` download.
- Added `Repair launch` in Settings to restart ComfyUI and the selected tunnel from a clean state.

### Fixed
- Fixed ComfyUI launch arguments so `--listen 0.0.0.0 --port 8188` are applied safely.
- Tunnel status now shows active only after the public URL responds.
- Improved tunnel error messages for dead links, missing Cloudflare, and local port problems.

### UI
- Refreshed light/dark visuals with softer glass-style panels.
- Added smoother drawer and onboarding animations.
- Cleaned up short descriptions and labels across the main screen, logs, and friend links.
