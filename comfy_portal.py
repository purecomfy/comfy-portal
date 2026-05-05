from __future__ import annotations

import base64
import json
import locale
import os
import re
import secrets
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import zipfile
import ctypes
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

try:
    import winreg
except Exception:
    winreg = None

import psutil
from PySide6.QtCore import QAbstractAnimation, Property, QEasingCurve, QPoint, QPropertyAnimation, QRectF, QSize, QTimer, Qt, Signal, QObject, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QFont, QIcon, QPainter, QPen, QPixmap, QPolygon
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDialog,
    QFileDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QStyleFactory,
    QVBoxLayout,
    QWidget,
)


APP_NAME = "Comfy Portal"
APP_VERSION = "1.1.4"
APP_USER_MODEL_ID = "Mofko.ComfyPortal"
WINDOWS_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
WINDOWS_AUTOSTART_VALUE = APP_NAME
GITHUB_REPO_URL = "https://github.com/purecomfy/comfy-portal"
GITHUB_RELEASES_URL = f"{GITHUB_REPO_URL}/releases"
GITHUB_LATEST_RELEASE_API = "https://api.github.com/repos/purecomfy/comfy-portal/releases/latest"
GITHUB_PORTABLE_ASSET_NAME = "Comfy.Portal.Portable.Release.zip"
GITHUB_ONEFILE_ASSET_NAME = "Comfy.Portal.exe"
COMFY_GITHUB_REPO_URL = "https://github.com/comfyanonymous/ComfyUI"
COMFY_GITHUB_LATEST_RELEASE_API = "https://api.github.com/repos/comfyanonymous/ComfyUI/releases/latest"
DEFAULT_WIDTH = 1220
DEFAULT_HEIGHT = 780
DRAWER_WIDTH = 340
FRIENDS_DRAWER_WIDTH = 438
POLL_MS = 6200
PROCESS_SCAN_TTL = 45.0
PORT_CHECK_TIMEOUT = 0.02
INTERNET_CHECK_TIMEOUT = 0.8
COMFY_HTTP_TIMEOUT = 0.8
INTERNET_CACHE_TTL = 45.0
SETUP_STATUS_CACHE_TTL = 180.0
DOWNLOAD_LINK_CACHE_TTL = 300.0
DOWNLOAD_LINK_TIMEOUT = 12.0
DOWNLOAD_CHUNK_SIZE = 1024 * 1024
DOWNLOAD_PROGRESS_INTERVAL = 1.0
DEFAULT_TUNNEL_RETRY_DELAY = 5.0
MAX_TUNNEL_RETRY_DELAY = 45.0
MAX_FRIEND_LINKS = 5
DISCOVER_COMFY_CACHE_TTL = 90.0
DISCOVER_COMFY_BUDGET_SECONDS = 2.8
DISCOVER_COMFY_DEEP_BUDGET_SECONDS = 4.5
LOG_VIEW_POLL_MS = 550
PUBLIC_TUNNEL_CACHE_TTL = 18.0
UPDATE_CHECK_CACHE_TTL = 900.0
OVERLAY_ANIMATION_MS = 180
PANEL_SLIDE_OFFSET = 6
BACKDROP_FADE_MS = 220
PAGE_FADE_MS = 170
TELEGRAM_CHANNEL_URL = "https://t.me/ComfyUIGuide"
TELEGRAM_BRAND_SIZE = 38
GITHUB_BRAND_SIZE = 38
ONBOARDING_MIN_SUBDOMAIN_LEN = 6
ONBOARDING_STORAGE_HEADROOM_BYTES = 1024 * 1024 * 1024
# Accept legacy 6-digit friend links and new 8-digit ones.
FRIEND_LINK_PATTERN = re.compile(r"friendscomfy(?:\d{6}|\d{8})")
SUBDOMAIN_PATTERN = re.compile(r"^[a-z0-9-]{3,63}$")
SUBDOMAIN_ARG_PATTERN = re.compile(r"--subdomain\s+([a-z0-9-]+)")
PUBLIC_URL_PATTERN = re.compile(r"https://([a-z0-9-]+)\.loca\.lt")
COMFYUI_PORTABLE_URL = "https://github.com/comfyanonymous/ComfyUI/releases/latest/download/ComfyUI_windows_portable_nvidia.7z"
PINNED_COMFY_PACKAGE_URL = "https://github.com/mofko/ComfyUI/releases/download/FAPEPE/ComfyUI_windows_portable_nvidia.7z"
COMFYUI_PORTABLE_ARCHIVE_NAME = "ComfyUI_windows_portable_nvidia.7z"
COMFY_PACKAGE_MARKER_NAME = ".comfy_portal_source.json"
CUSTOM_COMFY_ARCHIVE_NAME = "ComfyPortal.custom_comfy.7z"
CUSTOM_COMFY_URL_FILENAME = "ComfyPortal.custom_comfy_url.txt"
COMFYUI_MANAGER_ARCHIVE_URL = "https://github.com/ltdrdata/ComfyUI-Manager/archive/refs/heads/main.zip"
DOWNLOAD_USER_AGENT = f"ComfyPortal/{APP_VERSION}"
BUNDLED_CIVITAI_KEYS_B64 = (
    "NTY0MDAxNDRlMTlkZGFjZDMxZjcwNTNkMTZkMzI5Y2M=",
    "YmJiYjlmZmVjMmFjN2VlZjA3NWUxOTUxYzVjMzA0YWI=",
)
DEFAULT_LAUNCH_MODE = "fp16"
DEFAULT_EXTRA_LAUNCH_ARGS = "--disable-dynamic-vram"
MODEL_SIZE_HINTS = {
    "SAM": 420 * 1024 * 1024,
    "RealESRGAN x2": 70 * 1024 * 1024,
    "Control LoRA Canny": 150 * 1024 * 1024,
    "VAE": 340 * 1024 * 1024,
    "CLIP / text_encoders": 8 * 1024 * 1024 * 1024,
    "ControlNet Union": 3 * 1024 * 1024 * 1024,
    "Embeddings": 80 * 1024 * 1024,
    "Upscale 4x_NMKD-Siax_200k": 70 * 1024 * 1024,
    "mopMixtureOfPerverts_v20.safetensors": 2 * 1024 * 1024 * 1024,
    "xxxRay_dmd2.safetensors": 2 * 1024 * 1024 * 1024,
    "novaAnimeXL_ilV170.safetensors": 2 * 1024 * 1024 * 1024,
    "redcraft_ernieRedmix.safetensors": 4 * 1024 * 1024 * 1024,
    "redcraft_ernieRedmix_txt.safetensors": 8 * 1024 * 1024 * 1024,
    "flux2-tiny-vae.safetensors": 350 * 1024 * 1024,
    "bbox/face_yolov8m.pt": 60 * 1024 * 1024,
    "bbox/Eyeful_v2-Paired.pt": 90 * 1024 * 1024,
}
NODE_SIZE_HINT_BYTES = 220 * 1024 * 1024
PORTABLE_SIZE_HINT_BYTES = int(1.9 * 1024 * 1024 * 1024)
MANAGER_SIZE_HINT_BYTES = 40 * 1024 * 1024
COMFY_LAUNCH_MODES = {
    "fp16": {
        "title": "FP16",
        "args": ["--windows-standalone-build", "--listen", "--fp16-unet", "--fp16-vae", "--fp16-text-enc"],
    },
    "fp8": {
        "title": "FP8",
        "args": ["--windows-standalone-build", "--listen", "--fp8_e4m3fn-unet", "--fp8_e4m3fn-text-enc", "--fp16-vae"],
    },
    "bf16": {
        "title": "BF16",
        "args": ["--windows-standalone-build", "--listen", "--bf16-unet", "--bf16-vae", "--bf16-text-enc"],
    },
    "cpu": {
        "title": "CPU",
        "args": ["--windows-standalone-build", "--listen", "--cpu"],
    },
}
STARTER_MODEL_SPECS = (
    {
        "title": "SAM",
        "filename": "sam_vit_b_01ec64.pth",
        "url": "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth",
        "relative_dir": ("ComfyUI", "models", "sams"),
    },
    {
        "title": "RealESRGAN x2",
        "filename": "RealESRGAN_x2.pth",
        "url": "https://huggingface.co/ai-forever/Real-ESRGAN/resolve/main/RealESRGAN_x2.pth?download=true",
        "relative_dir": ("ComfyUI", "models", "upscale_models"),
    },
    {
        "title": "Control LoRA Canny",
        "filename": "control-lora-canny-rank256.safetensors",
        "url": "https://huggingface.co/stabilityai/control-lora/resolve/main/control-LoRAs-rank256/control-lora-canny-rank256.safetensors?download=true",
        "relative_dir": ("ComfyUI", "models", "controlnet"),
    },
    {
        "title": "VAE",
        "filename": "ae.safetensors",
        "url": "https://huggingface.co/Comfy-Org/HiDream-I1_ComfyUI/resolve/main/split_files/vae/ae.safetensors?download=true",
        "relative_dir": ("ComfyUI", "models", "vae"),
    },
    {
        "title": "CLIP / text_encoders",
        "filename": "qwen_3_4b.safetensors",
        "url": "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors?download=true",
        "relative_dir": ("ComfyUI", "models", "text_encoders"),
    },
    {
        "title": "ControlNet Union",
        "filename": "Z-Image-Turbo-Fun-Controlnet-Union-2.1-2602-8steps.safetensors",
        "url": "https://huggingface.co/alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union-2.1/resolve/main/Z-Image-Turbo-Fun-Controlnet-Union-2.1-2602-8steps.safetensors?download=true",
        "relative_dir": ("ComfyUI", "models", "model_patches"),
    },
    {
        "title": "Embeddings",
        "filename": "embedding_model.pt",
        "url": "https://civitai.com/api/download/models/2121199?type=Model&format=Other",
        "relative_dir": ("ComfyUI", "models", "embeddings"),
        "detect_any_file": True,
        "detect_extensions": (".pt", ".pth", ".bin", ".ckpt", ".safetensors"),
    },
    {
        "title": "Upscale 4x_NMKD-Siax_200k",
        "filename": "4x_NMKD-Siax_200k.pth",
        "url": "https://huggingface.co/gemasai/4x_NMKD-Siax_200k/resolve/main/4x_NMKD-Siax_200k.pth?download=true",
        "relative_dir": ("ComfyUI", "models", "upscale_models"),
    },
    {
        "title": "mopMixtureOfPerverts_v20.safetensors",
        "filename": "mopMixtureOfPerverts_v20.safetensors",
        "url": "https://civitai.red/api/download/models/2159501?type=Model&format=SafeTensor&size=pruned&fp=fp16",
        "relative_dir": ("ComfyUI", "models", "checkpoints"),
        "detect_names": ("mopMixtureOfPerverts_v20.safetensors",),
        "detect_contains_any": ("mopmixtureofperverts", "mixtureofperverts", "2159501"),
        "detect_extensions": (".safetensors", ".ckpt"),
    },
    {
        "title": "xxxRay_dmd2.safetensors",
        "filename": "xxxRay_dmd2.safetensors",
        "url": "https://civitai.red/api/download/models/1624818?type=Model&format=SafeTensor&size=full&fp=fp16",
        "relative_dir": ("ComfyUI", "models", "checkpoints"),
        "detect_names": ("xxxRay_dmd2.safetensors",),
        "detect_contains_any": ("xxxray", "ray_dmd2", "dmd2", "1624818"),
        "detect_extensions": (".safetensors", ".ckpt"),
    },
    {
        "title": "novaAnimeXL_ilV170.safetensors",
        "filename": "novaAnimeXL_ilV170.safetensors",
        "url": "https://civitai.red/api/download/models/2741698?type=Model&format=SafeTensor&size=pruned&fp=fp16",
        "relative_dir": ("ComfyUI", "models", "checkpoints"),
        "detect_names": ("novaAnimeXL_ilV170.safetensors",),
        "detect_contains_any": ("novaanimexl", "novaanime", "2741698"),
        "detect_extensions": (".safetensors", ".ckpt"),
    },
    {
        "title": "redcraft_ernieRedmix.safetensors",
        "filename": "redcraft_ernieRedmix.safetensors",
        "url": "https://civitai.red/api/download/models/2891710?type=Diffusion%20Model&format=Other&fp=fp8",
        "relative_dir": ("ComfyUI", "models", "unet"),
        "detect_names": ("redcraft_ernieRedmix.safetensors",),
        "detect_contains_any": ("redcraft", "ernieredmix", "2891710"),
        "detect_extensions": (".safetensors", ".ckpt"),
    },
    {
        "title": "redcraft_ernieRedmix_txt.safetensors",
        "filename": "redcraft_ernieRedmix_txt.safetensors",
        "url": "https://civitai.red/api/download/models/2891710?fileId=2773413",
        "relative_dir": ("ComfyUI", "models", "text_encoders"),
        "detect_names": ("redcraft_ernieRedmix_txt.safetensors",),
        "detect_contains_any": ("ernieredmix_txt", "redcraft", "2773413"),
        "detect_extensions": (".safetensors", ".ckpt"),
    },
    {
        "title": "flux2-tiny-vae.safetensors",
        "filename": "flux2-tiny-vae.safetensors",
        "url": "https://civitai.red/api/download/models/2891710?fileId=2773335",
        "relative_dir": ("ComfyUI", "models", "vae"),
        "detect_names": ("flux2-tiny-vae.safetensors",),
        "detect_contains_any": ("flux2-tiny-vae", "tiny-vae", "2773335"),
        "detect_extensions": (".safetensors", ".ckpt"),
    },
    {
        "title": "bbox/face_yolov8m.pt",
        "filename": "face_yolov8m.pt",
        "url": "https://huggingface.co/alexgenovese/ultralytics/resolve/main/bbox/face_yolov8m.pt?download=true",
        "relative_dir": ("ComfyUI", "models", "ultralytics", "bbox"),
    },
    {
        "title": "bbox/Eyeful_v2-Paired.pt",
        "filename": "Eyeful_v2-Paired.pt",
        "url": "https://huggingface.co/MidnightRunner/Ultralytics/resolve/main/bbox/Eyeful_v2-Paired.pt?download=true",
        "relative_dir": ("ComfyUI", "models", "ultralytics", "bbox"),
    },
)
REQUIRED_NODE_SPECS = (
    {
        "title": "ComfyUI Impact Pack",
        "cnr_id": "comfyui-impact-pack",
        "folder": "ComfyUI-Impact-Pack",
        "repo": "https://github.com/ltdrdata/ComfyUI-Impact-Pack.git",
    },
    {
        "title": "ComfyUI-Custom-Scripts",
        "cnr_id": "comfyui-custom-scripts",
        "folder": "ComfyUI-Custom-Scripts",
        "repo": "https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git",
    },
    {
        "title": "rgthree-comfy",
        "cnr_id": "rgthree-comfy",
        "folder": "rgthree-comfy",
        "repo": "https://github.com/rgthree/rgthree-comfy.git",
    },
    {
        "title": "ComfyUI-Easy-Use",
        "cnr_id": "comfyui-easy-use",
        "folder": "ComfyUI-Easy-Use",
        "repo": "https://github.com/yolain/ComfyUI-Easy-Use.git",
    },
    {
        "title": "ComfyUI_UltimateSDUpscale",
        "cnr_id": "comfyui_ultimatesdupscale",
        "folder": "ComfyUI_UltimateSDUpscale",
        "repo": "https://github.com/ssitu/ComfyUI_UltimateSDUpscale.git",
    },
    {
        "title": "ComfyUI Impact Subpack",
        "cnr_id": "comfyui-impact-subpack",
        "folder": "ComfyUI-Impact-Subpack",
        "repo": "https://github.com/ltdrdata/ComfyUI-Impact-Subpack.git",
    },
    {
        "title": "ComfyUI_Swwan",
        "cnr_id": "aining2022/ComfyUI_Swwan",
        "folder": "ComfyUI_Swwan",
        "repo": "https://github.com/aining2022/ComfyUI_Swwan.git",
    },
    {
        "title": "CG Use Everywhere",
        "cnr_id": "cg-use-everywhere",
        "folder": "cg-use-everywhere",
        "repo": "https://github.com/chrisgoringe/cg-use-everywhere.git",
        "aliases": ["CG Use Everywhere", "UE Nodes", "Anything Everywhere"],
    },
    {
        "title": "Save Image with Generation Metadata",
        "cnr_id": "comfyui-imagewithmetadata",
        "folder": "ImageWithMetadata",
        "repo": "https://github.com/shin131002/ComfyUI-ImageWithMetadata.git",
        "aliases": ["Save Image with Generation Metadata", "ComfyUI ImageWithMetadata Nodes", "Save Image with Metadata", "Execution Timer"],
    },
    {
        "title": "Various ComfyUI Nodes by Type",
        "cnr_id": "comfyui-various",
        "folder": "comfyui-various",
        "repo": "https://github.com/jamesWalker55/comfyui-various.git",
        "aliases": ["Various ComfyUI Nodes by Type", "Seed Generator"],
    },
    {
        "title": "CRT-Nodes",
        "cnr_id": "crt-nodes",
        "folder": "CRT-Nodes",
        "repo": "https://github.com/PGCRT/CRT-Nodes.git",
        "aliases": ["CRT-Nodes", "CRT_KSamplerBatch"],
    },
    {
        "title": "ComfyUI-Chibi-Nodes",
        "cnr_id": "comfyui-chibi-nodes",
        "folder": "ComfyUI-Chibi-Nodes",
        "repo": "https://github.com/chibiace/ComfyUI-Chibi-Nodes.git",
        "aliases": ["ComfyUI-Chibi-Nodes", "ComfyUI Chibi Nodes"],
    },
    {
        "title": "ComfyUI_essentials",
        "cnr_id": "comfyui_essentials",
        "folder": "ComfyUI_essentials",
        "repo": "https://github.com/cubiq/ComfyUI_essentials.git",
        "aliases": ["ComfyUI_essentials", "ComfyUI essentials", "essentials"],
    },
    {
        "title": "Comfyroll Studio",
        "cnr_id": "comfyroll-studio",
        "folder": "ComfyUI_Comfyroll_CustomNodes",
        "repo": "https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes.git",
        "aliases": ["Comfyroll Studio", "Comfyroll", "ComfyUI_Comfyroll_CustomNodes", "CR nodes"],
    },
    {
        "title": "ComfyUI ControlNet Aux",
        "cnr_id": "comfyui-controlnet-aux",
        "folder": "comfyui_controlnet_aux",
        "repo": "https://github.com/Fannovel16/comfyui_controlnet_aux.git",
        "aliases": ["ComfyUI ControlNet Aux", "ControlNet Aux", "controlnet_aux"],
    },
    {
        "title": "ComfyUI LayerStyle",
        "cnr_id": "comfyui-layerstyle",
        "folder": "ComfyUI_LayerStyle",
        "repo": "https://github.com/chflame163/ComfyUI_LayerStyle.git",
        "aliases": ["ComfyUI LayerStyle", "LayerStyle", "Layer Style"],
    },
    {
        "title": "ComfyUI-KJNodes",
        "cnr_id": "comfyui-kjnodes",
        "folder": "ComfyUI-KJNodes",
        "repo": "https://github.com/kijai/ComfyUI-KJNodes.git",
        "aliases": ["ComfyUI-KJNodes", "KJNodes", "SetNode", "GetNode", "JWString", "JWInteger"],
    },
    {
        "title": "ComfyUI-SeedVR2 VideoUpscaler",
        "cnr_id": "comfyui-seedvr2-videoupscaler",
        "folder": "ComfyUI-SeedVR2_VideoUpscaler",
        "repo": "https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler.git",
        "aliases": ["ComfyUI-SeedVR2_VideoUpscaler", "SeedVR2", "SeedVR2 VideoUpscaler"],
    },
    {
        "title": "ComfyUI-RMBG",
        "cnr_id": "comfyui-rmbg",
        "folder": "ComfyUI-RMBG",
        "repo": "https://github.com/1038lab/ComfyUI-RMBG.git",
        "aliases": ["ComfyUI-RMBG", "RMBG"],
    },
    {
        "title": "ComfyUI-Crystools",
        "cnr_id": "comfyui-crystools",
        "folder": "ComfyUI-Crystools",
        "repo": "https://github.com/crystian/ComfyUI-Crystools.git",
        "aliases": ["ComfyUI-Crystools", "Crystools"],
    },
    {
        "title": "ComfyUI-Florence2",
        "cnr_id": "comfyui-florence2",
        "folder": "ComfyUI-Florence2",
        "repo": "https://github.com/kijai/ComfyUI-Florence2.git",
        "aliases": ["ComfyUI-Florence2", "Florence2"],
    },
    {
        "title": "ComfyUI-ReActor",
        "cnr_id": "comfyui-reactor",
        "folder": "ComfyUI-ReActor",
        "repo": "https://github.com/Gourieff/ComfyUI-ReActor.git",
        "aliases": ["ComfyUI-ReActor", "ReActor"],
    },
    {
        "title": "ComfyUI-QwenVL",
        "cnr_id": "comfyui-qwenvl",
        "folder": "ComfyUI-QwenVL",
        "repo": "https://github.com/1038lab/ComfyUI-QwenVL.git",
        "aliases": ["ComfyUI-QwenVL", "QwenVL"],
    },
    {
        "title": "ComfyUI_Fill-Nodes",
        "cnr_id": "comfyui-fill-nodes",
        "folder": "ComfyUI_Fill-Nodes",
        "repo": "https://github.com/filliptm/ComfyUI_Fill-Nodes.git",
        "aliases": ["ComfyUI_Fill-Nodes", "Fill Nodes", "Fill-Nodes"],
    },
    {
        "title": "Derfuu ComfyUI ModdedNodes",
        "cnr_id": "derfuu-comfyui-moddednodes",
        "folder": "Derfuu_ComfyUI_ModdedNodes",
        "repo": "https://github.com/Derfuu/Derfuu_ComfyUI_ModdedNodes.git",
        "aliases": ["Derfuu_ComfyUI_ModdedNodes", "Derfuu ModdedNodes"],
    },
    {
        "title": "facerestore_cf",
        "cnr_id": "facerestore-cf",
        "folder": "facerestore_cf",
        "repo": "https://github.com/mav-rik/facerestore_cf.git",
        "aliases": ["facerestore_cf", "FaceRestore CF"],
    },
    {
        "title": "ComfyUI-mxToolkit",
        "cnr_id": "comfyui-mxtoolkit",
        "folder": "ComfyUI-mxToolkit",
        "repo": "https://github.com/Smirnov75/ComfyUI-mxToolkit.git",
        "aliases": ["ComfyUI-mxToolkit", "mxToolkit"],
    },
    {
        "title": "ComfyUI post processing nodes",
        "cnr_id": "comfyui-post-processing-nodes",
        "folder": "ComfyUI-post-processing-nodes",
        "repo": "https://github.com/EllangoK/ComfyUI-post-processing-nodes.git",
        "aliases": ["ComfyUI post processing nodes", "post-processing nodes"],
    },
    {
        "title": "virtuoso-nodes",
        "cnr_id": "virtuoso-nodes",
        "folder": "virtuoso-nodes",
        "repo": "https://github.com/chrisfreilich/virtuoso-nodes.git",
        "aliases": ["virtuoso-nodes", "Virtuoso Nodes"],
    },
    {
        "title": "Comfy Image Saver",
        "cnr_id": "comfy-image-saver",
        "folder": "comfy-image-saver",
        "repo": "https://github.com/giriss/comfy-image-saver.git",
        "aliases": ["comfy-image-saver", "Image Saver", "FancyTimerNode", "Execution Timer"],
    },
)
WORKFLOW_CANDIDATE_NAMES = (
    "mainapi1.json",
    "workflow.json",
    "workflow_api.json",
    "workflow_api_output.json",
)


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_resource_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def get_resource_path(*parts: str) -> Path:
    return get_resource_dir().joinpath(*parts)


def get_data_dir() -> Path:
    local_appdata = os.environ.get("LOCALAPPDATA")
    root = Path(local_appdata) if local_appdata else Path.home() / "AppData" / "Local"
    data_dir = root / "ComfyPortal"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


BASE_DIR = get_base_dir()
DATA_DIR = get_data_dir()
CONFIG_PATH = DATA_DIR / "ComfyPortal.config.json"
STATE_PATH = DATA_DIR / "ComfyPortal.state.json"
COMFY_OUT = DATA_DIR / "comfy.stdout.log"
COMFY_ERR = DATA_DIR / "comfy.stderr.log"
TUNNEL_OUT = DATA_DIR / "tunnel.stdout.log"
TUNNEL_ERR = DATA_DIR / "tunnel.stderr.log"
PROCESS_SCAN_CACHE = {
    "comfy": {"at": 0.0, "pids": []},
    "tunnel": {"at": 0.0, "pids": []},
    "friend_tunnel": {"at": 0.0, "pids": []},
}
FRIEND_PROCESS_MAP_CACHE = {"at": 0.0, "mapping": {}}
INTERNET_STATUS_CACHE = {"at": 0.0, "ok": True}
SETUP_STATUS_CACHE = {"at": 0.0, "key": "", "status": None}
DOWNLOAD_LINK_STATUS_CACHE = {"items": {}}
DISCOVER_COMFY_CACHE = {"at": 0.0, "path": None, "anchor": ""}
PUBLIC_TUNNEL_STATUS_CACHE = {"items": {}}
UPDATE_RELEASE_CACHE = {"at": 0.0, "info": None}
COMFY_RELEASE_CACHE = {"at": 0.0, "info": None}
COMFY_LAUNCH_LOCK = threading.Lock()
NETWORK_ERROR_HINTS = (
    "connection reset",
    "connection aborted",
    "connection refused",
    "connection timed out",
    "timed out",
    "temporary failure",
    "temporary failure in name resolution",
    "name or service not known",
    "network is unreachable",
    "network unreachable",
    "could not resolve host",
    "failed to connect",
    "unable to access",
    "unable to connect",
    "ssl",
    "proxy error",
    "tls",
    "http error 5",
)
MAIN_TUNNEL_LOCK = threading.Lock()
STATE_LOCK = threading.RLock()
SINGLE_INSTANCE_MUTEX = None
KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True) if os.name == "nt" else None


def resolve_asset_path(filename: str) -> Path:
    candidates = [
        get_resource_path("assets", filename),
        get_base_dir() / "assets" / filename,
        BASE_DIR / "assets" / filename,
        get_resource_path(filename),
        get_base_dir() / filename,
    ]
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).lower()
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists():
            return candidate
    return candidates[0]


def resolve_tool_path(filename: str) -> Path:
    candidates = [
        get_resource_path("tools", filename),
        get_base_dir() / "tools" / filename,
        BASE_DIR / "tools" / filename,
        get_resource_path(filename),
        get_base_dir() / filename,
    ]
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).lower()
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists():
            return candidate
    return candidates[0]


def default_config() -> dict:
    return {
        "port": 8188,
        "subdomain": "comfylocal5618",
        "theme": "light",
        "launch_mode": DEFAULT_LAUNCH_MODE,
        "extra_launch_args": DEFAULT_EXTRA_LAUNCH_ARGS,
        "launch_mode_confirmed": False,
        "onboarding_completed": False,
        "auto_copy_url": True,
        "auto_restart_tunnel": True,
        "start_on_boot": False,
        "comfy_root": "",
        "civitai_api_keys_b64": [],
    }


def default_state() -> dict:
    return {
        "comfy_pid": None,
        "tunnel_pid": None,
        "last_url": "",
        "friend_links": [],
        "desired_running": False,
        "tunnel_retry_after": 0.0,
        "tunnel_retry_delay": DEFAULT_TUNNEL_RETRY_DELAY,
        "last_tunnel_error": "",
    }


def read_json(path: Path, fallback: dict) -> dict:
    if not path.exists():
        return dict(fallback)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return dict(fallback)


def write_json(path: Path, data: dict) -> None:
    payload = json.dumps(data, indent=2)
    try:
        if path.exists() and path.read_text(encoding="utf-8") == payload:
            return
    except Exception:
        pass
    path.write_text(payload, encoding="utf-8")


def normalize_secret_token(value: object) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "", str(value or "").strip())


def encode_secret_b64(value: str) -> str:
    token = normalize_secret_token(value)
    return base64.b64encode(token.encode("utf-8")).decode("ascii") if token else ""


def decode_secret_b64(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        return normalize_secret_token(base64.b64decode(raw.encode("ascii"), validate=True).decode("utf-8"))
    except Exception:
        return ""


def normalize_api_key_items(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        items = value
    else:
        items = re.split(r"[\s,;]+", str(value))
    keys: list[str] = []
    seen: set[str] = set()
    for item in items:
        token = normalize_secret_token(item)
        if len(token) < 16 or token in seen:
            continue
        keys.append(token)
        seen.add(token)
    return keys


def encode_api_keys_b64(keys: object) -> list[str]:
    return [encoded for encoded in (encode_secret_b64(key) for key in normalize_api_key_items(keys)) if encoded]


def decode_api_keys_b64(values: object) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (list, tuple, set)):
        items = values
    else:
        items = re.split(r"[\s,;]+", str(values))
    keys: list[str] = []
    seen: set[str] = set()
    for item in items:
        token = decode_secret_b64(item)
        if len(token) < 16 or token in seen:
            continue
        keys.append(token)
        seen.add(token)
    return keys


def visible_secret_hint(keys: list[str]) -> str:
    return ", ".join(f"{key[:4]}...{key[-4:]}" for key in keys if len(key) >= 8)


def secret_list_stamp(values: object) -> str:
    return "|".join(str(value or "").strip() for value in (values if isinstance(values, (list, tuple, set)) else [values]) if str(value or "").strip())


def acquire_single_instance() -> bool:
    global SINGLE_INSTANCE_MUTEX
    if os.name != "nt" or KERNEL32 is None:
        return True
    try:
        mutex_name = "Local\\ComfyPortalSingleton"
        ctypes.set_last_error(0)
        handle = KERNEL32.CreateMutexW(None, False, mutex_name)
        if not handle:
            return True
        SINGLE_INSTANCE_MUTEX = handle
        already_exists = ctypes.get_last_error() == 183
        return not already_exists
    except Exception:
        return True


def load_config() -> dict:
    config = default_config()
    existing_raw = read_json(CONFIG_PATH, {})
    config.update(existing_raw)
    legacy_keys = normalize_api_key_items(existing_raw.get("civitai_api_key", "")) + normalize_api_key_items(existing_raw.get("civitai_api_keys", ""))
    stored_keys = decode_api_keys_b64(existing_raw.get("civitai_api_keys_b64", []))
    config["civitai_api_keys_b64"] = encode_api_keys_b64(stored_keys + legacy_keys)
    config["launch_mode"] = normalize_launch_mode(config.get("launch_mode", DEFAULT_LAUNCH_MODE))
    if "extra_launch_args" not in existing_raw:
        config["extra_launch_args"] = DEFAULT_EXTRA_LAUNCH_ARGS
    else:
        config["extra_launch_args"] = normalize_extra_launch_args(config.get("extra_launch_args", ""))
    config["launch_mode_confirmed"] = bool(config.get("launch_mode_confirmed", False))
    if "onboarding_completed" not in existing_raw:
        config["onboarding_completed"] = bool(config.get("launch_mode_confirmed")) and bool(existing_raw)
    else:
        config["onboarding_completed"] = bool(config.get("onboarding_completed", False))
    config.pop("smooth_animations", None)
    config.pop("civitai_api_key", None)
    config.pop("civitai_api_keys", None)
    return config


def save_config(config: dict) -> None:
    config = dict(config)
    config.pop("smooth_animations", None)
    legacy_keys = normalize_api_key_items(config.pop("civitai_api_key", ""))
    stored_keys = decode_api_keys_b64(config.get("civitai_api_keys_b64", []))
    raw_keys = normalize_api_key_items(config.pop("civitai_api_keys", ""))
    config["civitai_api_keys_b64"] = encode_api_keys_b64(stored_keys + legacy_keys + raw_keys)
    config["launch_mode"] = normalize_launch_mode(config.get("launch_mode", DEFAULT_LAUNCH_MODE))
    config["extra_launch_args"] = normalize_extra_launch_args(config.get("extra_launch_args", ""))
    config["launch_mode_confirmed"] = bool(config.get("launch_mode_confirmed", False))
    config["onboarding_completed"] = bool(config.get("onboarding_completed", False))
    write_json(CONFIG_PATH, config)
    invalidate_setup_status_cache()


def normalize_launch_mode(value: str) -> str:
    clean = str(value or "").strip().lower()
    legacy_map = {
        "nvidia_fast_fp16": "fp16",
        "nvidia": "fp16",
        "cpu": "cpu",
    }
    clean = legacy_map.get(clean, clean)
    return clean if clean in COMFY_LAUNCH_MODES else DEFAULT_LAUNCH_MODE


def parse_extra_launch_args(value: object) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    try:
        return [part for part in shlex.split(text, posix=True) if str(part).strip()]
    except ValueError:
        return [part for part in re.split(r"\s+", text) if part]


def normalize_extra_launch_args(value: object) -> str:
    args = parse_extra_launch_args(value)
    clean: list[str] = []
    seen: set[str] = set()
    for arg in args:
        token = str(arg).strip()
        if not token or token in seen:
            continue
        clean.append(token)
        seen.add(token)
    return " ".join(clean)


def comfy_launch_spec(config: dict | None = None) -> dict:
    config = config or load_config()
    mode = normalize_launch_mode(config.get("launch_mode", DEFAULT_LAUNCH_MODE))
    spec = dict(COMFY_LAUNCH_MODES[mode])
    spec["key"] = mode
    return spec


def comfy_launch_command(root: Path, config: dict | None = None) -> list[str]:
    config = config or load_config()
    spec = comfy_launch_spec(config)
    args = list(spec["args"])
    for extra_arg in parse_extra_launch_args(config.get("extra_launch_args", "")):
        if extra_arg not in args:
            args.append(extra_arg)
    return [
        str(root / "python_embeded" / "python.exe"),
        "-s",
        "ComfyUI\\main.py",
        *args,
    ]


def friend_url_for_subdomain(subdomain: str) -> str:
    return f"https://{subdomain}.loca.lt" if subdomain else ""


def custom_comfy_archive_candidates() -> list[Path]:
    return [
        BASE_DIR / CUSTOM_COMFY_ARCHIVE_NAME,
        BASE_DIR / COMFYUI_PORTABLE_ARCHIVE_NAME,
    ]


def custom_comfy_url_file() -> Path:
    return BASE_DIR / CUSTOM_COMFY_URL_FILENAME


def custom_comfy_folder_candidates() -> list[Path]:
    return [
        BASE_DIR / "ComfyPortal.custom_comfy",
        BASE_DIR / "custom_comfy",
    ]


def discover_workflow_files() -> list[Path]:
    candidates: list[Path] = []
    for name in WORKFLOW_CANDIDATE_NAMES:
        path = BASE_DIR / name
        if path.exists() and path.is_file():
            candidates.append(path)
    return candidates


def normalized_node_identifier(value: str) -> str:
    clean = str(value or "").strip().lower()
    clean = clean.removeprefix("https://github.com/")
    clean = clean.removesuffix(".git")
    return clean


def known_node_spec_map() -> dict[str, dict]:
    mapping: dict[str, dict] = {}
    for spec in REQUIRED_NODE_SPECS:
        mapping[normalized_node_identifier(spec["cnr_id"])] = spec
        mapping[normalized_node_identifier(spec["folder"])] = spec
        mapping[normalized_node_identifier(spec["repo"])] = spec
        repo_path = spec["repo"].split("github.com/")[-1]
        mapping[normalized_node_identifier(repo_path)] = spec
        for alias in spec.get("aliases", []):
            mapping[normalized_node_identifier(alias)] = spec
    return mapping


def resolve_comfy_package_source() -> dict:
    for folder_path in custom_comfy_folder_candidates():
        if is_comfy_root(folder_path):
            return {
                "kind": "local_folder",
                "label": f"Твоя сборка из папки {folder_path.name}",
                "source_root": Path(folder_path).resolve(),
            }

    for archive_path in custom_comfy_archive_candidates():
        if archive_path.exists() and archive_path.is_file():
            return {
                "kind": "local_archive",
                "label": f"Твоя сборка из файла {archive_path.name}",
                "archive_path": archive_path,
            }

    url_file = custom_comfy_url_file()
    if url_file.exists():
        try:
            custom_url = url_file.read_text(encoding="utf-8").strip()
        except Exception:
            custom_url = ""
        if custom_url:
            parsed = urlparse(custom_url)
            filename = Path(parsed.path).name or COMFYUI_PORTABLE_ARCHIVE_NAME
            if not filename.lower().endswith(".7z"):
                filename = COMFYUI_PORTABLE_ARCHIVE_NAME
            return {
                "kind": "remote_url",
                "label": f"Твоя сборка по ссылке {custom_url}",
            "url": custom_url,
            "archive_name": filename,
            }

    return {
        "kind": "official_latest",
        "label": "Официальная latest portable ComfyUI",
        "url": COMFYUI_PORTABLE_URL,
        "archive_name": COMFYUI_PORTABLE_ARCHIVE_NAME,
    }


def sanitize_subdomain(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9-]", "", (value or "").strip()).lower()


def is_valid_subdomain(value: str) -> bool:
    return bool(SUBDOMAIN_PATTERN.fullmatch(value or ""))


def extract_tunnel_subdomain(cmdline: str) -> str:
    match = SUBDOMAIN_ARG_PATTERN.search((cmdline or "").lower())
    return match.group(1) if match else ""


def extract_public_subdomain(url: str) -> str:
    match = PUBLIC_URL_PATTERN.search((url or "").strip().lower())
    return match.group(1) if match else ""


def friend_log_paths(link_id: str) -> tuple[Path, Path]:
    clean_id = re.sub(r"[^a-z0-9]", "", (link_id or "").lower())[:16] or "friend"
    return DATA_DIR / f"friend_{clean_id}.stdout.log", DATA_DIR / f"friend_{clean_id}.stderr.log"


def normalize_friend_entry(entry: dict | None) -> dict | None:
    if not isinstance(entry, dict):
        return None
    link_id = re.sub(r"[^a-z0-9]", "", str(entry.get("id", "")).lower())[:16] or secrets.token_hex(4)
    subdomain = sanitize_subdomain(str(entry.get("subdomain", "")))
    if not is_valid_subdomain(subdomain):
        return None
    pid = entry.get("pid")
    try:
        pid = int(pid) if pid is not None else None
    except Exception:
        pid = None
    url = str(entry.get("url", "")).strip() or friend_url_for_subdomain(subdomain)
    status = str(entry.get("status", "starting")).strip().lower()
    if status not in {"starting", "active", "error", "paused"}:
        status = "starting"
    try:
        created_at = float(entry.get("created_at", time.time()))
    except Exception:
        created_at = time.time()
    try:
        retry_after = float(entry.get("retry_after", 0.0) or 0.0)
    except Exception:
        retry_after = 0.0
    try:
        retry_delay = float(entry.get("retry_delay", DEFAULT_TUNNEL_RETRY_DELAY) or DEFAULT_TUNNEL_RETRY_DELAY)
    except Exception:
        retry_delay = DEFAULT_TUNNEL_RETRY_DELAY
    return {
        "id": link_id,
        "subdomain": subdomain,
        "url": url,
        "pid": pid,
        "status": status,
        "paused": bool(entry.get("paused", False)),
        "error": str(entry.get("error", "")).strip(),
        "created_at": created_at,
        "retry_after": retry_after,
        "retry_delay": retry_delay,
    }


def normalize_friend_links(entries: list[dict] | None, legacy_state: dict | None = None) -> list[dict]:
    normalized: list[dict] = []
    seen_subdomains: set[str] = set()
    seen_ids: set[str] = set()

    if isinstance(entries, list):
        for raw_entry in entries:
            entry = normalize_friend_entry(raw_entry)
            if not entry:
                continue
            if entry["id"] in seen_ids or entry["subdomain"] in seen_subdomains:
                continue
            normalized.append(entry)
            seen_ids.add(entry["id"])
            seen_subdomains.add(entry["subdomain"])
            if len(normalized) >= MAX_FRIEND_LINKS:
                return normalized

    legacy_state = legacy_state or {}
    legacy_subdomain = sanitize_subdomain(str(legacy_state.get("friend_subdomain", "")))
    if legacy_subdomain and is_valid_subdomain(legacy_subdomain) and legacy_subdomain not in seen_subdomains and len(normalized) < MAX_FRIEND_LINKS:
        normalized.append(
            {
                "id": secrets.token_hex(4),
                "subdomain": legacy_subdomain,
                "url": str(legacy_state.get("friend_last_url", "")).strip() or friend_url_for_subdomain(legacy_subdomain),
                "pid": legacy_state.get("friend_tunnel_pid"),
                "status": "active" if legacy_state.get("friend_tunnel_pid") else "starting",
                "paused": False,
                "error": "",
                "created_at": time.time(),
                "retry_after": 0.0,
                "retry_delay": DEFAULT_TUNNEL_RETRY_DELAY,
            }
        )
    return normalized


def normalize_state(raw_state: dict | None) -> dict:
    raw_state = raw_state or {}
    state = default_state()
    state.update(raw_state)
    has_explicit_friend_links = "friend_links" in raw_state
    state["friend_links"] = normalize_friend_links(
        raw_state.get("friend_links"),
        None if has_explicit_friend_links else raw_state,
    )
    for legacy_key in ("friend_tunnel_pid", "friend_subdomain", "friend_last_url"):
        state.pop(legacy_key, None)
    state["last_url"] = str(state.get("last_url", "")).strip()
    try:
        state["tunnel_retry_after"] = float(state.get("tunnel_retry_after", 0.0) or 0.0)
    except Exception:
        state["tunnel_retry_after"] = 0.0
    try:
        state["tunnel_retry_delay"] = float(state.get("tunnel_retry_delay", DEFAULT_TUNNEL_RETRY_DELAY) or DEFAULT_TUNNEL_RETRY_DELAY)
    except Exception:
        state["tunnel_retry_delay"] = DEFAULT_TUNNEL_RETRY_DELAY
    state["last_tunnel_error"] = str(state.get("last_tunnel_error", "")).strip()
    return state


def _read_state_unlocked() -> dict:
    return normalize_state(read_json(STATE_PATH, {}))


def _write_state_unlocked(state: dict) -> None:
    write_json(STATE_PATH, normalize_state(state))


def load_state() -> dict:
    with STATE_LOCK:
        return _read_state_unlocked()


def save_state(state: dict) -> None:
    with STATE_LOCK:
        _write_state_unlocked(state)


def update_state(mutator) -> tuple[dict, object]:
    with STATE_LOCK:
        state = _read_state_unlocked()
        result = mutator(state)
        _write_state_unlocked(state)
        return normalize_state(state), result


def update_friend_link_entry(link_id: str, updater) -> dict | None:
    def mutate(state: dict):
        entry = find_friend_link_entry(state, link_id)
        if not entry:
            return None
        updater(entry, state)
        return dict(entry)

    _, result = update_state(mutate)
    return result


def merge_friend_link_entries(updated_entries: list[dict]) -> None:
    if not updated_entries:
        return

    def mutate(state: dict):
        by_id = {entry.get("id"): entry for entry in state.get("friend_links", [])}
        for updated in updated_entries:
            current = by_id.get(updated.get("id"))
            if not current:
                continue
            current.update(
                {
                    "subdomain": updated.get("subdomain", current.get("subdomain", "")),
                    "url": updated.get("url", current.get("url", "")),
                    "pid": updated.get("pid"),
                    "status": updated.get("status", current.get("status", "starting")),
                    "paused": bool(updated.get("paused", current.get("paused", False))),
                    "error": updated.get("error", ""),
                    "created_at": updated.get("created_at", current.get("created_at", time.time())),
                    "retry_after": updated.get("retry_after", current.get("retry_after", 0.0)),
                    "retry_delay": updated.get("retry_delay", current.get("retry_delay", DEFAULT_TUNNEL_RETRY_DELAY)),
                }
            )

    update_state(mutate)


def normalize_subdomain(value: str) -> str:
    clean = sanitize_subdomain(value)
    return clean or "comfylocal5618"


def is_valid_main_subdomain(value: str) -> bool:
    clean = sanitize_subdomain(value)
    return len(clean) >= ONBOARDING_MIN_SUBDOMAIN_LEN and bool(SUBDOMAIN_PATTERN.fullmatch(clean))


def parse_version_tuple(value: str) -> tuple[int, ...]:
    clean = str(value or "").strip().lower().removeprefix("v")
    parts: list[int] = []
    for part in re.split(r"[.\-_]+", clean):
        if part.isdigit():
            parts.append(int(part))
        else:
            digits = "".join(ch for ch in part if ch.isdigit())
            if digits:
                parts.append(int(digits))
    return tuple(parts or [0])


def is_version_newer(remote: str, local: str = APP_VERSION) -> bool:
    return parse_version_tuple(remote) > parse_version_tuple(local)


def running_onefile_bundle() -> bool:
    return bool(getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))


def running_portable_bundle() -> bool:
    if not getattr(sys, "frozen", False):
        return False
    return (BASE_DIR / "lib").exists() or (BASE_DIR / "assets").exists()


def free_bytes_for_path(path: Path) -> int:
    try:
        target = path if path.exists() else path.parent
        return int(shutil.disk_usage(target).free)
    except Exception:
        return 0


def estimate_missing_setup_bytes(status: dict) -> int:
    total = 0
    if not status.get("comfy_ready"):
        total += PORTABLE_SIZE_HINT_BYTES
    if not status.get("manager_ready"):
        total += MANAGER_SIZE_HINT_BYTES
    for model in status.get("models", []):
        if not model.get("ready"):
            total += int(MODEL_SIZE_HINTS.get(model.get("title", ""), 250 * 1024 * 1024))
    for node in status.get("nodes", []):
        if not node.get("ready"):
            total += NODE_SIZE_HINT_BYTES
    return total


def has_enough_space_for_setup(status: dict, target_root: Path | None = None) -> tuple[bool, int, int]:
    missing_bytes = estimate_missing_setup_bytes(status)
    if missing_bytes <= 0:
        return True, free_bytes_for_path(target_root or BASE_DIR), 0
    anchor = target_root or current_comfy_root(load_config()) or BASE_DIR
    free_bytes = free_bytes_for_path(anchor)
    needed_bytes = missing_bytes + ONBOARDING_STORAGE_HEADROOM_BYTES
    return free_bytes >= needed_bytes, free_bytes, needed_bytes


def github_headers() -> dict[str, str]:
    return {
        "User-Agent": f"ComfyPortal/{APP_VERSION}",
        "Accept": "application/vnd.github+json",
    }


def github_release_asset_url(release: dict, preferred_name: str) -> str:
    for asset in release.get("assets", []) or []:
        if str(asset.get("name", "")) == preferred_name:
            return str(asset.get("browser_download_url", "") or "")
    return ""


def fetch_latest_release_info(force: bool = False) -> dict[str, object]:
    cache = UPDATE_RELEASE_CACHE
    now = time.monotonic()
    cached = cache.get("info")
    if cached and not force and (now - float(cache.get("at", 0.0) or 0.0)) < UPDATE_CHECK_CACHE_TTL:
        return dict(cached)
    request = urllib.request.Request(GITHUB_LATEST_RELEASE_API, headers=github_headers(), method="GET")
    with urllib.request.urlopen(request, timeout=DOWNLOAD_LINK_TIMEOUT) as response:
        data = json.loads(response.read().decode("utf-8", errors="replace"))
    tag_name = str(data.get("tag_name", "") or "").strip()
    info = {
        "tag_name": tag_name,
        "html_url": str(data.get("html_url", "") or GITHUB_RELEASES_URL),
        "portable_url": github_release_asset_url(data, GITHUB_PORTABLE_ASSET_NAME),
        "exe_url": github_release_asset_url(data, GITHUB_ONEFILE_ASSET_NAME),
        "available": bool(tag_name),
        "newer": is_version_newer(tag_name, APP_VERSION),
    }
    cache["info"] = dict(info)
    cache["at"] = now
    return dict(info)


def fetch_latest_comfy_release_info(force: bool = False) -> dict[str, object]:
    cache = COMFY_RELEASE_CACHE
    now = time.monotonic()
    cached = cache.get("info")
    if cached and not force and (now - float(cache.get("at", 0.0) or 0.0)) < UPDATE_CHECK_CACHE_TTL:
        return dict(cached)
    request = urllib.request.Request(COMFY_GITHUB_LATEST_RELEASE_API, headers=github_headers(), method="GET")
    with urllib.request.urlopen(request, timeout=DOWNLOAD_LINK_TIMEOUT) as response:
        data = json.loads(response.read().decode("utf-8", errors="replace"))
    tag_name = str(data.get("tag_name", "") or "").strip()
    info = {
        "tag_name": tag_name,
        "html_url": str(data.get("html_url", "") or COMFY_GITHUB_REPO_URL),
        "portable_url": COMFYUI_PORTABLE_URL,
        "available": bool(tag_name),
    }
    cache["info"] = dict(info)
    cache["at"] = now
    return dict(info)


def safe_latest_comfy_release_info(force: bool = False, allow_network: bool = True) -> dict[str, object]:
    cached = COMFY_RELEASE_CACHE.get("info")
    if not allow_network:
        if cached:
            return dict(cached)
        return {
            "tag_name": "",
            "html_url": COMFY_GITHUB_REPO_URL,
            "portable_url": COMFYUI_PORTABLE_URL,
            "available": False,
            "error": "ComfyUI latest еще не проверен.",
        }
    try:
        return fetch_latest_comfy_release_info(force=force)
    except Exception as exc:
        return {
            "tag_name": "",
            "html_url": COMFY_GITHUB_REPO_URL,
            "portable_url": COMFYUI_PORTABLE_URL,
            "available": False,
            "error": str(exc),
        }


def generate_friend_subdomain() -> str:
    return f"friendscomfy{secrets.randbelow(100000000):08d}"


def generate_unique_friend_subdomain(existing: set[str]) -> str:
    for _ in range(40):
        candidate = generate_friend_subdomain()
        if candidate not in existing:
            return candidate
    raise RuntimeError("Не удалось подобрать свободный friend subdomain.")


def friend_subdomains_from_state(state: dict | None = None) -> set[str]:
    state = state or load_state()
    return {
        sanitize_subdomain(str(entry.get("subdomain", "")))
        for entry in state.get("friend_links", [])
        if is_valid_subdomain(sanitize_subdomain(str(entry.get("subdomain", ""))))
    }


def normalize_root_path(value: str | Path | None) -> str:
    if not value:
        return ""
    try:
        return str(Path(value).expanduser().resolve())
    except Exception:
        return str(Path(value).expanduser())


def is_comfy_root(path: str | Path | None) -> bool:
    if not path:
        return False
    try:
        root = Path(path)
        return (root / "python_embeded" / "python.exe").exists() and (root / "ComfyUI" / "main.py").exists()
    except Exception:
        return False


def coerce_comfy_root(path: str | Path | None) -> Path | None:
    if not path:
        return None
    try:
        candidate = Path(path).expanduser()
        candidate = candidate.resolve()
    except Exception:
        candidate = Path(path).expanduser()
    if candidate.is_file():
        candidate = candidate.parent

    direct_candidates: list[Path] = [candidate]
    try:
        direct_candidates.extend(list(candidate.parents)[:4])
    except Exception:
        pass

    seen: set[str] = set()
    for probe in direct_candidates:
        try:
            key = str(probe.resolve()).lower()
        except Exception:
            key = str(probe).lower()
        if key in seen:
            continue
        seen.add(key)
        if is_comfy_root(probe):
            return probe.resolve()

    for probe in direct_candidates[:2]:
        discovered = discover_comfy_root_in(probe)
        if discovered:
            return discovered.resolve()
    return None


def comfy_source_marker_path(root: Path | None) -> Path | None:
    if not root:
        return None
    return Path(root) / COMFY_PACKAGE_MARKER_NAME


def read_comfy_source_marker(root: Path | None) -> dict:
    marker_path = comfy_source_marker_path(root)
    if not marker_path or not marker_path.exists():
        return {}
    try:
        return json.loads(marker_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_comfy_source_marker(root: Path | None, source: dict | None = None) -> None:
    if not root:
        return
    source = source or {}
    latest = safe_latest_comfy_release_info(force=True)
    marker = {
        "installed_by": APP_NAME,
        "installed_at": time.time(),
        "portal_version": APP_VERSION,
        "source_kind": str(source.get("kind", "official_latest")),
        "source_url": str(source.get("url", COMFYUI_PORTABLE_URL)),
        "archive_name": str(source.get("archive_name", COMFYUI_PORTABLE_ARCHIVE_NAME)),
        "tag_name": str(latest.get("tag_name", "") or ""),
    }
    marker_path = comfy_source_marker_path(root)
    try:
        if marker_path:
            marker_path.write_text(json.dumps(marker, indent=2), encoding="utf-8")
    except Exception:
        pass


def comfy_marker_stamp(root: Path | None) -> str:
    marker_path = comfy_source_marker_path(root)
    if not marker_path or not marker_path.exists():
        return ""
    try:
        stat = marker_path.stat()
        return f"{stat.st_mtime_ns}:{stat.st_size}"
    except Exception:
        return "marker"


def comfy_update_status(root: Path | None, source: dict | None = None) -> dict[str, object]:
    if not root:
        return {"available": False, "message": "", "installed_tag": "", "latest_tag": "", "latest_url": ""}
    source = source or {}
    if str(source.get("kind", "")) in {"local_folder", "local_archive", "remote_url"}:
        return {"available": False, "message": "Используется кастомная сборка ComfyUI.", "installed_tag": "", "latest_tag": "", "latest_url": ""}
    latest = safe_latest_comfy_release_info(allow_network=False)
    latest_tag = str(latest.get("tag_name", "") or "")
    marker = read_comfy_source_marker(root)
    installed_tag = str(marker.get("tag_name", "") or "")
    latest_url = str(latest.get("portable_url", COMFYUI_PORTABLE_URL) or COMFYUI_PORTABLE_URL)
    if not latest.get("available"):
        return {
            "available": False,
            "message": "Не удалось проверить latest ComfyUI. Продолжаем с текущей сборкой.",
            "installed_tag": installed_tag,
            "latest_tag": latest_tag,
            "latest_url": latest_url,
        }
    if installed_tag and latest_tag and is_version_newer(latest_tag, installed_tag):
        return {
            "available": True,
            "message": f"Доступна новая ComfyUI {latest_tag}. Текущая: {installed_tag}.",
            "installed_tag": installed_tag,
            "latest_tag": latest_tag,
            "latest_url": latest_url,
        }
    if not installed_tag:
        return {
            "available": True,
            "message": f"Версия ComfyUI неизвестна. Можно обновить до latest {latest_tag}.",
            "installed_tag": "",
            "latest_tag": latest_tag,
            "latest_url": latest_url,
        }
    return {
        "available": False,
        "message": f"ComfyUI актуальна: {installed_tag}.",
        "installed_tag": installed_tag,
        "latest_tag": latest_tag,
        "latest_url": latest_url,
    }


def legacy_startup_script_path() -> Path:
    appdata = Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming"))
    startup_dir = appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    startup_dir.mkdir(parents=True, exist_ok=True)
    return startup_dir / "Comfy Portal Autostart.vbs"


def current_launch_command(extra_args: list[str] | None = None) -> str:
    extra_args = extra_args or []
    quoted_args = " ".join(extra_args)
    if getattr(sys, "frozen", False):
        base = f'"{Path(sys.executable).resolve()}"'
    else:
        pythonw = Path(sys.executable).with_name("pythonw.exe")
        python_bin = pythonw if pythonw.exists() else Path(sys.executable)
        base = f'"{python_bin.resolve()}" "{Path(__file__).resolve()}"'
    return f"{base} {quoted_args}".strip()


def sync_windows_autostart(enabled: bool) -> None:
    legacy_target = legacy_startup_script_path()
    try:
        legacy_target.unlink()
    except FileNotFoundError:
        pass

    if os.name != "nt" or winreg is None:
        return

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, WINDOWS_RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if not enabled:
            try:
                winreg.DeleteValue(key, WINDOWS_AUTOSTART_VALUE)
            except FileNotFoundError:
                pass
            except OSError:
                pass
            return
        winreg.SetValueEx(key, WINDOWS_AUTOSTART_VALUE, 0, winreg.REG_SZ, current_launch_command(["--autorun"]))


def comfy_probe_priority(path: Path) -> tuple[int, int, str]:
    try:
        resolved = path.resolve()
    except Exception:
        resolved = path
    name = resolved.name.lower()
    full = str(resolved).lower()
    if "comfyui_windows_portable" in full:
        score = 0
    elif name == "comfyui":
        score = 1
    elif "comfyui" in name:
        score = 2
    elif "comfy" in name and "portal" not in name:
        score = 3
    elif "portable" in name:
        score = 4
    elif "stable diffusion" in full or "stable-diffusion" in full:
        score = 5
    else:
        score = 10
    return (score, len(name), name)


def iter_search_locations() -> list[Path]:
    user_home = Path.home()
    one_drive = Path(os.environ.get("OneDrive") or "")
    candidates = [
        BASE_DIR,
        BASE_DIR.parent,
        Path.cwd(),
        Path.cwd().parent,
        user_home / "Desktop",
        user_home / "Downloads",
        user_home / "Documents",
        user_home,
    ]
    if one_drive.exists():
        candidates.extend(
            [
                one_drive,
                one_drive / "Desktop",
                one_drive / "Downloads",
                one_drive / "Documents",
            ]
        )
    for anchor in (BASE_DIR, Path.cwd()):
        try:
            candidates.extend(list(anchor.parents)[:2])
        except Exception:
            continue
    preferred_drives: list[str] = []
    for source in (BASE_DIR, Path.cwd(), user_home):
        drive = source.drive.upper().rstrip(":")
        if drive and drive not in preferred_drives:
            preferred_drives.append(drive)
    for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
        if letter not in preferred_drives:
            preferred_drives.append(letter)
    for letter in preferred_drives:
        drive = Path(f"{letter}:/")
        if drive.exists():
            candidates.append(drive)

    seen: set[str] = set()
    result: list[Path] = []
    for candidate in candidates:
        try:
            key = str(candidate.resolve()).lower()
        except Exception:
            key = str(candidate).lower()
        if key in seen or not candidate.exists():
            continue
        seen.add(key)
        result.append(candidate)
    return result


def iter_probe_dirs(root: Path) -> list[Path]:
    probes = [root]
    try:
        children = sorted((child for child in root.iterdir() if child.is_dir()), key=comfy_probe_priority)
    except Exception:
        return probes

    is_drive_root = root == Path(root.anchor)
    likely_children = [child for child in children if comfy_probe_priority(child)[0] <= 4]
    other_children_limit = 24 if is_drive_root else 48
    other_children = [child for child in children if comfy_probe_priority(child)[0] > 4][:other_children_limit]
    prioritized_children = likely_children + other_children

    probes.extend(prioritized_children)
    grandchild_limit = 14 if is_drive_root else 22
    deep_seed_dirs: list[Path] = []
    for child in prioritized_children[:36]:
        try:
            grandchildren = sorted((grand for grand in child.iterdir() if grand.is_dir()), key=comfy_probe_priority)
        except Exception:
            continue
        likely_grandchildren = [grand for grand in grandchildren if comfy_probe_priority(grand)[0] <= 4]
        other_grandchildren = [grand for grand in grandchildren if comfy_probe_priority(grand)[0] > 4][:grandchild_limit]
        prioritized_grandchildren = likely_grandchildren + other_grandchildren
        probes.extend(prioritized_grandchildren)
        deep_seed_dirs.extend(prioritized_grandchildren[:18])

    great_grandchild_limit = 10 if is_drive_root else 16
    for seed in deep_seed_dirs[:42]:
        try:
            descendants = sorted((desc for desc in seed.iterdir() if desc.is_dir()), key=comfy_probe_priority)
        except Exception:
            continue
        likely_descendants = [desc for desc in descendants if comfy_probe_priority(desc)[0] <= 4]
        other_descendants = [desc for desc in descendants if comfy_probe_priority(desc)[0] > 4][:great_grandchild_limit]
        probes.extend(likely_descendants + other_descendants)
    return probes


def discover_comfy_root() -> Path | None:
    now = time.monotonic()
    cache_path = DISCOVER_COMFY_CACHE.get("path")
    cache_anchor = str(DISCOVER_COMFY_CACHE.get("anchor", "") or "")
    if (
        cache_anchor == "global"
        and now - float(DISCOVER_COMFY_CACHE.get("at", 0.0) or 0.0) < DISCOVER_COMFY_CACHE_TTL
    ):
        if cache_path:
            try:
                cached_root = Path(str(cache_path))
                if is_comfy_root(cached_root):
                    return cached_root.resolve()
            except Exception:
                pass
        else:
            return None

    seen: set[str] = set()
    deadline = now + DISCOVER_COMFY_BUDGET_SECONDS
    for root in iter_search_locations():
        if time.monotonic() >= deadline:
            break
        for probe in iter_probe_dirs(root):
            if time.monotonic() >= deadline:
                break
            try:
                probe_key = str(probe.resolve()).lower()
            except Exception:
                probe_key = str(probe).lower()
            if probe_key in seen:
                continue
            seen.add(probe_key)
            if is_comfy_root(probe):
                resolved = probe.resolve()
                DISCOVER_COMFY_CACHE.update({"at": time.monotonic(), "path": str(resolved), "anchor": "global"})
                return resolved
    DISCOVER_COMFY_CACHE.update({"at": time.monotonic(), "path": None, "anchor": "global"})
    return None


def resolve_comfy_root(config: dict | None = None, save_if_found: bool = True, allow_discover: bool = True) -> Path:
    config = config or load_config()
    configured_root = normalize_root_path(config.get("comfy_root", ""))
    if configured_root:
        coerced_root = coerce_comfy_root(configured_root)
        if coerced_root:
            if save_if_found and str(coerced_root) != configured_root:
                config["comfy_root"] = str(coerced_root)
                save_config(config)
            return coerced_root

    for candidate in (BASE_DIR, BASE_DIR.parent):
        root = coerce_comfy_root(candidate)
        if root:
            if save_if_found:
                config["comfy_root"] = str(root)
                save_config(config)
            return root

    if allow_discover:
        discovered = discover_comfy_root()
        if discovered:
            if save_if_found:
                config["comfy_root"] = str(discovered)
                save_config(config)
            return discovered
    raise RuntimeError("Не найдена portable-папка ComfyUI. Укажи ее в настройках приложения.")


def current_comfy_root(config: dict | None = None) -> Path | None:
    try:
        return resolve_comfy_root(config, save_if_found=False, allow_discover=False)
    except Exception:
        return None


def discover_comfy_root_in(base_dir: Path) -> Path | None:
    if not base_dir.exists():
        return None
    try:
        cache_anchor = str(base_dir.resolve()).lower()
    except Exception:
        cache_anchor = str(base_dir).lower()
    now = time.monotonic()
    if (
        DISCOVER_COMFY_CACHE.get("anchor") == cache_anchor
        and now - float(DISCOVER_COMFY_CACHE.get("at", 0.0) or 0.0) < DISCOVER_COMFY_CACHE_TTL
    ):
        cache_path = DISCOVER_COMFY_CACHE.get("path")
        if cache_path:
            try:
                cached_root = Path(str(cache_path))
                if is_comfy_root(cached_root):
                    return cached_root.resolve()
            except Exception:
                pass
    seen: set[str] = set()
    deadline = now + DISCOVER_COMFY_DEEP_BUDGET_SECONDS
    for probe in iter_probe_dirs(base_dir):
        if time.monotonic() >= deadline:
            break
        try:
            probe_key = str(probe.resolve()).lower()
        except Exception:
            probe_key = str(probe).lower()
        if probe_key in seen:
            continue
        seen.add(probe_key)
        if is_comfy_root(probe):
            resolved = probe.resolve()
            DISCOVER_COMFY_CACHE.update({"at": time.monotonic(), "path": str(resolved), "anchor": cache_anchor})
            return resolved
    DISCOVER_COMFY_CACHE.update({"at": time.monotonic(), "path": None, "anchor": cache_anchor})
    return None


def node_install_path(root: Path, spec: dict) -> Path:
    return root / "ComfyUI" / "custom_nodes" / spec["folder"]


def node_is_installed(root: Path | None, spec: dict) -> bool:
    if not root:
        return False
    path = node_install_path(root, spec)
    try:
        return path.is_dir() and any(path.iterdir())
    except Exception:
        return False


def manager_is_installed(root: Path | None) -> bool:
    if not root:
        return False
    path = root / "ComfyUI" / "custom_nodes" / "comfyui-manager"
    try:
        return path.is_dir() and any(path.iterdir())
    except Exception:
        return False


def starter_model_target_dir(root: Path, spec: dict) -> Path:
    return root.joinpath(*spec["relative_dir"])


def starter_model_target_path(root: Path, spec: dict) -> Path:
    return starter_model_target_dir(root, spec) / str(spec.get("filename", "")).strip()


def is_nonempty_file(path: Path) -> bool:
    try:
        return path.is_file() and path.stat().st_size > 0
    except Exception:
        return False


def starter_model_directory_files(target_dir: Path) -> list[Path]:
    try:
        return [item for item in target_dir.iterdir() if is_nonempty_file(item)]
    except Exception:
        return []


def starter_model_presence_stamp(root: Path | None, spec: dict) -> str:
    if not root:
        return "no-root"
    target_dir = starter_model_target_dir(root, spec)
    target_path = starter_model_target_path(root, spec)
    if is_nonempty_file(target_path):
        try:
            stat = target_path.stat()
            return f"target:{target_path.name}:{stat.st_mtime_ns}:{stat.st_size}"
        except Exception:
            return f"target:{target_path.name}:x"

    files = starter_model_directory_files(target_dir)
    if not files:
        return f"{target_dir.name}:0"

    markers: list[str] = []
    for file_path in sorted(files, key=lambda item: item.name.lower()):
        lower_name = file_path.name.lower()
        tracked_name = lower_name == str(spec.get("filename", "")).strip().lower()
        tracked_name = tracked_name or lower_name in {str(name).strip().lower() for name in spec.get("detect_names", ()) if str(name).strip()}
        tokens = [str(value).strip().lower() for value in spec.get("detect_contains_any", ()) if str(value).strip()]
        tracked_name = tracked_name or any(token in lower_name for token in tokens)
        if not tracked_name and not spec.get("detect_any_file"):
            continue
        try:
            stat = file_path.stat()
            markers.append(f"{file_path.name}:{stat.st_mtime_ns}:{stat.st_size}")
        except Exception:
            markers.append(f"{file_path.name}:x")
    return "|".join(markers) if markers else f"{target_dir.name}:present"


def starter_model_exists(root: Path | None, spec: dict) -> bool:
    if not root:
        return False
    target_path = starter_model_target_path(root, spec)
    if is_nonempty_file(target_path):
        return True

    target_dir = starter_model_target_dir(root, spec)
    files = starter_model_directory_files(target_dir)
    if not files:
        return False

    extra_names = [str(name or "").strip() for name in spec.get("detect_names", ()) if str(name or "").strip()]
    for extra_name in extra_names:
        if is_nonempty_file(target_dir / extra_name):
            return True

    extensions = {str(ext or "").strip().lower() for ext in spec.get("detect_extensions", ()) if str(ext or "").strip()}
    contains_any = [str(value or "").strip().lower() for value in spec.get("detect_contains_any", ()) if str(value or "").strip()]
    globs = [str(value or "").strip() for value in spec.get("detect_globs", ()) if str(value or "").strip()]

    if globs:
        for pattern in globs:
            try:
                if any(is_nonempty_file(path) for path in target_dir.glob(pattern)):
                    return True
            except Exception:
                continue

    if contains_any:
        for file_path in files:
            name = file_path.name.lower()
            if extensions and file_path.suffix.lower() not in extensions:
                continue
            if any(token in name for token in contains_any):
                return True

    if spec.get("detect_any_file"):
        for file_path in files:
            if not extensions or file_path.suffix.lower() in extensions:
                return True
    return False


def workflow_required_node_specs() -> tuple[list[dict], list[str], list[str]]:
    files = discover_workflow_files()
    if not files:
        return [], [], []

    mapping = known_node_spec_map()
    specs_by_folder = {spec["folder"]: spec for spec in REQUIRED_NODE_SPECS}
    unresolved: set[str] = set()
    used_files: list[str] = []

    def iter_workflow_node_dicts(data: object) -> list[dict]:
        if not isinstance(data, dict):
            return []
        raw_nodes = data.get("nodes")
        if isinstance(raw_nodes, list):
            return [node for node in raw_nodes if isinstance(node, dict)]
        if isinstance(raw_nodes, dict):
            return [node for node in raw_nodes.values() if isinstance(node, dict)]
        if all(isinstance(value, dict) for value in data.values()):
            return [node for node in data.values() if isinstance(node, dict) and ("class_type" in node or "type" in node)]
        return []

    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        nodes = iter_workflow_node_dicts(data)
        if not nodes:
            continue
        used_files.append(path.name)
        for node in nodes:
            if not isinstance(node, dict):
                continue
            properties = node.get("properties") or {}
            meta = node.get("_meta") or {}
            for raw_value in (
                properties.get("cnr_id"),
                properties.get("aux_id"),
                properties.get("Node name for S&R"),
                node.get("type"),
                node.get("class_type"),
                meta.get("title"),
            ):
                key = normalized_node_identifier(str(raw_value or ""))
                if not key:
                    continue
                spec = mapping.get(key)
                if not spec:
                    # Also try suffix matches like rgthree/rgthree-comfy -> rgthree-comfy
                    tail = key.split("/")[-1]
                    spec = mapping.get(tail)
                if spec:
                    specs_by_folder.setdefault(spec["folder"], spec)
                elif key and key not in {"comfy-core", "comfyui", "comfyui-manager"}:
                    unresolved.add(str(raw_value))

    return list(specs_by_folder.values()), sorted(unresolved), used_files


def collect_node_states(root: Path | None) -> list[dict]:
    states: list[dict] = []
    node_specs, _, _ = workflow_required_node_specs()
    specs_to_use = node_specs or list(REQUIRED_NODE_SPECS)
    for spec in specs_to_use:
        target = node_install_path(root, spec) if root else None
        states.append(
            {
                "title": spec["title"],
                "cnr_id": spec["cnr_id"],
                "folder": spec["folder"],
                "repo": spec["repo"],
                "path": str(target) if target else "",
                "ready": bool(root and node_is_installed(root, spec)),
            }
        )
    return states


def workflow_files_stamp() -> str:
    parts: list[str] = []
    for path in discover_workflow_files():
        try:
            stat = path.stat()
            parts.append(f"{path.name}:{stat.st_mtime_ns}:{stat.st_size}")
        except Exception:
            parts.append(f"{path.name}:missing")
    return "|".join(parts)


def setup_presence_stamp(root: str) -> str:
    normalized_root = normalize_root_path(root)
    if not normalized_root:
        return "no-root"
    root_path = Path(normalized_root)
    parts: list[str] = []
    manager_path = root_path / "ComfyUI" / "custom_nodes" / "comfyui-manager"
    candidates = [manager_path, *(node_install_path(root_path, spec) for spec in REQUIRED_NODE_SPECS)]
    for path in candidates:
        try:
            exists = path.exists()
            if exists:
                stat = path.stat()
                parts.append(f"{path.name}:1:{stat.st_mtime_ns}:{stat.st_size}")
            else:
                parts.append(f"{path.name}:0")
        except Exception:
            parts.append(f"{path.name}:x")
    for spec in STARTER_MODEL_SPECS:
        parts.append(f"{spec['title']}:{starter_model_presence_stamp(root_path, spec)}")
    workflow_stamp = workflow_files_stamp()
    if workflow_stamp:
        parts.append(f"wf:{workflow_stamp}")
    return "|".join(parts)


def setup_status_cache_key(config: dict | None = None) -> str:
    config = config or load_config()
    root = normalize_root_path(config.get("comfy_root", ""))
    source = resolve_comfy_package_source()
    return "|".join(
        [
            root,
            source.get("kind", ""),
            str(source.get("source_root", "")),
            str(source.get("archive_path", "")),
            str(source.get("url", "")),
            comfy_marker_stamp(Path(root) if root else None),
            secret_list_stamp(config.get("civitai_api_keys_b64", [])),
            setup_presence_stamp(root),
        ]
    )


def comfy_setup_status(config: dict | None = None) -> dict:
    config = config or load_config()
    root = current_comfy_root(config)
    configured_root = normalize_root_path(config.get("comfy_root", ""))
    root_path = root or (Path(configured_root) if configured_root else None)
    root_text = str(root_path) if root_path else ""
    source = resolve_comfy_package_source()
    update_status = comfy_update_status(root, source)
    workflow_specs, unresolved_workflow_nodes, workflow_files = workflow_required_node_specs()
    manager_ready = manager_is_installed(root)
    model_states = []
    for spec in STARTER_MODEL_SPECS:
        target = starter_model_target_path(root, spec) if root else None
        ready = starter_model_exists(root, spec)
        link_status = {"available": True, "message": "Ссылка доступна."} if ready else cached_direct_download_status(spec)
        model_states.append(
            {
                "title": spec["title"],
                "path": str(target) if target else "",
                "ready": ready,
                "download_available": bool(link_status.get("available", False)),
                "download_message": str(link_status.get("message", "") or ""),
                "download_checked": bool(link_status.get("checked", False)),
            }
        )
    return {
        "root": root_text,
        "source_label": source["label"],
        "source_kind": source["kind"],
        "comfy_ready": bool(root),
        "comfy_update_available": bool(update_status.get("available", False)),
        "comfy_update_message": str(update_status.get("message", "") or ""),
        "comfy_installed_tag": str(update_status.get("installed_tag", "") or ""),
        "comfy_latest_tag": str(update_status.get("latest_tag", "") or ""),
        "comfy_latest_url": str(update_status.get("latest_url", "") or ""),
        "manager_ready": manager_ready,
        "models": model_states,
        "nodes": collect_node_states(root),
        "workflow_files": workflow_files,
        "unresolved_workflow_nodes": unresolved_workflow_nodes,
    }


def cached_comfy_setup_status(config: dict | None = None, force: bool = False) -> dict:
    config = config or load_config()
    cache = SETUP_STATUS_CACHE
    key = setup_status_cache_key(config)
    now = time.monotonic()
    if (not force) and cache["status"] and cache["key"] == key and now - float(cache["at"]) < SETUP_STATUS_CACHE_TTL:
        return dict(cache["status"])
    status = comfy_setup_status(config)
    cache["status"] = dict(status)
    cache["key"] = key
    cache["at"] = now
    return dict(status)


def invalidate_setup_status_cache() -> None:
    SETUP_STATUS_CACHE["at"] = 0.0
    SETUP_STATUS_CACHE["key"] = ""
    SETUP_STATUS_CACHE["status"] = None


def setup_status_snapshot() -> dict | None:
    cached = SETUP_STATUS_CACHE.get("status")
    return dict(cached) if cached else None


def comfy_setup_has_missing(status: dict) -> bool:
    return (
        (not status.get("comfy_ready"))
        or (not status.get("manager_ready"))
        or any(not item.get("ready") for item in status.get("models", []))
        or any(not item.get("ready") for item in status.get("nodes", []))
    )


def comfy_core_has_missing(status: dict) -> bool:
    return (
        (not status.get("comfy_ready"))
        or (not status.get("manager_ready"))
        or any(not item.get("ready") for item in status.get("models", []))
    )


def comfy_nodes_have_missing(status: dict) -> bool:
    return any(not item.get("ready") for item in status.get("nodes", []))


def comfy_core_missing_count(status: dict) -> int:
    count = 0
    if not status.get("comfy_ready"):
        count += 1
    elif status.get("comfy_update_available"):
        count += 1
    if not status.get("manager_ready"):
        count += 1
    count += sum(1 for item in status.get("models", []) if not item.get("ready"))
    return count


def comfy_nodes_missing_count(status: dict) -> int:
    return sum(1 for item in status.get("nodes", []) if not item.get("ready"))


def missing_setup_titles(status: dict, include_nodes: bool = True) -> list[str]:
    missing: list[str] = []
    if not status.get("comfy_ready"):
        missing.append("Portable ComfyUI")
    elif status.get("comfy_update_available"):
        missing.append("Обновление ComfyUI")
    if not status.get("manager_ready"):
        missing.append("ComfyUI Manager")
    missing.extend(str(item.get("title", "model")) for item in status.get("models", []) if not item.get("ready"))
    if include_nodes:
        missing.extend(str(item.get("title", "node")) for item in status.get("nodes", []) if not item.get("ready"))
    return missing


def assert_setup_verified(config: dict | None = None, include_nodes: bool = True) -> dict:
    invalidate_setup_status_cache()
    status = cached_comfy_setup_status(config or load_config(), force=True)
    missing = missing_setup_titles(status, include_nodes=include_nodes)
    if missing:
        preview = ", ".join(missing[:6])
        extra = f" и еще {len(missing) - 6}" if len(missing) > 6 else ""
        raise RuntimeError(f"Установка завершилась не полностью. Не найдено: {preview}{extra}.")
    return status


def assert_nodes_verified(root: Path) -> None:
    missing = [spec["title"] for spec in pending_node_specs(root)]
    if missing:
        preview = ", ".join(missing[:6])
        extra = f" и еще {len(missing) - 6}" if len(missing) > 6 else ""
        raise RuntimeError(f"Установка nodes завершилась не полностью. Не найдено: {preview}{extra}.")


def estimate_setup_eta(status: dict) -> str:
    missing_models = sum(1 for item in status.get("models", []) if not item.get("ready"))
    comfy_missing = not status.get("comfy_ready")
    comfy_update = bool(status.get("comfy_update_available"))
    manager_missing = not status.get("manager_ready")
    source_kind = status.get("source_kind", "")

    if comfy_missing:
        if source_kind in {"local_installed", "local_folder"}:
            return "~2-6 мин"
        if source_kind in {"local_archive", "remote_url"}:
            return "~4-10 мин"
        return "~6-15 мин"
    if comfy_update:
        return "~4-10 мин"

    missing_nodes = sum(1 for item in status.get("nodes", []) if not item.get("ready"))
    missing_total = missing_models + missing_nodes + (1 if manager_missing else 0)
    if missing_total <= 0:
        return "~10-30 сек"
    if missing_total == 1:
        return "~30-90 сек"
    if missing_total == 2:
        return "~1-3 мин"
    return "~2-6 мин"


SETUP_STAGE_LABELS = {
    "prepare": "Подготовка",
    "download": "Загрузка",
    "extract": "Распаковка",
    "clone": "Клонирование",
    "deps": "Зависимости",
    "copy": "Копирование",
    "done": "Готово",
    "error": "Ошибка",
}


def build_setup_progress_meta(
    row_key: str = "",
    stage: str = "",
    row_percent: int | float | None = None,
    meta_text: str = "",
) -> str:
    payload: dict[str, object] = {}
    if row_key:
        payload["row_key"] = row_key
    if stage:
        payload["stage"] = stage
    if row_percent is not None:
        payload["row_percent"] = int(max(0, min(100, round(float(row_percent)))))
    if meta_text:
        payload["meta_text"] = meta_text
    if not payload:
        return ""
    return json.dumps(payload, ensure_ascii=False)


def parse_setup_progress_meta(meta: str) -> dict[str, object]:
    raw = (meta or "").strip()
    if not raw:
        return {}
    if raw.startswith("{"):
        try:
            payload = json.loads(raw)
            if isinstance(payload, dict):
                return payload
        except Exception:
            pass
    return {"meta_text": raw}


def setup_stage_label(stage: str, fallback: str = "Установка") -> str:
    return SETUP_STAGE_LABELS.get((stage or "").strip().lower(), fallback)


def error_looks_network_related(text: str) -> bool:
    lower_text = (text or "").strip().lower()
    if not lower_text:
        return False
    return any(hint in lower_text for hint in NETWORK_ERROR_HINTS)


def wait_for_internet_restore(status_cb=None, wait_message: str = "Нет интернета. Ждем сеть и продолжим.") -> None:
    first_loop = True
    while not internet_is_available(force=True):
        if status_cb and first_loop:
            try:
                status_cb(wait_message)
            except Exception:
                pass
        first_loop = False
        time.sleep(2.0)


def run_hidden_process_with_retries(
    command: list[str],
    cwd: Path,
    error_prefix: str,
    status_cb=None,
    cleanup_before_retry=None,
) -> subprocess.CompletedProcess:
    transient_errors = 0
    while True:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            cwd=str(cwd),
            **hidden_subprocess_kwargs(),
        )
        if result.returncode == 0:
            return result
        error_text = (result.stderr or result.stdout or "").strip() or error_prefix
        network_down = not internet_is_available(force=True)
        is_transient = network_down or error_looks_network_related(error_text)
        if is_transient:
            transient_errors += 1
            if cleanup_before_retry:
                try:
                    cleanup_before_retry()
                except Exception:
                    pass
            if network_down:
                wait_for_internet_restore(status_cb=status_cb)
            else:
                if status_cb:
                    try:
                        status_cb("Сеть дернулась. Повторяем шаг установки...")
                    except Exception:
                        pass
                time.sleep(min(3.0 + transient_errors, 10.0))
            continue
        raise RuntimeError(error_text)


def format_bytes(num_bytes: float) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(max(num_bytes, 0.0))
    index = 0
    while value >= 1024.0 and index < len(units) - 1:
        value /= 1024.0
        index += 1
    precision = 0 if index == 0 else 1
    return f"{value:.{precision}f} {units[index]}"


def starter_model_request(spec: dict, config: dict | None = None) -> tuple[str, dict[str, str], str]:
    requests = starter_model_requests(spec, config)
    return requests[0]


def civitai_auth_required_message() -> str:
    return "Civitai требует вход/API key: прямая ссылка закрыта для публичной загрузки."


def is_civitai_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return "civitai.com" in host or "civitai.red" in host


CIVITAI_KEY_ROTATION = {"index": 0}


def append_civitai_token(url: str, token: str) -> str:
    clean_token = normalize_secret_token(token)
    if not clean_token:
        return url
    parsed = urlparse(url)
    query = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True) if key.lower() != "token"]
    query.append(("token", clean_token))
    return urlunparse(parsed._replace(query=urlencode(query)))


def civitai_url_mirrors(url: str) -> list[str]:
    if not is_civitai_url(url):
        return [url]
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    mirrors = [url]
    alternate_host = ""
    if "civitai.red" in host:
        alternate_host = parsed.netloc.replace("civitai.red", "civitai.com")
    elif "civitai.com" in host:
        alternate_host = parsed.netloc.replace("civitai.com", "civitai.red")
    if alternate_host:
        alternate_url = urlunparse(parsed._replace(netloc=alternate_host))
        if alternate_url not in mirrors:
            mirrors.append(alternate_url)
    return mirrors


def civitai_api_keys(config: dict | None = None) -> list[str]:
    keys: list[str] = []
    keys.extend(normalize_api_key_items(os.environ.get("COMFY_PORTAL_CIVITAI_KEYS", "")))
    keys.extend(decode_api_keys_b64(os.environ.get("COMFY_PORTAL_CIVITAI_KEYS_B64", "")))
    keys.extend(decode_api_keys_b64(BUNDLED_CIVITAI_KEYS_B64))
    if config is None:
        try:
            config = load_config()
        except Exception:
            config = {}
    keys.extend(decode_api_keys_b64((config or {}).get("civitai_api_keys_b64", [])))
    keys.extend(normalize_api_key_items((config or {}).get("civitai_api_keys", "")))
    deduped: list[str] = []
    seen: set[str] = set()
    for key in keys:
        if key and key not in seen:
            deduped.append(key)
            seen.add(key)
    return deduped


def rotated_civitai_keys(config: dict | None = None) -> list[str]:
    keys = civitai_api_keys(config)
    if len(keys) <= 1:
        return keys
    start = int(CIVITAI_KEY_ROTATION.get("index", 0) or 0) % len(keys)
    CIVITAI_KEY_ROTATION["index"] = (start + 1) % len(keys)
    return keys[start:] + keys[:start]


def civitai_headers(token: str) -> dict[str, str]:
    clean_token = normalize_secret_token(token)
    return {"Authorization": f"Bearer {clean_token}"} if clean_token else {}


def civitai_request_variants(url: str, config: dict | None = None) -> list[tuple[str, dict[str, str]]]:
    headers = {"User-Agent": DOWNLOAD_USER_AGENT}
    if not is_civitai_url(url):
        return [(url, headers)]
    variants: list[tuple[str, dict[str, str]]] = []
    for mirror_url in civitai_url_mirrors(url):
        for token in rotated_civitai_keys(config):
            variants.append((append_civitai_token(mirror_url, token), {**headers, **civitai_headers(token)}))
    if not variants:
        variants.extend((mirror_url, headers) for mirror_url in civitai_url_mirrors(url))
    return variants


def starter_model_requests(spec: dict, config: dict | None = None) -> list[tuple[str, dict[str, str], str]]:
    filename = str(spec.get("filename", ""))
    return [(url, headers, filename) for url, headers in civitai_request_variants(str(spec["url"]), config)]


def is_civitai_auth_redirect(location: str | None) -> bool:
    if not location:
        return False
    lower = location.lower()
    return "/login" in lower or "download-auth" in lower or "returnurl=%2fmodel-versions" in lower


def check_direct_download_url(url: str) -> tuple[bool, str]:
    host = urlparse(url).netloc.lower()

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    attempts: list[tuple[str, str, dict[str, str]]] = []
    for request_url, headers in civitai_request_variants(url):
        if "civitai.com" in host or "civitai.red" in host:
            attempts.append((request_url, "GET", {**headers, "Range": "bytes=0-0"}))
        else:
            attempts.append((request_url, "HEAD", headers))
            attempts.append((request_url, "GET", {**headers, "Range": "bytes=0-0"}))
    last_status: int | None = None
    transient_failure = False
    auth_failure = False
    for request_url, method, request_headers in attempts:
        try:
            request = urllib.request.Request(request_url, headers=request_headers, method=method)
            with opener.open(request, timeout=DOWNLOAD_LINK_TIMEOUT) as response:
                status_code = int(getattr(response, "status", response.getcode()) or 200)
                if 200 <= status_code < 400:
                    return True, "Ссылка доступна."
        except urllib.error.HTTPError as exc:
            status_code = int(getattr(exc, "code", 0) or 0)
            last_status = status_code or last_status
            if 300 <= status_code < 400:
                if is_civitai_auth_redirect(exc.headers.get("Location")):
                    auth_failure = True
                    continue
                return True, "Ссылка доступна."
            if is_civitai_url(url) and status_code in {401, 403}:
                auth_failure = True
                continue
            if is_civitai_url(url) and 500 <= status_code < 600:
                transient_failure = True
                continue
            if status_code == 405 and method == "HEAD":
                continue
            return False, f"Сейчас скачать нельзя: сервер отвечает {status_code}."
        except urllib.error.URLError as exc:
            reason_text = str(getattr(exc, "reason", exc) or exc).lower()
            if any(token in reason_text for token in ("timed out", "timeout", "handshake", "temporary")):
                transient_failure = True
                continue
            continue
        except Exception as exc:
            reason_text = str(exc or "").lower()
            if any(token in reason_text for token in ("timed out", "timeout", "handshake", "temporary")):
                transient_failure = True
            continue
    if auth_failure:
        return False, civitai_auth_required_message()
    if last_status is not None:
        return False, f"Сейчас скачать нельзя: сервер отвечает {last_status}."
    if transient_failure:
        return True, "Проверка ссылки долго отвечает. Попробуем скачать при установке."
    return False, "Сейчас скачать нельзя: ссылка временно недоступна."


def cached_direct_download_status(spec: dict, force: bool = False) -> dict[str, object]:
    url = str(spec.get("url", "")).strip()
    if not url:
        return {"available": False, "message": "Сейчас скачать нельзя: ссылка не задана.", "checked": True}
    cache_items = DOWNLOAD_LINK_STATUS_CACHE["items"]
    cache_key = f"{spec.get('title', '')}|{url}|{secret_list_stamp(load_config().get('civitai_api_keys_b64', [])) if is_civitai_url(url) else ''}"
    cached = cache_items.get(cache_key)
    now = time.monotonic()
    if cached and not force and (now - float(cached.get("at", 0.0))) < DOWNLOAD_LINK_CACHE_TTL:
        return {
            "available": bool(cached.get("available")),
            "message": str(cached.get("message", "") or ""),
            "checked": True,
        }
    if (not force) and not cached:
        return {"available": True, "message": "Проверяем ссылку...", "checked": False}
    available, message = check_direct_download_url(url)
    cache_items[cache_key] = {"available": available, "message": message, "at": time.monotonic()}
    return {"available": available, "message": message, "checked": True}


def refresh_setup_download_links(config: dict | None = None) -> None:
    config = config or load_config()
    root = current_comfy_root(config)
    for spec in pending_starter_model_specs(root):
        cached_direct_download_status(spec, force=True)


def download_file(url: str, destination: Path, progress_cb=None, status_cb=None, request_headers: dict[str, str] | None = None) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_suffix(destination.suffix + ".part")
    started_at = time.monotonic()
    transient_errors = 0
    while True:
        existing_size = temp_path.stat().st_size if temp_path.exists() else 0
        headers = {"User-Agent": DOWNLOAD_USER_AGENT}
        if request_headers:
            headers.update(request_headers)
        if existing_size > 0:
            headers["Range"] = f"bytes={existing_size}-"
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                response_status = int(getattr(response, "status", response.getcode()) or 200)
                final_url = str(response.geturl() or "")
                content_type = str(response.headers.get("Content-Type") or "").lower()
                if is_civitai_url(url) and (is_civitai_auth_redirect(final_url) or "text/html" in content_type):
                    raise RuntimeError(civitai_auth_required_message())
                content_length = int(response.headers.get("Content-Length") or 0)
                if existing_size > 0 and response_status != 206:
                    try:
                        temp_path.unlink()
                    except FileNotFoundError:
                        pass
                    existing_size = 0
                    transient_errors += 1
                    continue
                total = existing_size + content_length if content_length else 0
                last_emit = 0.0
                mode = "ab" if existing_size > 0 else "wb"
                downloaded = existing_size
                with temp_path.open(mode) as handle:
                    while True:
                        chunk = response.read(DOWNLOAD_CHUNK_SIZE)
                        if not chunk:
                            break
                        handle.write(chunk)
                        downloaded += len(chunk)
                        if progress_cb:
                            now = time.monotonic()
                            if total <= 0 or now - last_emit >= DOWNLOAD_PROGRESS_INTERVAL:
                                rate = downloaded / max(now - started_at, 0.1)
                                progress_cb(downloaded, total, rate)
                                last_emit = now
                if progress_cb:
                    rate = downloaded / max(time.monotonic() - started_at, 0.1)
                    progress_cb(downloaded, total, rate)
                transient_errors = 0
                break
        except urllib.error.HTTPError as exc:
            status_code = int(getattr(exc, "code", 0) or 0)
            if is_civitai_url(url) and (status_code in {401, 403} or is_civitai_auth_redirect(exc.headers.get("Location"))):
                raise RuntimeError(civitai_auth_required_message()) from exc
            if progress_cb:
                current_total = temp_path.stat().st_size if temp_path.exists() else 0
                progress_cb(current_total, current_total or 0, 0.0)
            network_down = not internet_is_available(force=True)
            if network_down:
                wait_for_internet_restore(status_cb=status_cb)
                continue
            error_text = str(exc)
            if error_looks_network_related(error_text) and transient_errors < 8:
                transient_errors += 1
                if status_cb:
                    try:
                        status_cb("Сеть дернулась. Пробуем продолжить загрузку...")
                    except Exception:
                        pass
                time.sleep(min(3.0 + transient_errors, 10.0))
                continue
            raise RuntimeError(f"Не удалось скачать файл: {exc}") from exc
        except Exception as exc:
            if is_civitai_url(url) and civitai_auth_required_message() in str(exc):
                raise RuntimeError(civitai_auth_required_message()) from exc
            if progress_cb:
                current_total = temp_path.stat().st_size if temp_path.exists() else 0
                progress_cb(current_total, current_total or 0, 0.0)
            network_down = not internet_is_available(force=True)
            if network_down:
                wait_for_internet_restore(status_cb=status_cb)
                continue
            error_text = str(exc)
            if error_looks_network_related(error_text) and transient_errors < 8:
                transient_errors += 1
                if status_cb:
                    try:
                        status_cb("Сеть дернулась. Пробуем продолжить загрузку...")
                    except Exception:
                        pass
                time.sleep(min(3.0 + transient_errors, 10.0))
                continue
            raise RuntimeError(f"Не удалось скачать файл: {exc}") from exc
    temp_path.replace(destination)
    return destination


def hidden_subprocess_kwargs(new_process_group: bool = False) -> dict:
    kwargs: dict = {}
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        if new_process_group:
            creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = getattr(subprocess, "SW_HIDE", 0)
        kwargs["creationflags"] = creationflags
        kwargs["startupinfo"] = startupinfo
    return kwargs


def set_windows_app_user_model_id(app_id: str = APP_USER_MODEL_ID) -> None:
    if os.name != "nt":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(str(app_id))
    except Exception:
        pass


def ps_quote(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def prepare_release_update(release_info: dict[str, object]) -> str:
    tag_name = str(release_info.get("tag_name", "") or "").strip() or "latest"
    temp_dir = DATA_DIR / "updates"
    temp_dir.mkdir(parents=True, exist_ok=True)
    current_pid = os.getpid()

    if running_portable_bundle():
        asset_url = str(release_info.get("portable_url", "") or "")
        if not asset_url:
            raise RuntimeError("Для portable-обновления не найден zip asset в релизе.")
        zip_path = temp_dir / f"Comfy.Portal.{tag_name}.zip"
        download_file(asset_url, zip_path)
        script_path = temp_dir / "apply_portable_update.ps1"
        target_dir = BASE_DIR
        target_exe = target_dir / "Comfy Portal.exe"
        stage_dir = temp_dir / f"stage_{tag_name}"
        script_text = f"""
$ErrorActionPreference = 'Stop'
$pidToWait = {current_pid}
$zipPath = {ps_quote(zip_path)}
$stageDir = {ps_quote(stage_dir)}
$targetDir = {ps_quote(target_dir)}
$targetExe = {ps_quote(target_exe)}
while (Get-Process -Id $pidToWait -ErrorAction SilentlyContinue) {{ Start-Sleep -Milliseconds 350 }}
if (Test-Path -LiteralPath $stageDir) {{ Remove-Item -LiteralPath $stageDir -Recurse -Force -ErrorAction SilentlyContinue }}
Expand-Archive -LiteralPath $zipPath -DestinationPath $stageDir -Force
Get-ChildItem -LiteralPath $stageDir | ForEach-Object {{
    Copy-Item -LiteralPath $_.FullName -Destination $targetDir -Recurse -Force
}}
Start-Sleep -Milliseconds 250
if (Test-Path -LiteralPath $targetExe) {{
    Start-Process -FilePath $targetExe
}}
"""
    else:
        asset_url = str(release_info.get("exe_url", "") or "")
        if not asset_url:
            raise RuntimeError("Для этой сборки в релизе нет отдельного .exe для автообновления.")
        exe_path = temp_dir / "Comfy Portal.new.exe"
        download_file(asset_url, exe_path)
        script_path = temp_dir / "apply_onefile_update.ps1"
        current_exe = Path(sys.executable).resolve()
        backup_exe = current_exe.with_suffix(".old.exe")
        script_text = f"""
$ErrorActionPreference = 'Stop'
$pidToWait = {current_pid}
$newExe = {ps_quote(exe_path)}
$targetExe = {ps_quote(current_exe)}
$backupExe = {ps_quote(backup_exe)}
while (Get-Process -Id $pidToWait -ErrorAction SilentlyContinue) {{ Start-Sleep -Milliseconds 350 }}
if (Test-Path -LiteralPath $backupExe) {{ Remove-Item -LiteralPath $backupExe -Force -ErrorAction SilentlyContinue }}
if (Test-Path -LiteralPath $targetExe) {{ Move-Item -LiteralPath $targetExe -Destination $backupExe -Force }}
Move-Item -LiteralPath $newExe -Destination $targetExe -Force
Start-Sleep -Milliseconds 250
Start-Process -FilePath $targetExe
"""
    script_path.write_text(script_text.strip(), encoding="utf-8")
    subprocess.Popen(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
        ],
        close_fds=True,
        **hidden_subprocess_kwargs(new_process_group=True),
    )
    return f"Обновление {tag_name} скачано. Перезапускаем портал..."


def seven_zip_executable_candidates() -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()
    for filename in ("7zr.exe", "7za.exe", "7zz.exe", "7z.exe"):
        path = resolve_tool_path(filename)
        if path.exists():
            key = str(path).lower()
            if key not in seen:
                candidates.append(str(path))
                seen.add(key)
    for name in ("7zr", "7z", "7zz", "7za"):
        path_text = shutil.which(name)
        if path_text:
            key = path_text.lower()
            if key not in seen:
                candidates.append(path_text)
                seen.add(key)
    return candidates


def compact_process_error(result: subprocess.CompletedProcess) -> str:
    text = (result.stderr or result.stdout or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text[:600] if text else f"код выхода {result.returncode}"


def extract_7z_archive(archive_path: Path, destination_dir: Path) -> None:
    destination_dir.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []

    for seven_zip in seven_zip_executable_candidates():
        try:
            result = subprocess.run(
                [seven_zip, "x", "-y", f"-o{destination_dir}", str(archive_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                **hidden_subprocess_kwargs(),
            )
            if result.returncode == 0:
                return
            errors.append(f"7-Zip ({Path(seven_zip).name}): {compact_process_error(result)}")
        except Exception as exc:
            errors.append(f"7-Zip ({Path(seven_zip).name}): {exc}")

    try:
        import py7zr

        with py7zr.SevenZipFile(archive_path, mode="r") as archive:
            archive.extractall(path=destination_dir)
        return
    except ModuleNotFoundError:
        errors.append("py7zr: модуль не найден")
    except Exception as exc:
        errors.append(f"py7zr: {exc}")

    tar_path = shutil.which("tar")
    if tar_path:
        try:
            result = subprocess.run(
                [tar_path, "-xf", str(archive_path), "-C", str(destination_dir)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                **hidden_subprocess_kwargs(),
            )
            if result.returncode == 0:
                return
            errors.append(f"tar: {compact_process_error(result)}")
        except Exception as exc:
            errors.append(f"tar: {exc}")
    else:
        errors.append("tar: не найден")

    details = " | ".join(error for error in errors if error)
    raise RuntimeError(
        "Не удалось распаковать .7z архив ComfyUI. "
        "Для архивов с BCJ2 нужен bundled 7-Zip extractor, он должен лежать в tools/7zr.exe рядом с приложением. "
        f"Детали: {details}"
    )


PRESERVED_COMFY_UPDATE_DIRS = {
    ("ComfyUI", "models"),
    ("ComfyUI", "custom_nodes"),
    ("ComfyUI", "input"),
    ("ComfyUI", "output"),
    ("ComfyUI", "user"),
    ("ComfyUI", "workflows"),
}


def should_preserve_comfy_update_path(relative_path: Path) -> bool:
    parts = tuple(relative_path.parts)
    for preserved in PRESERVED_COMFY_UPDATE_DIRS:
        if len(parts) >= len(preserved) and tuple(part.lower() for part in parts[: len(preserved)]) == tuple(part.lower() for part in preserved):
            return True
    return False


def merge_comfy_update_tree(source_root: Path, target_root: Path, base_source: Path | None = None) -> None:
    base_source = base_source or source_root
    for item in source_root.iterdir():
        relative = item.relative_to(base_source)
        if should_preserve_comfy_update_path(relative):
            continue
        destination = target_root / relative
        if item.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            merge_comfy_update_tree(item, target_root, base_source)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, destination)


def install_comfyui_portable(install_parent: Path, progress=None, force_update: bool = False) -> Path:
    install_parent = install_parent.expanduser().resolve()
    install_parent.mkdir(parents=True, exist_ok=True)
    existing_root = discover_comfy_root_in(install_parent)
    if existing_root and not force_update:
        if progress:
            progress(1.0, "Portable ComfyUI уже найден", build_setup_progress_meta("comfy", "done", 100, "Portable уже установлен"))
        config = load_config()
        config["comfy_root"] = str(existing_root)
        save_config(config)
        return existing_root

    source = resolve_comfy_package_source()
    if existing_root and force_update:
        if progress:
            progress(0.0, "Обновляем portable ComfyUI", build_setup_progress_meta("comfy", "prepare", 0, "Сохраняем models/custom_nodes/output"))
        try:
            stop_all()
        except Exception:
            pass
        with tempfile.TemporaryDirectory(prefix="comfyportal_comfy_update_") as temp_dir:
            temp_parent = Path(temp_dir)
            if source["kind"] in {"local_installed", "local_folder"}:
                new_root = Path(source["source_root"]).resolve()
            elif source["kind"] == "local_archive":
                if progress:
                    progress(0.20, "Распаковываем новую ComfyUI", build_setup_progress_meta("comfy", "extract", None, "Локальный архив"))
                extract_7z_archive(Path(source["archive_path"]), temp_parent)
                new_root = discover_comfy_root_in(temp_parent)
            else:
                archive_name = str(source.get("archive_name", COMFYUI_PORTABLE_ARCHIVE_NAME))
                archive_path = DATA_DIR / archive_name
                if progress:
                    progress(0.0, f"Скачиваем обновление {archive_name}", build_setup_progress_meta("comfy", "prepare", 0, "Подготовка"))
                download_file(
                    str(source["url"]),
                    archive_path,
                    progress_cb=(
                        None
                        if not progress
                        else lambda downloaded, total, rate: progress(
                            0.05 + (0.65 * (downloaded / total if total else 0.0)),
                            f"Скачиваем обновление {archive_name}",
                            build_setup_progress_meta(
                                "comfy",
                                "download",
                                100 * (downloaded / total if total else 0.0),
                                f"{format_bytes(rate)}/s" + (f" • {format_bytes(downloaded)} / {format_bytes(total)}" if total else ""),
                            ),
                        )
                    ),
                    status_cb=(
                        None
                        if not progress
                        else lambda text: progress(
                            0.05,
                            f"Скачиваем обновление {archive_name}",
                            build_setup_progress_meta("comfy", "download", None, text),
                        )
                    ),
                )
                try:
                    if progress:
                        progress(0.75, "Распаковываем обновление ComfyUI", build_setup_progress_meta("comfy", "extract", None, "Распаковка"))
                    extract_7z_archive(archive_path, temp_parent)
                finally:
                    try:
                        archive_path.unlink()
                    except FileNotFoundError:
                        pass
                new_root = discover_comfy_root_in(temp_parent)
            if not new_root or not is_comfy_root(new_root):
                raise RuntimeError("Обновление ComfyUI скачано, но portable-папка внутри архива не найдена.")
            if progress:
                progress(0.92, "Обновляем файлы ComfyUI", build_setup_progress_meta("comfy", "copy", None, "models/custom_nodes/output сохраняются"))
            merge_comfy_update_tree(new_root, existing_root)
        write_comfy_source_marker(existing_root, source)
        config = load_config()
        config["comfy_root"] = str(existing_root)
        save_config(config)
        if progress:
            progress(1.0, "ComfyUI обновлена", build_setup_progress_meta("comfy", "done", 100, "Обновление готово"))
        return existing_root

    if source["kind"] in {"local_installed", "local_folder"}:
        source_root = Path(source["source_root"]).resolve()
        target_root = install_parent / source_root.name
        if progress:
            progress(0.0, f"Копируем твою сборку {source_root.name}", build_setup_progress_meta("comfy", "copy", None, "Локальная копия"))
        if target_root.exists():
            if is_comfy_root(target_root):
                return target_root.resolve()
            raise RuntimeError(f"Папка {target_root} уже занята и не похожа на portable ComfyUI.")
        shutil.copytree(source_root, target_root)
        if progress:
            progress(1.0, "Твоя portable-сборка скопирована", build_setup_progress_meta("comfy", "done", 100, "Готово"))
        extracted_root = discover_comfy_root_in(install_parent)
        if not extracted_root:
            raise RuntimeError("Не удалось скопировать твою portable-сборку ComfyUI.")
        config = load_config()
        config["comfy_root"] = str(extracted_root)
        save_config(config)
        write_comfy_source_marker(extracted_root, source)
        return extracted_root

    if source["kind"] == "local_archive":
        archive_path = Path(source["archive_path"])
        cleanup_archive = False
        if progress:
            progress(0.0, f"Используем архив {archive_path.name}", build_setup_progress_meta("comfy", "prepare", 0, "Локальный архив"))
    else:
        archive_name = str(source.get("archive_name", COMFYUI_PORTABLE_ARCHIVE_NAME))
        archive_path = DATA_DIR / archive_name
        if progress:
            progress(0.0, f"Скачиваем {archive_name}", build_setup_progress_meta("comfy", "prepare", 0, "Подготовка"))
        download_file(
            str(source["url"]),
            archive_path,
            progress_cb=(
                None
                if not progress
                else lambda downloaded, total, rate: progress(
                    0.05 + (0.70 * (downloaded / total if total else 0.0)),
                    f"Скачиваем {archive_name}",
                    build_setup_progress_meta(
                        "comfy",
                        "download",
                        100 * (downloaded / total if total else 0.0),
                        f"{format_bytes(rate)}/s" + (f" • {format_bytes(downloaded)} / {format_bytes(total)}" if total else ""),
                    ),
                )
            ),
            status_cb=(
                None
                if not progress
                else lambda text: progress(
                    0.05,
                    f"Скачиваем {archive_name}",
                    build_setup_progress_meta("comfy", "download", None, text),
                )
            ),
        )
        cleanup_archive = True
    try:
        if progress:
            progress(0.80, "Распаковываем portable ComfyUI", build_setup_progress_meta("comfy", "extract", None, "Распаковка"))
        extract_7z_archive(archive_path, install_parent)
    finally:
        if cleanup_archive:
            try:
                archive_path.unlink()
            except FileNotFoundError:
                pass
    if progress:
        progress(1.0, "Portable ComfyUI готов", build_setup_progress_meta("comfy", "done", 100, "Готово"))
    extracted_root = discover_comfy_root_in(install_parent)
    if not extracted_root:
        raise RuntimeError("ComfyUI скачан, но portable-папка после распаковки не найдена.")
    config = load_config()
    config["comfy_root"] = str(extracted_root)
    save_config(config)
    write_comfy_source_marker(extracted_root, source)
    return extracted_root


def install_comfyui_manager(root: Path, progress=None) -> str:
    manager_dir = root / "ComfyUI" / "custom_nodes" / "comfyui-manager"
    if manager_is_installed(root):
        if progress:
            progress(1.0, "ComfyUI Manager уже установлен", build_setup_progress_meta("manager", "done", 100, "Manager уже на месте"))
        return "Manager уже установлен."
    if manager_dir.exists():
        shutil.rmtree(manager_dir, ignore_errors=True)

    manager_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="comfyportal_manager_") as temp_dir:
        temp_path = Path(temp_dir)
        archive_path = temp_path / "comfyui-manager.zip"
        if progress:
            progress(0.0, "Скачиваем ComfyUI Manager", build_setup_progress_meta("manager", "prepare", 0, "Подготовка"))
        download_file(
            COMFYUI_MANAGER_ARCHIVE_URL,
            archive_path,
            progress_cb=(
                None
                if not progress
                else lambda downloaded, total, rate: progress(
                    0.15 + (0.60 * (downloaded / total if total else 0.0)),
                    "Скачиваем ComfyUI Manager",
                    build_setup_progress_meta(
                        "manager",
                        "download",
                        100 * (downloaded / total if total else 0.0),
                        f"{format_bytes(rate)}/s" + (f" • {format_bytes(downloaded)} / {format_bytes(total)}" if total else ""),
                    ),
                )
            ),
            status_cb=(
                None
                if not progress
                else lambda text: progress(
                    0.15,
                    "Скачиваем ComfyUI Manager",
                    build_setup_progress_meta("manager", "download", None, text),
                )
            ),
        )
        extract_dir = temp_path / "manager"
        if progress:
            progress(0.78, "Распаковываем ComfyUI Manager", build_setup_progress_meta("manager", "extract", None, "Распаковка"))
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(extract_dir)
        extracted_root = next((item for item in extract_dir.iterdir() if item.is_dir()), None)
        if not extracted_root:
            raise RuntimeError("Не удалось распаковать ComfyUI Manager.")
        shutil.copytree(extracted_root, manager_dir)
    if not manager_is_installed(root):
        raise RuntimeError("ComfyUI Manager установлен, но проверка не нашла файлы manager.")
    invalidate_setup_status_cache()
    if progress:
        progress(1.0, "ComfyUI Manager установлен", build_setup_progress_meta("manager", "done", 100, "Manager проверен"))
    return "Manager установлен и проверен."


def pending_starter_model_specs(root: Path | None, specs: list[dict] | tuple[dict, ...] | None = None) -> list[dict]:
    specs_to_check = list(specs or STARTER_MODEL_SPECS)
    if not root:
        return specs_to_check
    pending: list[dict] = []
    for spec in specs_to_check:
        if not starter_model_exists(root, spec):
            pending.append(spec)
    return pending


def pending_node_specs(root: Path | None, specs: list[dict] | tuple[dict, ...] | None = None) -> list[dict]:
    specs_to_check = list(specs or [])
    if not specs_to_check:
        workflow_specs, _, _ = workflow_required_node_specs()
        specs_to_check = list(workflow_specs or REQUIRED_NODE_SPECS)
    if not root:
        return specs_to_check
    pending: list[dict] = []
    for spec in specs_to_check:
        if not node_is_installed(root, spec):
            pending.append(spec)
    return pending


def install_starter_models(root: Path, progress=None, specs: list[dict] | tuple[dict, ...] | None = None) -> list[str]:
    results: list[str] = []
    pending_specs = pending_starter_model_specs(root, specs)
    if not pending_specs:
        if progress:
            progress(1.0, "Все файлы для Comfy уже на месте", "")
        return results
    total_count = len(pending_specs)
    config = load_config()
    for index, spec in enumerate(pending_specs, start=1):
        row_key = f"model:{spec['title']}"
        target_dir = root.joinpath(*spec["relative_dir"])
        target_dir.mkdir(parents=True, exist_ok=True)
        target_filename = str(spec.get("filename", "")).strip()
        target_path = target_dir / target_filename
        if target_path.exists() and target_path.stat().st_size > 0:
            results.append(f"{spec['title']} уже был на месте")
            if progress:
                progress(index / total_count, f"{spec['title']} уже на месте", build_setup_progress_meta(row_key, "done", 100, "Файл уже установлен"))
            continue
        link_status = cached_direct_download_status(spec, force=True)
        if not link_status.get("available", False):
            message = str(link_status.get("message", "") or f"Сейчас скачать нельзя: {spec['title']} недоступен.")
            results.append(message)
            if progress:
                progress(index / total_count, message, build_setup_progress_meta(row_key, "error", 0, "Ссылка недоступна"))
            continue
        request_variants = starter_model_requests(spec, config)
        if progress:
            progress((index - 1) / total_count, f"Скачиваем {spec['title']}", build_setup_progress_meta(row_key, "prepare", 0, "Подготовка"))
        last_error = ""
        download_ok = False
        for attempt_index, (download_url, request_headers, resolved_filename) in enumerate(request_variants, start=1):
            if resolved_filename and target_filename != resolved_filename:
                target_filename = resolved_filename
                target_path = target_dir / target_filename
            try:
                download_file(
                    download_url,
                    target_path,
                    progress_cb=(
                        None
                        if not progress
                        else lambda downloaded, total, rate, current_index=index: progress(
                            ((current_index - 1) + (downloaded / total if total else 0.0)) / total_count,
                            f"Скачиваем {spec['title']}",
                            build_setup_progress_meta(
                                row_key,
                                "download",
                                100 * (downloaded / total if total else 0.0),
                                f"{format_bytes(rate)}/s" + (f" • {format_bytes(downloaded)} / {format_bytes(total)}" if total else ""),
                            ),
                        )
                    ),
                    status_cb=(
                        None
                        if not progress
                        else lambda text, spec_title=spec["title"], current_index=index: progress(
                            ((current_index - 1) + 0.01) / total_count,
                            f"Скачиваем {spec_title}",
                            build_setup_progress_meta(row_key, "download", None, text),
                        )
                    ),
                    request_headers=request_headers,
                )
                download_ok = True
                break
            except RuntimeError as exc:
                last_error = str(exc)
                try:
                    target_path.unlink()
                except FileNotFoundError:
                    pass
                if attempt_index < len(request_variants) and civitai_auth_required_message() in last_error:
                    if progress:
                        progress(
                            ((index - 1) + 0.02) / total_count,
                            f"Пробуем другой Civitai key для {spec['title']}",
                            build_setup_progress_meta(row_key, "download", None, "Civitai key не подошел, переключаемся"),
                        )
                    continue
                continue
        if not download_ok:
            message = f"{spec['title']}: {last_error or 'не удалось скачать файл.'}"
            results.append(message)
            if progress:
                progress(index / total_count, message, build_setup_progress_meta(row_key, "error", 0, last_error or "Ошибка загрузки"))
            continue
        if progress:
            progress(
                ((index - 1) + 0.98) / total_count,
                f"Проверяем {spec['title']}",
                build_setup_progress_meta(row_key, "verify", 98, "Проверяем файл на диске"),
            )
        if not starter_model_exists(root, spec):
            message = f"{spec['title']} скачан, но проверка не нашла файл в нужной папке."
            results.append(message)
            if progress:
                progress(index / total_count, message, build_setup_progress_meta(row_key, "error", 0, "Проверка файла не прошла"))
            continue
        invalidate_setup_status_cache()
        results.append(f"{spec['title']} скачан и проверен")
        if progress:
            progress(index / total_count, f"{spec['title']} готов", build_setup_progress_meta(row_key, "done", 100, "Файл проверен"))
    return results


def install_missing_nodes(root: Path, progress=None, specs: list[dict] | tuple[dict, ...] | None = None) -> list[str]:
    custom_nodes_dir = root / "ComfyUI" / "custom_nodes"
    custom_nodes_dir.mkdir(parents=True, exist_ok=True)
    results: list[str] = []
    specs_to_install = pending_node_specs(root, specs)
    if not specs_to_install:
        if progress:
            progress(1.0, "Все nodes уже установлены", "")
        return results
    total_count = len(specs_to_install)
    for index, spec in enumerate(specs_to_install, start=1):
        row_key = f"node:{spec['folder']}"
        target_dir = node_install_path(root, spec)
        if node_is_installed(root, spec):
            results.append(f"{spec['title']} уже установлен")
            if progress:
                progress(index / total_count, f"{spec['title']} уже установлен", build_setup_progress_meta(row_key, "done", 100, "Нода уже установлена"))
            continue
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        if progress:
            progress((index - 1) / total_count, f"Клонируем {spec['title']}", build_setup_progress_meta(row_key, "clone", None, "git clone"))
        try:
            run_hidden_process_with_retries(
                ["git", "clone", "--depth", "1", spec["repo"], str(target_dir)],
                custom_nodes_dir,
                f"Не удалось установить {spec['title']}",
                status_cb=(
                    None
                    if not progress
                    else lambda text, spec_title=spec["title"]: progress(
                        (index - 1 + 0.1) / total_count,
                        f"Клонируем {spec_title}",
                        build_setup_progress_meta(row_key, "clone", None, text),
                    )
                ),
                cleanup_before_retry=lambda target=target_dir: shutil.rmtree(target, ignore_errors=True),
            )
        except RuntimeError as exc:
            message = str(exc)
            results.append(message)
            if progress:
                progress(index / total_count, message, build_setup_progress_meta(row_key, "error", 0, "GitHub недоступен или clone не удался"))
            continue
        requirements_path = target_dir / "requirements.txt"
        if requirements_path.exists():
            python_bin = root / "python_embeded" / "python.exe"
            if progress:
                progress((index - 1 + 0.7) / total_count, f"Ставим зависимости для {spec['title']}", build_setup_progress_meta(row_key, "deps", None, "pip install"))
            try:
                run_hidden_process_with_retries(
                    [str(python_bin), "-s", "-m", "pip", "install", "-r", str(requirements_path)],
                    target_dir,
                    f"Не удалось поставить зависимости {spec['title']}",
                    status_cb=(
                        None
                        if not progress
                        else lambda text, spec_title=spec["title"]: progress(
                            (index - 1 + 0.75) / total_count,
                            f"Ставим зависимости для {spec_title}",
                            build_setup_progress_meta(row_key, "deps", None, text),
                        )
                    ),
                )
            except RuntimeError as exc:
                message = str(exc)
                results.append(message)
                if progress:
                    progress(index / total_count, message, build_setup_progress_meta(row_key, "error", 0, "pip install не удался"))
                continue
        if progress:
            progress(
                (index - 1 + 0.96) / total_count,
                f"Проверяем {spec['title']}",
                build_setup_progress_meta(row_key, "verify", 98, "Проверяем папку ноды"),
            )
        if not node_is_installed(root, spec):
            message = f"{spec['title']} установлен, но проверка не нашла папку ноды."
            results.append(message)
            if progress:
                progress(index / total_count, message, build_setup_progress_meta(row_key, "error", 0, "Проверка папки не прошла"))
            continue
        invalidate_setup_status_cache()
        results.append(f"{spec['title']} установлен")
        if progress:
            progress(index / total_count, f"{spec['title']} установлен", build_setup_progress_meta(row_key, "done", 100, "Нода проверена"))
    return results


def install_comfy_setup(install_parent: Path | None = None, progress=None) -> str:
    root = current_comfy_root()
    messages: list[str] = []
    status = cached_comfy_setup_status(force=True)
    update_available = bool(root and status.get("comfy_update_available"))
    manager_missing = not status.get("manager_ready")
    missing_model_specs = pending_starter_model_specs(root)
    missing_node_specs_list = pending_node_specs(root)
    total_units = (
        (1 if (not root or update_available) else 0)
        + (1 if manager_missing else 0)
        + len(missing_model_specs)
        + len(missing_node_specs_list)
    )
    total_units = max(total_units, 1)
    completed_units = 0.0
    last_percent = 0

    def emit(step_units: float, step_fraction: float, detail: str, meta: str = "") -> None:
        if not progress:
            return
        nonlocal last_percent
        clamped_fraction = max(0.0, min(1.0, float(step_fraction)))
        raw_percent = ((completed_units + (clamped_fraction * max(step_units, 0.0))) / total_units) * 100.0
        percent = int(max(0, min(100, round(raw_percent))))
        percent = max(last_percent, percent)
        last_percent = percent
        progress(detail, percent, meta)

    if not root:
        if install_parent is None:
            raise RuntimeError("Выбери папку, куда скачать portable ComfyUI.")
        root = install_comfyui_portable(install_parent, progress=lambda fraction, detail, meta="": emit(1, fraction, detail, meta))
        messages.append(f"ComfyUI готов в {root}")
        completed_units += 1
        missing_model_specs = pending_starter_model_specs(root, missing_model_specs)
        missing_node_specs_list = pending_node_specs(root, missing_node_specs_list)
    elif update_available:
        root = install_comfyui_portable(root.parent, progress=lambda fraction, detail, meta="": emit(1, fraction, detail, meta), force_update=True)
        messages.append("ComfyUI обновлена до latest-сборки.")
        completed_units += 1
        missing_model_specs = pending_starter_model_specs(root, missing_model_specs)
        missing_node_specs_list = pending_node_specs(root, missing_node_specs_list)
    else:
        config = load_config()
        config["comfy_root"] = str(root)
        save_config(config)
        messages.append("Portable ComfyUI уже найден.")

    if manager_missing:
        messages.append(install_comfyui_manager(root, progress=lambda fraction, detail, meta="": emit(1, fraction, detail, meta)))
        completed_units += 1
    else:
        messages.append("Manager уже установлен.")

    if missing_model_specs:
        model_units = len(missing_model_specs)
        messages.extend(
            install_starter_models(
                root,
                progress=lambda fraction, detail, meta="": emit(model_units, fraction, detail, meta),
                specs=missing_model_specs,
            )
        )
        completed_units += model_units
    else:
        messages.append("Стартовые модели уже на месте.")

    if missing_node_specs_list:
        node_units = len(missing_node_specs_list)
        messages.extend(
            install_missing_nodes(
                root,
                progress=lambda fraction, detail, meta="": emit(node_units, fraction, detail, meta),
                specs=missing_node_specs_list,
            )
        )
        completed_units += node_units
    else:
        messages.append("Ноды workflow уже на месте.")

    assert_setup_verified(include_nodes=True)
    return " ".join(messages)


def install_comfy_core_setup(install_parent: Path | None = None, progress=None) -> str:
    root = current_comfy_root()
    messages: list[str] = []
    status = cached_comfy_setup_status(force=True)
    update_available = bool(root and status.get("comfy_update_available"))
    manager_missing = not status.get("manager_ready")
    missing_model_specs = pending_starter_model_specs(root)
    total_units = (1 if (not root or update_available) else 0) + (1 if manager_missing else 0) + len(missing_model_specs)
    total_units = max(total_units, 1)
    completed_units = 0.0
    last_percent = 0

    def emit(step_units: float, step_fraction: float, detail: str, meta: str = "") -> None:
        if not progress:
            return
        nonlocal last_percent
        clamped_fraction = max(0.0, min(1.0, float(step_fraction)))
        raw_percent = ((completed_units + (clamped_fraction * max(step_units, 0.0))) / total_units) * 100.0
        percent = int(max(0, min(100, round(raw_percent))))
        percent = max(last_percent, percent)
        last_percent = percent
        progress(detail, percent, meta)

    if not root:
        if install_parent is None:
            raise RuntimeError("Выбери папку, куда скачать portable ComfyUI.")
        root = install_comfyui_portable(install_parent, progress=lambda fraction, detail, meta="": emit(1, fraction, detail, meta))
        messages.append(f"ComfyUI готов в {root}")
        completed_units += 1
        missing_model_specs = pending_starter_model_specs(root, missing_model_specs)
    elif update_available:
        root = install_comfyui_portable(root.parent, progress=lambda fraction, detail, meta="": emit(1, fraction, detail, meta), force_update=True)
        messages.append("ComfyUI обновлена до latest-сборки.")
        completed_units += 1
        missing_model_specs = pending_starter_model_specs(root, missing_model_specs)
    else:
        config = load_config()
        config["comfy_root"] = str(root)
        save_config(config)
        messages.append("Portable ComfyUI уже найден.")

    if manager_missing:
        messages.append(install_comfyui_manager(root, progress=lambda fraction, detail, meta="": emit(1, fraction, detail, meta)))
        completed_units += 1
    else:
        messages.append("Manager уже установлен.")

    if missing_model_specs:
        model_units = len(missing_model_specs)
        messages.extend(
            install_starter_models(
                root,
                progress=lambda fraction, detail, meta="": emit(model_units, fraction, detail, meta),
                specs=missing_model_specs,
            )
        )
        completed_units += model_units
    else:
        messages.append("Все файлы для Comfy уже на месте.")

    assert_setup_verified(include_nodes=False)
    return " ".join(messages)


def install_nodes_setup(progress=None) -> str:
    root = current_comfy_root()
    if not root:
        raise RuntimeError("Сначала установи полный Comfy setup.")
    missing_node_specs_list = pending_node_specs(root)
    if not missing_node_specs_list:
        invalidate_setup_status_cache()
        return "Все nodes уже установлены."
    node_units = len(missing_node_specs_list)
    messages = install_missing_nodes(
        root,
        progress=lambda fraction, detail, meta="": progress(detail, int(max(0, min(100, round(fraction * 100)))), meta) if progress else None,
        specs=missing_node_specs_list,
    )
    assert_nodes_verified(root)
    invalidate_setup_status_cache()
    return " ".join(messages)


def set_desired_running(enabled: bool) -> None:
    state = load_state()
    state["desired_running"] = enabled
    if not enabled:
        state["tunnel_retry_after"] = 0.0
        state["tunnel_retry_delay"] = DEFAULT_TUNNEL_RETRY_DELAY
        state["last_tunnel_error"] = ""
    save_state(state)


def reset_tunnel_retry(error_text: str = "") -> None:
    state = load_state()
    changed = (
        float(state.get("tunnel_retry_after", 0.0) or 0.0) != 0.0
        or float(state.get("tunnel_retry_delay", DEFAULT_TUNNEL_RETRY_DELAY) or DEFAULT_TUNNEL_RETRY_DELAY) != DEFAULT_TUNNEL_RETRY_DELAY
        or state.get("last_tunnel_error", "") != error_text
    )
    if not changed:
        return
    state["tunnel_retry_after"] = 0.0
    state["tunnel_retry_delay"] = DEFAULT_TUNNEL_RETRY_DELAY
    state["last_tunnel_error"] = error_text
    save_state(state)


def reset_friend_retry(link_id: str) -> None:
    update_friend_link_entry(
        link_id,
        lambda current, _state: current.update(
            {
                "retry_after": 0.0,
                "retry_delay": DEFAULT_TUNNEL_RETRY_DELAY,
                "error": "",
            }
        ),
    )


def schedule_friend_retry(link_id: str, error_text: str = "") -> None:
    now = time.time()

    def mutate(current, _state):
        delay = float(current.get("retry_delay", DEFAULT_TUNNEL_RETRY_DELAY) or DEFAULT_TUNNEL_RETRY_DELAY)
        delay = min(max(delay, DEFAULT_TUNNEL_RETRY_DELAY), MAX_TUNNEL_RETRY_DELAY)
        current["retry_after"] = now + delay
        current["retry_delay"] = min(delay * 1.7, MAX_TUNNEL_RETRY_DELAY)
        current["status"] = "error"
        current["paused"] = False
        current["pid"] = None
        if error_text:
            current["error"] = error_text

    update_friend_link_entry(link_id, mutate)


def schedule_tunnel_retry(error_text: str = "") -> None:
    state = load_state()
    delay = float(state.get("tunnel_retry_delay", DEFAULT_TUNNEL_RETRY_DELAY) or DEFAULT_TUNNEL_RETRY_DELAY)
    delay = min(max(delay, DEFAULT_TUNNEL_RETRY_DELAY), MAX_TUNNEL_RETRY_DELAY)
    state["tunnel_retry_after"] = time.time() + delay
    state["tunnel_retry_delay"] = min(delay * 1.7, MAX_TUNNEL_RETRY_DELAY)
    if error_text:
        state["last_tunnel_error"] = error_text
    state["tunnel_pid"] = None
    save_state(state)


def mark_tunnel_retry_pending(delay: float = DEFAULT_TUNNEL_RETRY_DELAY) -> None:
    state = load_state()
    state["tunnel_retry_after"] = time.time() + max(delay, DEFAULT_TUNNEL_RETRY_DELAY)
    state["tunnel_retry_delay"] = min(max(float(state.get("tunnel_retry_delay", DEFAULT_TUNNEL_RETRY_DELAY) or DEFAULT_TUNNEL_RETRY_DELAY), DEFAULT_TUNNEL_RETRY_DELAY), MAX_TUNNEL_RETRY_DELAY)
    save_state(state)


def port_is_open(port: int) -> bool:
    sock = socket.socket()
    sock.settimeout(PORT_CHECK_TIMEOUT)
    try:
        return sock.connect_ex(("127.0.0.1", int(port))) == 0
    finally:
        sock.close()


def comfy_http_ready(port: int, timeout_seconds: float = COMFY_HTTP_TIMEOUT) -> bool:
    headers = {"User-Agent": DOWNLOAD_USER_AGENT}
    probes = (
        (f"http://127.0.0.1:{int(port)}/system_stats", ("devices", "system")),
        (f"http://127.0.0.1:{int(port)}/", ("comfy", "<!doctype html", "<html")),
    )
    for url, markers in probes:
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                status = int(getattr(response, "status", 200) or 200)
                body = response.read(512).decode("utf-8", errors="ignore").lower()
                if 200 <= status < 500 and any(marker in body for marker in markers):
                    return True
        except Exception:
            continue
    return False


def wait_for_comfy_ready(port: int, timeout_seconds: float = 90.0, interval_seconds: float = 0.6) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if port_is_open(port) and comfy_http_ready(port):
            return True
        time.sleep(interval_seconds)
    return port_is_open(port) and comfy_http_ready(port)


def internet_is_available(force: bool = False) -> bool:
    now = time.monotonic()
    cache = INTERNET_STATUS_CACHE
    if not force and now - float(cache["at"]) < INTERNET_CACHE_TTL:
        return bool(cache["ok"])

    ok = False
    for host, port in (("1.1.1.1", 53), ("8.8.8.8", 53)):
        try:
            with socket.create_connection((host, port), timeout=INTERNET_CHECK_TIMEOUT):
                ok = True
                break
        except OSError:
            continue
    cache["ok"] = ok
    cache["at"] = now
    return ok


def clear_logs(*paths: Path) -> None:
    for path in paths:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def ensure_layout(config: dict | None = None) -> Path:
    root = resolve_comfy_root(config)
    if not (root / "python_embeded" / "python.exe").exists():
        raise RuntimeError("Не найден python_embeded\\python.exe в выбранной папке ComfyUI.")
    if not (root / "ComfyUI" / "main.py").exists():
        raise RuntimeError("Не найден ComfyUI\\main.py в выбранной папке ComfyUI.")
    return root


def find_matching_processes(kind: str) -> list[psutil.Process]:
    matches: list[psutil.Process] = []
    config = load_config() if kind in {"tunnel", "friend_tunnel"} else None
    state = load_state() if kind in {"tunnel", "friend_tunnel"} else None
    main_subdomain = normalize_subdomain((config or {}).get("subdomain", ""))
    friend_subdomains = friend_subdomains_from_state(state)
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = " ".join(proc.info.get("cmdline") or []).lower()
            name = (proc.info.get("name") or "").lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        tunnel_subdomain = extract_tunnel_subdomain(cmdline)

        if kind == "comfy":
            if "comfyui\\main.py" in cmdline or "comfyui/main.py" in cmdline:
                matches.append(proc)
            elif name.startswith("python") and "fp16_accumulation" in cmdline and "main.py" in cmdline:
                matches.append(proc)
        elif kind == "tunnel":
            is_localtunnel = "localtunnel" in cmdline or (name.startswith("node") and "loca.lt" in cmdline)
            if is_localtunnel and main_subdomain and tunnel_subdomain == main_subdomain:
                matches.append(proc)
        elif kind == "friend_tunnel":
            is_localtunnel = "localtunnel" in cmdline or (name.startswith("node") and "loca.lt" in cmdline)
            if is_localtunnel and tunnel_subdomain and (tunnel_subdomain in friend_subdomains or FRIEND_LINK_PATTERN.fullmatch(tunnel_subdomain)):
                matches.append(proc)
    return matches


def pid_is_running(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        proc = psutil.Process(pid)
        return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def cached_process_scan(kind: str, force: bool = False) -> list[int]:
    now = time.monotonic()
    cache = PROCESS_SCAN_CACHE[kind]
    if force or now - cache["at"] > PROCESS_SCAN_TTL:
        cache["pids"] = [proc.pid for proc in find_matching_processes(kind)]
        cache["at"] = now
    return cache["pids"]


def kill_process_tree(proc: psutil.Process) -> None:
    try:
        children = proc.children(recursive=True)
        for child in children:
            try:
                child.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        proc.kill()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass


def any_comfy_process(state: dict | None = None) -> bool:
    state = state or load_state()
    return pid_is_running(state.get("comfy_pid")) or bool(cached_process_scan("comfy"))


def any_tunnel_process(state: dict | None = None) -> bool:
    state = state or load_state()
    return pid_is_running(state.get("tunnel_pid")) or bool(cached_process_scan("tunnel"))


def any_friend_tunnel_process(state: dict | None = None) -> bool:
    state = state or load_state()
    for entry in state.get("friend_links", []):
        if pid_is_running(entry.get("pid")):
            return True
    return bool(cached_process_scan("friend_tunnel"))


def friend_process_map() -> dict[str, psutil.Process]:
    return cached_friend_process_map()


def cached_friend_process_map(force: bool = False) -> dict[str, psutil.Process]:
    now = time.monotonic()
    cache = FRIEND_PROCESS_MAP_CACHE
    if force or now - float(cache["at"]) > PROCESS_SCAN_TTL:
        mapping: dict[str, psutil.Process] = {}
        for proc in find_matching_processes("friend_tunnel"):
            try:
                cmdline = " ".join(proc.cmdline()).lower()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            subdomain = extract_tunnel_subdomain(cmdline)
            if subdomain:
                mapping[subdomain] = proc
        cache["mapping"] = mapping
        cache["at"] = now
    return dict(cache["mapping"])


def read_text_tail(path: Path, max_bytes: int = 16384) -> str:
    if not path.exists():
        return ""
    try:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - max_bytes), os.SEEK_SET)
            data = handle.read()
        encodings = ["utf-8", locale.getpreferredencoding(False), "cp866", "cp1251"]
        seen: set[str] = set()
        for encoding in encodings:
            encoding = str(encoding or "").strip().lower()
            if not encoding or encoding in seen:
                continue
            seen.add(encoding)
            try:
                return data.decode(encoding)
            except Exception:
                continue
        return data.decode("utf-8", errors="replace")
    except Exception:
        encodings = ["utf-8", locale.getpreferredencoding(False), "cp866", "cp1251"]
        seen: set[str] = set()
        for encoding in encodings:
            encoding = str(encoding or "").strip().lower()
            if not encoding or encoding in seen:
                continue
            seen.add(encoding)
            try:
                return path.read_text(encoding=encoding)
            except Exception:
                continue
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return ""


def detect_tunnel_url(path: Path, preferred_subdomain: str = "") -> str:
    if not path.exists():
        return ""
    content = read_text_tail(path, max_bytes=16384)
    matches = re.findall(r"https://[a-z0-9-]+\.loca\.lt", content)
    if not matches:
        return ""
    preferred = sanitize_subdomain(preferred_subdomain)
    if preferred:
        for url in reversed(matches):
            if extract_public_subdomain(url) == preferred:
                return url
        return ""
    return matches[-1]


def public_comfy_url_ready(url: str, timeout_seconds: float = 1.2) -> bool:
    clean_url = str(url or "").strip().rstrip("/")
    if not clean_url:
        return False
    headers = {"User-Agent": DOWNLOAD_USER_AGENT}
    probes = (
        (f"{clean_url}/system_stats", ("devices", "system", "vram_total")),
        (f"{clean_url}/queue", ("queue_running", "queue_pending", "running", "pending")),
        (clean_url, ("comfy", "<!doctype html", "<html")),
    )
    for probe_url, markers in probes:
        try:
            request = urllib.request.Request(probe_url, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                status = int(getattr(response, "status", response.getcode()) or 200)
                body = response.read(768).decode("utf-8", errors="ignore").lower()
                if 200 <= status < 500 and any(marker in body for marker in markers):
                    return True
        except Exception:
            continue
    return False


def cached_public_tunnel_ready(url: str, force: bool = False) -> bool:
    clean_url = str(url or "").strip().rstrip("/")
    if not clean_url:
        return False
    cache_items = PUBLIC_TUNNEL_STATUS_CACHE["items"]
    now = time.monotonic()
    cached = cache_items.get(clean_url)
    if cached and not force and (now - float(cached.get("at", 0.0))) < PUBLIC_TUNNEL_CACHE_TTL:
        return bool(cached.get("ready", False))
    ready = public_comfy_url_ready(clean_url)
    cache_items[clean_url] = {"ready": ready, "at": now}
    return ready


def wait_for_public_tunnel_url(log_path: Path, subdomain: str, timeout_seconds: float = 20.0, interval_seconds: float = 0.35) -> str:
    deadline = time.time() + timeout_seconds
    last_detected = ""
    while time.time() < deadline:
        detected = detect_tunnel_url(log_path, subdomain)
        if detected:
            last_detected = detected
            if cached_public_tunnel_ready(detected, force=True):
                return detected
        time.sleep(interval_seconds)
    return last_detected if last_detected and cached_public_tunnel_ready(last_detected, force=True) else ""


def tail_text(path: Path, lines: int = 4) -> str:
    if not path.exists():
        return ""
    return "\n".join(read_text_tail(path, max_bytes=8192).splitlines()[-lines:])


def combined_comfy_log_text(max_bytes: int = 65536) -> str:
    parts: list[str] = []
    stdout_text = read_text_tail(COMFY_OUT, max_bytes=max_bytes // 2)
    stderr_text = read_text_tail(COMFY_ERR, max_bytes=max_bytes // 2)
    if stdout_text.strip():
        parts.append("[stdout]\n" + stdout_text.strip())
    if stderr_text.strip():
        parts.append("[stderr]\n" + stderr_text.strip())
    return "\n\n".join(parts).strip()


def summarize_error_tail(path: Path) -> str:
    text = tail_text(path, lines=12)
    if not text:
        return ""
    lowered_text = text.lower()
    if "npx.cmd" in lowered_text or "npx " in lowered_text:
        return "Не удалось запустить localtunnel через npx."
    def normalize_error_line(value: str) -> str:
        cleaned = str(value or "").replace("\u00ad", "").replace("\xa0", " ")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    lines = [normalize_error_line(line) for line in text.splitlines() if normalize_error_line(line)]
    if not lines:
        return ""
    for line in reversed(lines):
        lower = line.lower()
        if "is not recognized as an internal or external command" in lower or "не является внутренней или внешней" in lower:
            return "Не удалось запустить localtunnel через npx."
        if "error:" in lower or "refused" in lower or "firewall" in lower or "failed" in lower:
            return line
    return lines[-1]


def npx_executable() -> str:
    return shutil.which("npx.cmd") or shutil.which("npx") or "npx"


def npx_launch_prefix() -> list[str]:
    npx_path = Path(npx_executable())
    node_path = shutil.which("node.exe") or shutil.which("node")
    if os.name == "nt" and node_path:
        candidates = [
            npx_path.parent / "node_modules" / "npm" / "bin" / "npx-cli.js",
            npx_path.parent / "node_modules" / "npm" / "bin" / "npx",
        ]
        for candidate in candidates:
            if candidate.exists():
                return [str(Path(node_path).resolve()), str(candidate.resolve())]
    return [str(npx_path)]


def wait_for_port(port: int, timeout_seconds: float = 90.0, interval_seconds: float = 0.6) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if port_is_open(port):
            return True
        time.sleep(interval_seconds)
    return port_is_open(port)


def launch_localtunnel(comfy_root: Path, port: int, subdomain: str, out_path: Path, err_path: Path) -> subprocess.Popen:
    clear_logs(out_path, err_path)
    out = open(out_path, "w", encoding="utf-8")
    err = open(err_path, "w", encoding="utf-8")
    command = [
        *npx_launch_prefix(),
        "--yes",
        "localtunnel",
        "--port",
        str(int(port)),
        "--local-host",
        "127.0.0.1",
        "--subdomain",
        normalize_subdomain(subdomain),
    ]
    try:
        proc = subprocess.Popen(
            command,
            cwd=str(comfy_root),
            stdout=out,
            stderr=err,
            shell=False,
            **hidden_subprocess_kwargs(new_process_group=True),
        )
    finally:
        out.close()
        err.close()
    return proc


def find_friend_link_entry(state: dict, link_id: str) -> dict | None:
    for entry in state.get("friend_links", []):
        if entry.get("id") == link_id:
            return entry
    return None


def reserve_friend_link(custom_subdomain: str | None = None) -> dict:
    def mutate(state: dict):
        friend_links = list(state.get("friend_links", []))
        if len(friend_links) >= MAX_FRIEND_LINKS:
            raise RuntimeError("Доступно максимум 5 friend links.")
        existing = {entry.get("subdomain", "") for entry in friend_links}
        main_subdomain = normalize_subdomain(load_config().get("subdomain", ""))
        requested_subdomain = sanitize_subdomain(custom_subdomain or "")
        if custom_subdomain is not None:
            if not is_valid_subdomain(requested_subdomain):
                raise RuntimeError("Введи нормальный subdomain: 3-63 символа, буквы, цифры или дефис.")
            if requested_subdomain == main_subdomain:
                raise RuntimeError("Этот subdomain уже используется основной ссылкой.")
            if requested_subdomain in existing:
                raise RuntimeError("Такая friend-ссылка уже существует.")
            subdomain = requested_subdomain
        else:
            subdomain = generate_unique_friend_subdomain(existing | {main_subdomain})
        entry = {
            "id": secrets.token_hex(4),
            "subdomain": subdomain,
            "url": friend_url_for_subdomain(subdomain),
            "pid": None,
            "status": "starting",
            "error": "",
            "created_at": time.time(),
            "retry_after": 0.0,
            "retry_delay": DEFAULT_TUNNEL_RETRY_DELAY,
        }
        friend_links.append(entry)
        state["friend_links"] = friend_links
        return dict(entry)

    _, entry = update_state(mutate)
    return entry


def start_comfy_if_needed() -> str:
    with COMFY_LAUNCH_LOCK:
        config = load_config()
        comfy_root = ensure_layout(config)
        state = load_state()
        port_open = port_is_open(config["port"])
        comfy_ready = comfy_http_ready(config["port"]) if port_open else False
        comfy_proc = any_comfy_process(state)
        if comfy_ready or comfy_proc:
            return "ComfyUI уже активен."
        if port_open and not comfy_ready:
            raise RuntimeError(f"Порт {config['port']} уже занят другим приложением.")

        clear_logs(COMFY_OUT, COMFY_ERR)
        out = open(COMFY_OUT, "w", encoding="utf-8")
        err = open(COMFY_ERR, "w", encoding="utf-8")
        try:
            proc = subprocess.Popen(
                comfy_launch_command(comfy_root, config),
                cwd=str(comfy_root),
                stdout=out,
                stderr=err,
                shell=False,
                **hidden_subprocess_kwargs(new_process_group=True),
            )
        finally:
            out.close()
            err.close()
        state["comfy_pid"] = proc.pid
        save_state(state)
        return "ComfyUI запускается."


def start_tunnel_if_needed() -> str:
    with MAIN_TUNNEL_LOCK:
        config = load_config()
        comfy_root = ensure_layout(config)
        state = load_state()
        if not wait_for_comfy_ready(config["port"], timeout_seconds=30.0, interval_seconds=0.5):
            raise RuntimeError("ComfyUI еще не отвечает по HTTP и не готов для туннеля.")
        if any_tunnel_process(state):
            return "Туннель уже активен."

        proc = launch_localtunnel(comfy_root, config["port"], config["subdomain"], TUNNEL_OUT, TUNNEL_ERR)
        state["tunnel_pid"] = proc.pid
        state["last_tunnel_error"] = ""
        save_state(state)
        reset_tunnel_retry()
        ready_url = wait_for_public_tunnel_url(TUNNEL_OUT, config["subdomain"], timeout_seconds=22.0)
        if ready_url:
            state = load_state()
            state["last_url"] = ready_url
            state["last_tunnel_error"] = ""
            save_state(state)
            return "Туннель готов."
        if not pid_is_running(proc.pid):
            error_text = summarize_error_tail(TUNNEL_ERR) or "Туннель не успел подняться."
            schedule_tunnel_retry(error_text)
            raise RuntimeError(error_text)
        return "Туннель запускается."


def start_friend_tunnel(link_id: str) -> str:
    config = load_config()
    comfy_root = ensure_layout(config)
    state = load_state()
    entry = find_friend_link_entry(state, link_id)
    if not entry:
        raise RuntimeError("Friend link уже удален.")
    if pid_is_running(entry.get("pid")):
        return f"Friend link {entry['subdomain']} уже активен."

    if not port_is_open(config["port"]):
        start_comfy_if_needed()
        if not wait_for_comfy_ready(config["port"]):
            raise RuntimeError("ComfyUI не ответил вовремя.")

    out_path, err_path = friend_log_paths(entry["id"])
    proc = launch_localtunnel(comfy_root, config["port"], entry["subdomain"], out_path, err_path)
    updated_entry = update_friend_link_entry(
        link_id,
        lambda current, _state: current.update(
            {
                "pid": proc.pid,
                "status": "starting",
                "paused": False,
                "error": "",
                "retry_after": 0.0,
                "created_at": time.time(),
            }
        ),
    )
    if not updated_entry:
        try:
            kill_process_tree(psutil.Process(proc.pid))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return "Friend link был удален."
    cached_process_scan("friend_tunnel", force=True)
    cached_friend_process_map(force=True)

    deadline = time.time() + 18
    while time.time() < deadline:
        current_entry = update_friend_link_entry(link_id, lambda current, _state: current.update({"pid": proc.pid}))
        if not current_entry:
            return "Friend link был удален."
        if not pid_is_running(proc.pid):
            error_text = summarize_error_tail(err_path) or "Friend link не успел подняться."
            update_friend_link_entry(
                link_id,
                lambda current, _state: current.update(
                    {
                        "status": "error",
                        "paused": False,
                        "error": error_text,
                        "pid": None,
                    }
                ),
            )
            schedule_friend_retry(link_id, error_text)
            raise RuntimeError(error_text)
        detected_url = wait_for_public_tunnel_url(out_path, entry["subdomain"], timeout_seconds=0.35, interval_seconds=0.05)
        if detected_url:
            ready_entry = update_friend_link_entry(
                link_id,
                lambda current, _state: current.update(
                    {
                        "url": detected_url,
                        "status": "active",
                        "paused": False,
                        "error": "",
                        "pid": proc.pid,
                        "retry_after": 0.0,
                        "retry_delay": DEFAULT_TUNNEL_RETRY_DELAY,
                    }
                ),
            )
            if not ready_entry:
                return "Friend link был удален."
            return f"Friend link {ready_entry['subdomain']} готов."
        time.sleep(0.35)

    current_entry = update_friend_link_entry(
        link_id,
        lambda current, _state: current.update(
            {
                "pid": proc.pid if pid_is_running(proc.pid) else None,
                "status": "active" if pid_is_running(proc.pid) else "error",
                "paused": False,
                "error": "" if pid_is_running(proc.pid) else (summarize_error_tail(err_path) or "Friend link не ответил вовремя."),
                "retry_after": 0.0 if pid_is_running(proc.pid) else current.get("retry_after", 0.0),
            }
        ),
    )
    if current_entry:
        current_entry["pid"] = proc.pid if pid_is_running(proc.pid) else None
    if current_entry and not pid_is_running(proc.pid):
        schedule_friend_retry(link_id, current_entry.get("error", "Friend link не ответил вовремя."))
    return f"Friend link {entry['subdomain']} создан."


def start_all() -> str:
    config = load_config()
    ensure_layout(config)
    set_desired_running(True)
    update_state(
        lambda state: [
            entry.update(
                {
                    "paused": False,
                    "status": "starting" if entry.get("status") == "paused" else entry.get("status", "starting"),
                    "retry_after": 0.0,
                    "retry_delay": DEFAULT_TUNNEL_RETRY_DELAY,
                    "error": "",
                }
            )
            for entry in state.get("friend_links", [])
        ]
    )
    reset_tunnel_retry()
    comfy_msg = start_comfy_if_needed()
    if not wait_for_comfy_ready(config["port"]):
        raise RuntimeError("ComfyUI не ответил вовремя.")
    tunnel_msg = start_tunnel_if_needed()
    return f"{comfy_msg} {tunnel_msg}"


def stop_friend_tunnel(link_id: str) -> str:
    state = load_state()
    candidates: dict[int, psutil.Process] = {}
    entry = find_friend_link_entry(state, link_id)
    if not entry:
        return "Friend link уже удален."
    target_subdomain = entry.get("subdomain", "")

    if entry.get("pid"):
        try:
            candidates[entry["pid"]] = psutil.Process(entry["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    for subdomain, proc in friend_process_map().items():
        if subdomain == target_subdomain:
            candidates[proc.pid] = proc

    for proc in list(candidates.values()):
        kill_process_tree(proc)

    def mutate(current_state: dict):
        current_state["friend_links"] = [item for item in current_state.get("friend_links", []) if item.get("id") != link_id]

    update_state(mutate)
    cached_process_scan("friend_tunnel", force=True)
    cached_friend_process_map(force=True)
    for path in friend_log_paths(link_id):
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    return f"Friend link {target_subdomain} удален."


def stop_all() -> str:
    state = load_state()
    candidates: dict[int, psutil.Process] = {}
    friend_ids = [entry.get("id") for entry in state.get("friend_links", []) if entry.get("id")]

    for kind in ("friend_tunnel", "tunnel", "comfy"):
        for proc in find_matching_processes(kind):
            candidates[proc.pid] = proc

    for key in ("tunnel_pid", "comfy_pid"):
        pid = state.get(key)
        if pid:
            try:
                candidates[pid] = psutil.Process(pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    for proc in list(candidates.values()):
        kill_process_tree(proc)

    state["comfy_pid"] = None
    state["tunnel_pid"] = None
    state["last_url"] = ""
    for entry in state.get("friend_links", []):
        entry["pid"] = None
        entry["status"] = "paused"
        entry["paused"] = True
        entry["error"] = ""
        entry["retry_after"] = 0.0
        entry["retry_delay"] = DEFAULT_TUNNEL_RETRY_DELAY
    state["desired_running"] = False
    state["tunnel_retry_after"] = 0.0
    state["tunnel_retry_delay"] = DEFAULT_TUNNEL_RETRY_DELAY
    state["last_tunnel_error"] = ""
    save_state(state)
    cached_process_scan("comfy", force=True)
    cached_process_scan("tunnel", force=True)
    cached_process_scan("friend_tunnel", force=True)
    cached_friend_process_map(force=True)
    for link_id in friend_ids:
        for path in friend_log_paths(link_id):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
    return "Все процессы остановлены."


def stop_main_tunnel_only() -> None:
    state = load_state()
    candidates: dict[int, psutil.Process] = {}

    for proc in find_matching_processes("tunnel"):
        candidates[proc.pid] = proc

    pid = state.get("tunnel_pid")
    if pid:
        try:
            candidates[pid] = psutil.Process(pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    for proc in list(candidates.values()):
        kill_process_tree(proc)

    state["tunnel_pid"] = None
    state["last_url"] = ""
    state["last_tunnel_error"] = ""
    state["tunnel_retry_after"] = 0.0
    state["tunnel_retry_delay"] = DEFAULT_TUNNEL_RETRY_DELAY
    save_state(state)
    cached_process_scan("tunnel", force=True)
    reset_tunnel_retry()


def regenerate_main_tunnel() -> str:
    config = load_config()
    ensure_layout(config)
    set_desired_running(True)
    stop_main_tunnel_only()
    if not port_is_open(config["port"]):
        start_comfy_if_needed()
        if not wait_for_comfy_ready(config["port"]):
            raise RuntimeError("ComfyUI не ответил вовремя.")
    start_tunnel_if_needed()
    return f"Ссылка обновляется для {normalize_subdomain(config['subdomain'])}."


def runtime_snapshot(include_logs: bool = False) -> dict:
    config = load_config()
    state = load_state()
    comfy_root = normalize_root_path(config.get("comfy_root", ""))
    internet_ok = internet_is_available()
    comfy_active = any_comfy_process(state)
    if not comfy_active and port_is_open(config["port"]):
        comfy_active = comfy_http_ready(config["port"])
    tunnel_active = any_tunnel_process(state)
    main_subdomain = normalize_subdomain(config.get("subdomain", ""))
    detected_main_url = detect_tunnel_url(TUNNEL_OUT, main_subdomain) if tunnel_active else ""
    main_url_ready = bool(detected_main_url and cached_public_tunnel_ready(detected_main_url))
    url = detected_main_url if (tunnel_active and main_url_ready) else ""
    if tunnel_active:
        reset_tunnel_retry()
    if url and tunnel_active:
        if state.get("last_url") != url:
            state["last_url"] = url
            save_state(state)
    else:
        url = ""
    if not comfy_active:
        comfy_active = port_is_open(config["port"])
    retry_after = float(state.get("tunnel_retry_after", 0.0) or 0.0)
    retry_in = max(0, int(retry_after - time.time()))
    tunnel_error = state.get("last_tunnel_error", "")
    if not tunnel_error and not tunnel_active:
        tunnel_error = summarize_error_tail(TUNNEL_ERR)
    if tunnel_active and detected_main_url and not main_url_ready:
        tunnel_error = tunnel_error or "Ссылка прогревается. Ждем, пока Comfy начнет отвечать через туннель."

    friend_processes = friend_process_map()
    state_changed = False
    friend_links: list[dict] = []
    aggregated_friend_logs: list[str] = []
    friend_running = False
    friend_active_count = 0

    for entry in state.get("friend_links", []):
        out_path, err_path = friend_log_paths(entry["id"])
        running_proc = friend_processes.get(entry["subdomain"])
        running_pid = running_proc.pid if running_proc else None
        if not running_pid and pid_is_running(entry.get("pid")):
            running_pid = entry.get("pid")
        detected_url = detect_tunnel_url(out_path, entry["subdomain"])
        public_ready = bool(detected_url and cached_public_tunnel_ready(detected_url))
        error_text = summarize_error_tail(err_path)
        status = entry.get("status", "starting")
        paused = bool(entry.get("paused", False))
        now = time.time()
        retry_after = float(entry.get("retry_after", 0.0) or 0.0)
        retry_delay = float(entry.get("retry_delay", DEFAULT_TUNNEL_RETRY_DELAY) or DEFAULT_TUNNEL_RETRY_DELAY)
        retry_in = max(0, int(retry_after - now))

        created_age = now - float(entry.get("created_at", now) or now)
        if running_pid:
            status = "active" if public_ready else "starting"
            paused = False
            friend_running = True
            if status == "active":
                friend_active_count += 1
            if retry_after != 0.0 or retry_delay != DEFAULT_TUNNEL_RETRY_DELAY:
                retry_after = 0.0
                retry_delay = DEFAULT_TUNNEL_RETRY_DELAY
                state_changed = True
        elif paused:
            status = "paused"
            error_text = ""
            retry_after = 0.0
            retry_delay = DEFAULT_TUNNEL_RETRY_DELAY
        elif status == "starting" and now - float(entry.get("created_at", now)) < 4 and not error_text:
            status = "starting"
            friend_running = True
        elif error_text:
            status = "error"
            if retry_after <= now:
                delay = min(max(retry_delay, DEFAULT_TUNNEL_RETRY_DELAY), MAX_TUNNEL_RETRY_DELAY)
                retry_after = now + delay
                retry_delay = min(delay * 1.7, MAX_TUNNEL_RETRY_DELAY)
                state_changed = True
        elif status == "active":
            status = "error"
            error_text = error_text or "Friend link остановлен."
            if retry_after <= now:
                delay = min(max(retry_delay, DEFAULT_TUNNEL_RETRY_DELAY), MAX_TUNNEL_RETRY_DELAY)
                retry_after = now + delay
                retry_delay = min(delay * 1.7, MAX_TUNNEL_RETRY_DELAY)
                state_changed = True

        normalized_url = detected_url or entry.get("url") or friend_url_for_subdomain(entry.get("subdomain", ""))
        if entry.get("pid") != running_pid:
            entry["pid"] = running_pid
            state_changed = True
        if entry.get("url") != normalized_url:
            entry["url"] = normalized_url
            state_changed = True
        if entry.get("status") != status:
            entry["status"] = status
            state_changed = True
        if bool(entry.get("paused", False)) != paused:
            entry["paused"] = paused
            state_changed = True
        if entry.get("error", "") != error_text:
            entry["error"] = error_text
            state_changed = True
        if float(entry.get("retry_after", 0.0) or 0.0) != retry_after:
            entry["retry_after"] = retry_after
            state_changed = True
        if float(entry.get("retry_delay", DEFAULT_TUNNEL_RETRY_DELAY) or DEFAULT_TUNNEL_RETRY_DELAY) != retry_delay:
            entry["retry_delay"] = retry_delay
            state_changed = True

        retry_in = max(0, int(retry_after - time.time()))
        friend_entry = dict(entry)
        friend_entry["retry_in"] = retry_in if status == "error" else 0
        friend_links.append(friend_entry)
        if include_logs:
            log_line = tail_text(err_path) or tail_text(out_path)
            if log_line:
                aggregated_friend_logs.append(f"{entry['subdomain']}: {log_line.splitlines()[-1]}")

    if state_changed:
        merge_friend_link_entries(friend_links)
        state["friend_links"] = normalize_friend_links(friend_links)

    return {
        "config": config,
        "state": state,
        "url": url,
        "comfy_root": comfy_root,
        "internet_ok": internet_ok,
        "comfy_active": comfy_active,
        "tunnel_active": tunnel_active,
        "friend_active": friend_running,
        "friend_links": friend_links,
        "friend_active_count": friend_active_count,
        "friend_count": len(friend_links),
        "desired_running": bool(state.get("desired_running")),
        "retry_in": retry_in,
        "tunnel_error": tunnel_error,
        "logs": {
            "comfy": (tail_text(COMFY_ERR) or tail_text(COMFY_OUT)) if include_logs else "",
            "comfy_full": combined_comfy_log_text() if include_logs else "",
            "tunnel": (tail_text(TUNNEL_ERR) or tail_text(TUNNEL_OUT)) if include_logs else "",
            "friend": "\n".join(aggregated_friend_logs),
        },
    }


def migrate_legacy_storage() -> None:
    legacy_pairs = [
        (BASE_DIR / "ComfyPortal.config.json", CONFIG_PATH),
        (BASE_DIR / "ComfyPortal.state.json", STATE_PATH),
    ]
    for source, target in legacy_pairs:
        if target.exists() or not source.exists():
            continue
        try:
            shutil.copy2(source, target)
        except Exception:
            continue


@dataclass
class Theme:
    app_bg: str
    panel_bg: str
    panel_alt: str
    surface: str
    surface_alt: str
    border: str
    text: str
    muted: str
    green: str
    red: str
    blue: str
    blue_hover: str
    soft_btn: str
    soft_btn_hover: str
    shadow: QColor


THEMES = {
    "light": Theme(
        app_bg="#f3f7fd",
        panel_bg="#ffffff",
        panel_alt="#eef3fb",
        surface="#ffffff",
        surface_alt="#f4f7fc",
        border="#dce6f2",
        text="#111827",
        muted="#6b7280",
        green="#16a34a",
        red="#ef4444",
        blue="#2563ff",
        blue_hover="#1f4fd1",
        soft_btn="#eaf0fb",
        soft_btn_hover="#dce7fa",
        shadow=QColor(36, 56, 92, 28),
    ),
    "dark": Theme(
        app_bg="#050608",
        panel_bg="#0c0e12",
        panel_alt="#13161b",
        surface="#0f1115",
        surface_alt="#171b21",
        border="#222831",
        text="#f5f7fa",
        muted="#8d97a6",
        green="#22c55e",
        red="#fb5a67",
        blue="#3b82f6",
        blue_hover="#2563eb",
        soft_btn="#161a20",
        soft_btn_hover="#1f252d",
        shadow=QColor(0, 0, 0, 120),
    ),
}


class UiBridge(QObject):
    finished = Signal(str, bool, str)
    progress = Signal(str, int, str, str)
    snapshot_ready = Signal(object)
    snapshot_failed = Signal(str)
    setup_status_ready = Signal(object)
    update_ready = Signal(object)
    update_failed = Signal(str)


class CardFrame(QFrame):
    def __init__(self, object_name: str):
        super().__init__()
        self.setObjectName(object_name)
        self.setFrameShape(QFrame.NoFrame)
        self.shadow = None


class StatusCard(CardFrame):
    def __init__(self, title: str):
        super().__init__("statusCard")
        self._current_value = None
        self._current_color = None
        self._current_detail = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("statusTitle")
        self.value_label = QLabel("...")
        self.value_label.setObjectName("statusValue")
        self.detail_label = QLabel("")
        self.detail_label.setObjectName("statusDetail")
        self.detail_label.setWordWrap(True)

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.detail_label)
        layout.addStretch(1)

    def set_status(self, value: str, color: str, detail: str) -> None:
        if self._current_value != value:
            self.value_label.setText(value)
            self._current_value = value
        if self._current_color != color:
            self.value_label.setStyleSheet(f"color: {color};")
            self._current_color = color
        if self._current_detail != detail:
            self.detail_label.setText(detail)
            self._current_detail = detail


def build_icon_pixmap(icon_name: str, color: str, size: int = 26) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    pen = QPen(QColor(color))
    pen.setWidthF(max(1.7, size * 0.09))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    if icon_name == "copy":
        back_rect = QRectF(size * 0.18, size * 0.30, size * 0.42, size * 0.46)
        front_rect = QRectF(size * 0.36, size * 0.16, size * 0.42, size * 0.46)
        radius = size * 0.11
        painter.drawRoundedRect(back_rect, radius, radius)
        painter.drawRoundedRect(front_rect, radius, radius)
    elif icon_name == "settings":
        center = QPoint(size // 2, size // 2)
        outer_r = size * 0.34
        inner_r = size * 0.14
        spoke_start = size * 0.26
        spoke_end = size * 0.40
        for angle in range(0, 360, 45):
            painter.save()
            painter.translate(center)
            painter.rotate(angle)
            painter.drawLine(QPoint(0, int(-spoke_start)), QPoint(0, int(-spoke_end)))
            painter.restore()
        painter.drawEllipse(QRectF(center.x() - outer_r, center.y() - outer_r, outer_r * 2, outer_r * 2))
        painter.drawEllipse(QRectF(center.x() - inner_r, center.y() - inner_r, inner_r * 2, inner_r * 2))
    elif icon_name == "close":
        margin = int(size * 0.28)
        painter.drawLine(QPoint(margin, margin), QPoint(size - margin, size - margin))
        painter.drawLine(QPoint(size - margin, margin), QPoint(margin, size - margin))
    elif icon_name == "install":
        tray_y = size * 0.68
        tray_left = size * 0.20
        tray_right = size * 0.80
        painter.drawLine(QPoint(int(tray_left), int(tray_y)), QPoint(int(tray_right), int(tray_y)))
        painter.drawLine(QPoint(int(tray_left), int(tray_y)), QPoint(int(tray_left), int(size * 0.50)))
        painter.drawLine(QPoint(int(tray_right), int(tray_y)), QPoint(int(tray_right), int(size * 0.50)))
        painter.drawLine(QPoint(size // 2, int(size * 0.20)), QPoint(size // 2, int(size * 0.54)))
        painter.drawLine(QPoint(size // 2, int(size * 0.56)), QPoint(int(size * 0.34), int(size * 0.40)))
        painter.drawLine(QPoint(size // 2, int(size * 0.56)), QPoint(int(size * 0.66), int(size * 0.40)))
    elif icon_name == "logs":
        left = int(size * 0.24)
        right = int(size * 0.76)
        for index, y in enumerate((0.30, 0.50, 0.70)):
            painter.drawLine(QPoint(left, int(size * y)), QPoint(right, int(size * y)))
            bullet_x = int(size * 0.14)
            painter.drawLine(QPoint(bullet_x, int(size * y)), QPoint(int(size * 0.18), int(size * y)))
    elif icon_name == "refresh":
        rect = QRectF(size * 0.20, size * 0.20, size * 0.60, size * 0.60)
        painter.drawArc(rect, 48 * 16, 114 * 16)
        painter.drawArc(rect, 228 * 16, 114 * 16)
        painter.setBrush(QColor(color))
        top_head = QPolygon(
            [
                QPoint(int(size * 0.82), int(size * 0.28)),
                QPoint(int(size * 0.69), int(size * 0.29)),
                QPoint(int(size * 0.75), int(size * 0.40)),
            ]
        )
        bottom_head = QPolygon(
            [
                QPoint(int(size * 0.18), int(size * 0.72)),
                QPoint(int(size * 0.31), int(size * 0.71)),
                QPoint(int(size * 0.25), int(size * 0.60)),
            ]
        )
        painter.drawPolygon(top_head)
        painter.drawPolygon(bottom_head)
        painter.setBrush(Qt.NoBrush)
    elif icon_name == "back":
        mid_y = size // 2
        left = int(size * 0.24)
        right = int(size * 0.76)
        painter.drawLine(QPoint(left, mid_y), QPoint(right, mid_y))
        painter.drawLine(QPoint(left, mid_y), QPoint(int(size * 0.44), int(size * 0.28)))
        painter.drawLine(QPoint(left, mid_y), QPoint(int(size * 0.44), int(size * 0.72)))
    elif icon_name == "telegram":
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(color))
        plane = QPolygon(
            [
                QPoint(int(size * 0.16), int(size * 0.50)),
                QPoint(int(size * 0.82), int(size * 0.22)),
                QPoint(int(size * 0.68), int(size * 0.80)),
                QPoint(int(size * 0.50), int(size * 0.64)),
                QPoint(int(size * 0.40), int(size * 0.75)),
                QPoint(int(size * 0.45), int(size * 0.58)),
                QPoint(int(size * 0.30), int(size * 0.51)),
            ]
        )
        painter.drawPolygon(plane)

    painter.end()
    return QIcon(pixmap)


class ToggleSwitch(QPushButton):
    def __init__(self) -> None:
        super().__init__()
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(48, 24)
        self.setFocusPolicy(Qt.NoFocus)
        self.theme = THEMES["light"]

    def apply_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        track_rect = QRectF(1, 1, self.width() - 2, self.height() - 2)
        if not self.isEnabled():
            painter.setOpacity(0.45)
        track_color = QColor(self.theme.green if self.isChecked() else self.theme.red)
        painter.setPen(QPen(QColor(self.theme.border), 1))
        painter.setBrush(track_color)
        painter.drawRoundedRect(track_rect, track_rect.height() / 2, track_rect.height() / 2)

        knob_size = self.height() - 6
        knob_x = self.width() - knob_size - 3 if self.isChecked() else 3
        knob_rect = QRectF(knob_x, 3, knob_size, knob_size)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(knob_rect)
        painter.end()


class ToggleRow(CardFrame):
    def __init__(self, title: str, hint: str):
        super().__init__("toggleRow")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(10)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("drawerLabel")
        self.title_label.setToolTip(hint)
        self.title_label.setMinimumHeight(24)

        self.toggle = ToggleSwitch()
        self.toggle.setToolTip(hint)

        layout.addWidget(self.title_label, 1)
        layout.addWidget(self.toggle, 0, Qt.AlignRight | Qt.AlignVCenter)

    def set_checked(self, checked: bool) -> None:
        self.toggle.setChecked(checked)

    def is_checked(self) -> bool:
        return self.toggle.isChecked()

    def apply_theme(self, theme: Theme) -> None:
        self.toggle.apply_theme(theme)


class FriendLinkRow(CardFrame):
    copy_requested = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, link_id: str):
        super().__init__("friendLinkCard")
        self.link_id = link_id
        self.current_status = ""
        self.theme = THEMES["light"]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(10)
        self.subdomain_label = QLabel("")
        self.subdomain_label.setObjectName("friendRowTitle")
        self.status_label = QLabel("Starting")
        self.status_label.setObjectName("friendRowStatus")
        self.loader = QProgressBar()
        self.loader.setObjectName("friendMiniLoader")
        self.loader.setTextVisible(False)
        self.loader.setFixedSize(82, 6)
        self.loader.setRange(0, 0)
        self.loader.setVisible(True)
        header.addWidget(self.subdomain_label, 1)
        header.addWidget(self.status_label, 0, Qt.AlignRight)
        header.addWidget(self.loader, 0, Qt.AlignRight | Qt.AlignVCenter)

        link_row = QHBoxLayout()
        link_row.setSpacing(10)
        self.link_field = QLineEdit()
        self.link_field.setObjectName("friendLinkField")
        self.link_field.setReadOnly(True)
        self.link_field.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.link_field.setFixedHeight(46)
        self.link_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.copy_button = QPushButton("")
        self.copy_button.setObjectName("copyButton")
        self.copy_button.setFixedSize(42, 42)
        self.copy_button.setIconSize(QSize(18, 18))
        self.copy_button.setCursor(Qt.PointingHandCursor)
        self.copy_button.clicked.connect(lambda: self.copy_requested.emit(self.link_id))

        self.delete_button = QPushButton("")
        self.delete_button.setObjectName("friendMiniDeleteButton")
        self.delete_button.setFixedSize(42, 42)
        self.delete_button.setIconSize(QSize(14, 14))
        self.delete_button.setCursor(Qt.PointingHandCursor)
        self.delete_button.clicked.connect(lambda: self.delete_requested.emit(self.link_id))

        link_row.addWidget(self.link_field, 1)
        link_row.addWidget(self.copy_button, 0, Qt.AlignRight)
        link_row.addWidget(self.delete_button, 0, Qt.AlignRight)

        self.detail_label = QLabel("")
        self.detail_label.setObjectName("friendRowDetail")
        self.detail_label.setWordWrap(True)

        layout.addLayout(header)
        layout.addLayout(link_row)
        layout.addWidget(self.detail_label)

    def apply_theme(self, theme: Theme, copy_icon: QIcon, delete_icon: QIcon) -> None:
        self.theme = theme
        self.copy_button.setIcon(copy_icon)
        self.delete_button.setIcon(delete_icon)
        if self.current_status:
            self.set_status(self.current_status, self.detail_label.text())

    def set_status(self, status: str, detail: str) -> None:
        self.current_status = status
        status_text = status
        if status == "active":
            color = self.theme.green
            visible_loader = False
            status_text = "Готово"
        elif status == "paused":
            color = self.theme.text
            visible_loader = False
            status_text = "Пауза"
        elif status == "error":
            color = self.theme.red
            visible_loader = False
            status_text = "Ошибка"
        else:
            color = self.theme.blue
            visible_loader = True
            status_text = "Загрузка"
        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 800;")
        self.loader.setVisible(visible_loader)
        self.detail_label.setText(detail)

    def set_data(self, entry: dict) -> None:
        self.subdomain_label.setText(entry["subdomain"])
        self.link_field.setText(entry["url"])
        self.link_field.setCursorPosition(0)
        self.copy_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        if entry["status"] == "active":
            detail = "Ссылка уже готова. Можно сразу отправлять другу."
        elif entry["status"] == "paused":
            detail = "Ссылка сохранена. Нажми Start, чтобы поднять ее снова."
        elif entry["status"] == "error":
            retry_in = int(entry.get("retry_in", 0) or 0)
            if retry_in > 0:
                detail = f"{entry.get('error') or 'Friend link упал.'} Повтор через {retry_in}с."
            else:
                detail = entry.get("error") or "Не удалось поднять friend link."
        else:
            detail = "Поднимаем локальный туннель и ждем, пока ссылка станет живой."
        self.set_status(entry["status"], detail)


class DrawerFrame(CardFrame):
    def __init__(self, object_name: str = "settingsDrawer"):
        super().__init__(object_name)


class DrawerBackdrop(QWidget):
    clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("drawerBackdrop")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._alpha = 0.0
        self.hide()

    def get_alpha(self) -> float:
        return self._alpha

    def set_alpha(self, value: float) -> None:
        clamped = max(0.0, min(255.0, float(value)))
        if abs(self._alpha - clamped) < 0.5:
            return
        self._alpha = clamped
        self.update()

    alpha = Property(float, get_alpha, set_alpha)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, int(round(self._alpha))))
        painter.end()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        self.clicked.emit()
        event.accept()


class FriendSubdomainDialog(QDialog):
    def __init__(self, theme: Theme, main_subdomain: str, existing_subdomains: set[str], parent: QWidget | None = None):
        super().__init__(parent)
        self.theme = theme
        self.main_subdomain = sanitize_subdomain(main_subdomain)
        self.existing_subdomains = {sanitize_subdomain(value) for value in existing_subdomains}
        self.result_subdomain = ""

        self.setModal(True)
        self.setWindowTitle("Своя friend-ссылка")
        self.setFixedWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        title = QLabel("Свой friend subdomain")
        title.setObjectName("dialogTitle")

        hint = QLabel("Введи subdomain для временной ссылки друга. Только буквы, цифры и дефис.")
        hint.setObjectName("dialogHint")
        hint.setWordWrap(True)

        self.input = QLineEdit()
        self.input.setObjectName("dialogInput")
        self.input.setPlaceholderText("myfriendlink")
        self.input.setMinimumHeight(44)
        self.input.returnPressed.connect(self.accept_subdomain)
        self.input.textEdited.connect(lambda *_args: self.error_label.setVisible(False))

        self.error_label = QLabel("")
        self.error_label.setObjectName("dialogError")
        self.error_label.setVisible(False)
        self.error_label.setWordWrap(True)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addStretch(1)

        cancel_button = QPushButton("Отмена")
        cancel_button.setObjectName("dialogSecondaryButton")
        cancel_button.setCursor(Qt.PointingHandCursor)
        cancel_button.clicked.connect(self.reject)

        add_button = QPushButton("Добавить")
        add_button.setObjectName("dialogPrimaryButton")
        add_button.setCursor(Qt.PointingHandCursor)
        add_button.clicked.connect(self.accept_subdomain)

        actions.addWidget(cancel_button)
        actions.addWidget(add_button)

        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(self.input)
        layout.addWidget(self.error_label)
        layout.addLayout(actions)

        self.apply_theme()
        QTimer.singleShot(0, self.input.setFocus)

    def apply_theme(self) -> None:
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {self.theme.panel_bg};
                color: {self.theme.text};
            }}
            QLabel#dialogTitle {{
                font-size: 22px;
                font-weight: 700;
                color: {self.theme.text};
            }}
            QLabel#dialogHint {{
                font-size: 13px;
                color: {self.theme.muted};
            }}
            QLabel#dialogError {{
                font-size: 12px;
                color: {self.theme.red};
                font-weight: 700;
            }}
            QLineEdit#dialogInput {{
                background: {self.theme.panel_alt};
                border: 1px solid {self.theme.border};
                border-radius: 16px;
                padding: 11px 14px;
                font-size: 14px;
                color: {self.theme.text};
                selection-background-color: {self.theme.blue};
            }}
            QPushButton#dialogSecondaryButton, QPushButton#dialogPrimaryButton {{
                min-width: 120px;
                min-height: 42px;
                border-radius: 16px;
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton#dialogSecondaryButton {{
                background: {self.theme.soft_btn};
                color: {self.theme.text};
                border: 1px solid {self.theme.border};
            }}
            QPushButton#dialogSecondaryButton:hover {{
                background: {self.theme.soft_btn_hover};
            }}
            QPushButton#dialogPrimaryButton {{
                background: {self.theme.blue};
                color: white;
                border: none;
            }}
            QPushButton#dialogPrimaryButton:hover {{
                background: {self.theme.blue_hover};
            }}
            """
        )

    def show_error(self, text: str) -> None:
        self.error_label.setText(text)
        self.error_label.setVisible(True)

    def accept_subdomain(self) -> None:
        subdomain = sanitize_subdomain(self.input.text())
        if not is_valid_subdomain(subdomain):
            self.show_error("Subdomain: 3-63 символа, только буквы, цифры и дефис.")
            return
        if subdomain == self.main_subdomain:
            self.show_error("Этот subdomain уже занят основной ссылкой.")
            return
        if subdomain in self.existing_subdomains:
            self.show_error("Такая friend-ссылка уже есть.")
            return
        self.result_subdomain = subdomain
        self.accept()


class ComfyGuideDialog(QDialog):
    install_requested = Signal()

    def __init__(self, theme: Theme, status: dict, parent: QWidget | None = None):
        super().__init__(parent)
        self.theme = theme
        self.status = status
        self.has_missing = comfy_setup_has_missing(status)
        self._progress_value = -1
        self._progress_detail = ""
        self._progress_meta = ""
        self.status_rows: dict[str, dict] = {}
        self.setModal(True)
        self.setWindowTitle("Comfy setup")
        self.resize(640, 760)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("guideScroll")
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.content = QWidget()
        self.scroll.setWidget(self.content)
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)

        title = QLabel("Comfy")
        title.setObjectName("guideTitle")
        subtitle = QLabel(
            "Здесь собрана помощь по portable ComfyUI, Manager, стартовым моделям и нодам для workflow. "
            "Показываем, что уже готово, а что еще нужно дотянуть."
        )
        subtitle.setObjectName("guideHint")
        subtitle.setWordWrap(True)

        status_card = QFrame()
        status_card.setObjectName("guideStatusCard")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(18, 18, 18, 18)
        status_layout.setSpacing(12)

        folder_title = QLabel("Portable folder")
        folder_title.setObjectName("guideSectionTitle")
        folder_value = QLabel(self.status.get("root") or "Папка пока не выбрана")
        folder_value.setObjectName("guidePathText")
        folder_value.setWordWrap(True)
        status_layout.addWidget(folder_title)
        status_layout.addWidget(folder_value)
        status_layout.addSpacing(8)
        status_layout.addWidget(self.build_status_row("source", "Источник сборки", self.status.get("source_kind") != "official_latest", self.status.get("source_label", "")))
        status_layout.addWidget(self.build_status_row("comfy", "Portable ComfyUI", bool(self.status.get("comfy_ready")), "Portable найден" if self.status.get("comfy_ready") else "Нужно скачать portable", installable=True))
        status_layout.addWidget(self.build_status_row("manager", "ComfyUI Manager", bool(self.status.get("manager_ready")), "Manager уже есть" if self.status.get("manager_ready") else "Будет поставлен в custom_nodes", installable=True))
        for model in self.status.get("models", []):
            status_layout.addWidget(
                self.build_status_row(
                    f"model:{model['title']}",
                    model["title"],
                    bool(model.get("ready")),
                    "Файл уже на месте" if model.get("ready") else "Будет скачан в нужную папку",
                    installable=True,
                )
            )

        nodes_card = QFrame()
        nodes_card.setObjectName("guideStatusCard")
        nodes_layout = QVBoxLayout(nodes_card)
        nodes_layout.setContentsMargins(18, 18, 18, 18)
        nodes_layout.setSpacing(12)

        nodes_title = QLabel("Nodes")
        nodes_title.setObjectName("guideSectionTitle")
        workflow_names = ", ".join(self.status.get("workflow_files", []))
        unresolved_names = ", ".join(self.status.get("unresolved_workflow_nodes", []))
        nodes_hint_text = "Ноды, которые нужны этому workflow и будут доставлены в custom_nodes."
        if workflow_names:
            nodes_hint_text += f" Workflow files: {workflow_names}."
        if unresolved_names:
            nodes_hint_text += f" Неизвестные ноды: {unresolved_names}."
        nodes_hint = QLabel(nodes_hint_text)
        nodes_hint.setObjectName("guideHint")
        nodes_hint.setWordWrap(True)
        nodes_layout.addWidget(nodes_title)
        nodes_layout.addWidget(nodes_hint)
        for node in self.status.get("nodes", []):
            nodes_layout.addWidget(
                self.build_status_row(
                    f"node:{node['folder']}",
                    node["title"],
                    bool(node.get("ready")),
                    "Нода уже на месте" if node.get("ready") else "Будет установлена через git clone в custom_nodes",
                    installable=True,
                )
            )

        what_card = QFrame()
        what_card.setObjectName("guideInfoCard")
        what_layout = QVBoxLayout(what_card)
        what_layout.setContentsMargins(18, 18, 18, 18)
        what_layout.setSpacing(10)

        what_title = QLabel("Что делает кнопка скачать")
        what_title.setObjectName("guideSectionTitle")
        what_text = QLabel(
            "1. Если portable ComfyUI не найден, приложение попросит папку и само скачает portable-архив.\n"
            "2. Только после этого поставит ComfyUI Manager в ComfyUI/custom_nodes/comfyui-manager.\n"
            "3. Затем доложит SAM, RealESRGAN x2, Control LoRA Canny и основную image-модель прямо в нужные model-папки.\n"
            "4. И уже после ComfyUI установит missing nodes для твоего workflow в custom_nodes."
        )
        what_text.setObjectName("guideSectionBody")
        what_text.setWordWrap(True)
        what_layout.addWidget(what_title)
        what_layout.addWidget(what_text)

        paths_card = QFrame()
        paths_card.setObjectName("guideInfoCard")
        paths_layout = QVBoxLayout(paths_card)
        paths_layout.setContentsMargins(18, 18, 18, 18)
        paths_layout.setSpacing(10)

        paths_title = QLabel("Куда лягут файлы")
        paths_title.setObjectName("guideSectionTitle")
        paths_text = QLabel(
            "SAM -> ComfyUI/models/sams\n"
            "RealESRGAN -> ComfyUI/models/upscale_models\n"
            "Control LoRA Canny -> ComfyUI/models/controlnet\n"
            "novaAnimeXL ilV180 -> ComfyUI/models/checkpoints"
        )
        paths_text.setObjectName("guideSectionBody")
        paths_text.setWordWrap(True)
        paths_layout.addWidget(paths_title)
        paths_layout.addWidget(paths_text)

        notes_card = QFrame()
        notes_card.setObjectName("guideInfoCard")
        notes_layout = QVBoxLayout(notes_card)
        notes_layout.setContentsMargins(18, 18, 18, 18)
        notes_layout.setSpacing(10)

        notes_title = QLabel("Важно")
        notes_title.setObjectName("guideSectionTitle")
        notes_text = QLabel(
            "Если ComfyUI у тебя уже стоит, загрузка не будет тащить portable заново и просто добьет Manager с моделями. "
            "Если portable пока нет, приложение предложит папку и разложит все по ней автоматически."
        )
        notes_text.setObjectName("guideSectionBody")
        notes_text.setWordWrap(True)
        notes_layout.addWidget(notes_title)
        notes_layout.addWidget(notes_text)

        source_card = QFrame()
        source_card.setObjectName("guideInfoCard")
        source_layout = QVBoxLayout(source_card)
        source_layout.setContentsMargins(18, 18, 18, 18)
        source_layout.setSpacing(10)

        source_title = QLabel("Как раздать именно твою версию")
        source_title.setObjectName("guideSectionTitle")
        source_text = QLabel(
            "Вариант 1: положи рядом с exe архив с точной сборкой и назови его ComfyPortal.custom_comfy.7z.\n"
            "Вариант 2: положи рядом файл ComfyPortal.custom_comfy_url.txt и вставь в него прямую ссылку на свой .7z архив.\n"
            "Тогда кнопка скачать поставит не latest, а именно твою фиксированную сборку."
        )
        source_text.setObjectName("guideSectionBody")
        source_text.setWordWrap(True)
        source_layout.addWidget(source_title)
        source_layout.addWidget(source_text)

        self.install_progress_card = QFrame()
        self.install_progress_card.setObjectName("guideProgressCard")
        install_progress_layout = QVBoxLayout(self.install_progress_card)
        install_progress_layout.setContentsMargins(18, 18, 18, 18)
        install_progress_layout.setSpacing(8)

        self.install_progress_title = QLabel("Установка")
        self.install_progress_title.setObjectName("guideSectionTitle")
        self.install_progress_percent = QLabel("0%")
        self.install_progress_percent.setObjectName("guideProgressPercent")
        self.install_progress_stage = QLabel("Готово")
        self.install_progress_stage.setObjectName("guideProgressStage")
        self.install_progress_detail = QLabel("Все готово. Если чего-то не хватает, тут появится статус установки.")
        self.install_progress_detail.setObjectName("guideSectionBody")
        self.install_progress_detail.setWordWrap(True)
        self.install_eta_label = QLabel("")
        self.install_eta_label.setObjectName("guideHint")
        self.install_eta_label.setWordWrap(True)
        self.install_progress = QProgressBar()
        self.install_progress.setObjectName("guideInstallProgress")
        self.install_progress.setTextVisible(False)
        self.install_progress.setFixedHeight(12)
        self.install_progress.setRange(0, 100)
        self.install_progress.setValue(0)
        progress_header = QHBoxLayout()
        progress_header.setSpacing(10)
        progress_header.addWidget(self.install_progress_title, 1)
        progress_header.addWidget(self.install_progress_stage, 0, Qt.AlignRight)
        progress_header.addWidget(self.install_progress_percent, 0, Qt.AlignRight)
        install_progress_layout.addLayout(progress_header)
        install_progress_layout.addWidget(self.install_progress_detail)
        install_progress_layout.addWidget(self.install_eta_label)
        install_progress_layout.addWidget(self.install_progress)
        self.install_progress_card.setVisible(False)

        content_layout.addWidget(title)
        content_layout.addWidget(subtitle)
        content_layout.addWidget(status_card)
        content_layout.addWidget(nodes_card)
        content_layout.addWidget(self.install_progress_card)
        content_layout.addWidget(what_card)
        content_layout.addWidget(paths_card)
        content_layout.addWidget(notes_card)
        content_layout.addWidget(source_card)
        content_layout.addStretch(1)

        actions = QHBoxLayout()
        actions.setContentsMargins(24, 24, 24, 24)
        actions.setSpacing(10)
        actions.addStretch(1)

        close_button = QPushButton("Close")
        close_button.setObjectName("dialogSecondaryButton")
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.clicked.connect(self.reject)

        install_button = QPushButton("Установить недостающее")
        install_button.setObjectName("dialogPrimaryButton")
        install_button.setCursor(Qt.PointingHandCursor)
        install_button.clicked.connect(self.request_install)
        self.install_button = install_button

        actions.addWidget(close_button)
        actions.addWidget(install_button)

        layout.addWidget(self.scroll, 1)
        layout.addLayout(actions)
        self.apply_theme()
        self.refresh_status(self.status)

    def build_status_row(self, key: str, title: str, ready: bool, detail: str, installable: bool = False) -> QWidget:
        row = QFrame()
        row.setObjectName("guideStatusRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)
        name_label = QLabel(title)
        name_label.setObjectName("guideStatusName")
        detail_label = QLabel(detail)
        detail_label.setObjectName("guideHint")
        detail_label.setWordWrap(True)
        row_progress = QProgressBar()
        row_progress.setObjectName("guideRowProgress")
        row_progress.setTextVisible(False)
        row_progress.setFixedHeight(8)
        row_progress.setRange(0, 100)
        row_progress.setValue(0)
        row_progress.setVisible(False)
        row_progress_meta = QLabel("")
        row_progress_meta.setObjectName("guideRowProgressMeta")
        row_progress_meta.setWordWrap(True)
        row_progress_meta.setVisible(False)
        text_layout.addWidget(name_label)
        text_layout.addWidget(detail_label)
        text_layout.addWidget(row_progress)
        text_layout.addWidget(row_progress_meta)

        badge = QPushButton("Установлено" if ready else "Установить")
        badge.setObjectName("guideStatusButton")
        badge.setCursor(Qt.PointingHandCursor if installable and not ready else Qt.ArrowCursor)
        badge.setEnabled(bool(installable and not ready))
        badge.setProperty("ready", ready)
        badge.setProperty("installable", installable)
        if installable:
            badge.clicked.connect(self.request_install)
        badge.style().unpolish(badge)
        badge.style().polish(badge)

        layout.addLayout(text_layout, 1)
        layout.addWidget(badge, 0, Qt.AlignRight | Qt.AlignVCenter)
        self.status_rows[key] = {
            "detail": detail_label,
            "badge": badge,
            "installable": installable,
            "progress": row_progress,
            "progress_meta": row_progress_meta,
        }
        return row

    def request_install(self) -> None:
        self.install_requested.emit()

    def clear_row_progress(self, keep_key: str = "") -> None:
        for key, row in self.status_rows.items():
            if keep_key and key == keep_key:
                continue
            progress_bar = row.get("progress")
            progress_meta = row.get("progress_meta")
            if isinstance(progress_bar, QProgressBar):
                progress_bar.setRange(0, 100)
                progress_bar.setValue(0)
                progress_bar.setVisible(False)
            if isinstance(progress_meta, QLabel):
                progress_meta.setText("")
                progress_meta.setVisible(False)

    def set_row_progress(self, key: str, percent: int | None, meta_text: str = "") -> None:
        if not key or key not in self.status_rows:
            self.clear_row_progress()
            return
        self.clear_row_progress(keep_key=key)
        row = self.status_rows[key]
        progress_bar = row.get("progress")
        progress_meta = row.get("progress_meta")
        if isinstance(progress_bar, QProgressBar):
            if percent is None:
                if not (progress_bar.minimum() == 0 and progress_bar.maximum() == 0):
                    progress_bar.setRange(0, 0)
            else:
                if not (progress_bar.minimum() == 0 and progress_bar.maximum() == 100):
                    progress_bar.setRange(0, 100)
                clamped = max(0, min(100, int(percent)))
                if progress_bar.value() != clamped:
                    progress_bar.setValue(clamped)
            if not progress_bar.isVisible():
                progress_bar.setVisible(True)
        if isinstance(progress_meta, QLabel):
            if progress_meta.text() != meta_text:
                progress_meta.setText(meta_text)
            should_show = bool(meta_text)
            if progress_meta.isVisible() != should_show:
                progress_meta.setVisible(should_show)

    def refresh_status(self, status: dict) -> None:
        self.status = status
        self.has_missing = comfy_setup_has_missing(status)
        comfy_ready = bool(self.status.get("comfy_ready"))
        manager_ready = bool(self.status.get("manager_ready"))
        updates: list[tuple[str, bool, str]] = [
            ("source", self.status.get("source_kind") != "official_latest", self.status.get("source_label", "")),
            ("comfy", comfy_ready, "Portable найден" if comfy_ready else "Нужно скачать portable"),
            ("manager", manager_ready, "Manager уже есть" if manager_ready else ("Сначала нужно установить Portable ComfyUI" if not comfy_ready else "Будет поставлен в custom_nodes")),
        ]
        for model in self.status.get("models", []):
            updates.append(
                (
                    f"model:{model['title']}",
                    bool(model.get("ready")),
                    "Файл уже на месте" if model.get("ready") else ("Сначала нужно установить Portable ComfyUI" if not comfy_ready else "Будет скачан в нужную папку"),
                )
            )
        for node in self.status.get("nodes", []):
            updates.append(
                (
                    f"node:{node['folder']}",
                    bool(node.get("ready")),
                    "Нода уже на месте" if node.get("ready") else ("Сначала нужно установить Portable ComfyUI" if not comfy_ready else "Будет установлена через git clone в custom_nodes"),
                )
            )
        for key, ready, detail in updates:
            row = self.status_rows.get(key)
            if not row:
                continue
            detail_label = row["detail"]
            badge = row["badge"]
            installable = bool(row["installable"])
            if detail_label.text() != detail:
                detail_label.setText(detail)
            text = "Установлено" if ready else "Установить"
            if badge.text() != text:
                badge.setText(text)
            badge.setProperty("ready", ready)
            can_install_now = bool(installable and not ready and (key == "comfy" or comfy_ready))
            badge.setEnabled(can_install_now)
            badge.setCursor(Qt.PointingHandCursor if can_install_now else Qt.ArrowCursor)
            badge.style().unpolish(badge)
            badge.style().polish(badge)
            if ready:
                progress_bar = row.get("progress")
                progress_meta = row.get("progress_meta")
                if isinstance(progress_bar, QProgressBar):
                    progress_bar.setVisible(False)
                if isinstance(progress_meta, QLabel):
                    progress_meta.setVisible(False)
                    progress_meta.setText("")
        self.install_button.setEnabled(self.has_missing)
        self.install_button.setText("Установить недостающее" if self.has_missing else "Все установлено")
        self.install_button.setCursor(Qt.PointingHandCursor if self.has_missing else Qt.ArrowCursor)
        self.apply_theme()

    def begin_install(self, eta_text: str) -> None:
        self.refresh_status(cached_comfy_setup_status(force=True))
        self.clear_row_progress()
        self.install_progress_card.setVisible(True)
        self.install_progress.setRange(0, 100)
        self.install_progress.setValue(0)
        self.install_progress_percent.setText("0%")
        self.install_progress_stage.setText("Подготовка")
        self.install_progress_detail.setText("Ставим portable ComfyUI, Manager, стартовые модели и missing nodes.")
        self.install_eta_label.setText(f"Примерное время: {eta_text}")
        self.install_button.setEnabled(False)
        self.install_button.setText("Установка...")
        self.install_button.setCursor(Qt.ArrowCursor)
        self._progress_value = 0
        self._progress_detail = self.install_progress_detail.text()
        self._progress_meta = self.install_eta_label.text()

    def update_install_progress(self, detail: str, percent: int, meta: str = "") -> None:
        self.install_progress_card.setVisible(True)
        payload = parse_setup_progress_meta(meta)
        row_key = str(payload.get("row_key", "") or "")
        row_meta_text = str(payload.get("meta_text", "") or "")
        raw_row_percent = payload.get("row_percent")
        row_percent = None if raw_row_percent is None else int(max(0, min(100, int(raw_row_percent))))
        stage = str(payload.get("stage", "") or "").strip().lower()
        if row_key and stage in {"done", "error"}:
            row = self.status_rows.get(row_key)
            if row:
                ready = stage == "done"
                progress_bar = row.get("progress")
                progress_meta = row.get("progress_meta")
                badge = row.get("badge")
                detail_label = row.get("detail")
                if isinstance(progress_bar, QProgressBar):
                    progress_bar.setVisible(False)
                    progress_bar.setValue(0)
                if isinstance(progress_meta, QLabel):
                    progress_meta.setVisible(False)
                    progress_meta.setText("")
                if isinstance(detail_label, QLabel):
                    detail_label.setText(row_meta_text or ("Проверено" if ready else "Ошибка установки"))
                if isinstance(badge, QPushButton):
                    badge.setText("Установлено" if ready else "Ошибка")
                    badge.setProperty("ready", ready)
                    badge.setEnabled(False)
                    badge.style().unpolish(badge)
                    badge.style().polish(badge)
        else:
            self.set_row_progress(row_key, row_percent, row_meta_text)
        clamped_percent = max(0, min(100, int(percent)))
        if self.install_progress.maximum() != 100:
            self.install_progress.setRange(0, 100)
        if self._progress_value != clamped_percent:
            self.install_progress.setValue(clamped_percent)
            self.install_progress_percent.setText(f"{clamped_percent}%")
            self._progress_value = clamped_percent
        if self._progress_detail != detail:
            self.install_progress_detail.setText(detail)
            self._progress_detail = detail
        stage_text = setup_stage_label(str(payload.get("stage", "") or ""), "Установка")
        if stage_text == "Установка" and meta:
            lower_meta = meta.lower()
            if "git" in lower_meta:
                stage_text = "Клонирование"
            elif "pip" in lower_meta:
                stage_text = "Зависимости"
            elif "/s" in meta or "•" in meta:
                stage_text = "Загрузка"
        if self.install_progress_stage.text() != stage_text:
            self.install_progress_stage.setText(stage_text)
        meta_label = row_meta_text or str(payload.get("meta_text", "") or meta)
        if meta_label and self._progress_meta != meta_label:
            self.install_eta_label.setText(meta_label)
            self._progress_meta = meta_label

    def finish_install(self, message: str, is_error: bool) -> None:
        self.install_progress_card.setVisible(True)
        self.clear_row_progress()
        self.install_progress.setRange(0, 100)
        self.install_progress.setValue(100 if not is_error else 0)
        self.install_progress_percent.setText("100%" if not is_error else "0%")
        self.install_progress_stage.setText("Готово" if not is_error else "Ошибка")
        self.install_progress_detail.setText(message)
        self.install_eta_label.setText("Готово." if not is_error else "Установка остановилась с ошибкой.")
        self._progress_value = 100 if not is_error else 0
        self._progress_detail = message
        self._progress_meta = self.install_eta_label.text()
        self.refresh_status(cached_comfy_setup_status(force=True))

    def apply_theme(self) -> None:
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {self.theme.panel_bg};
                color: {self.theme.text};
            }}
            QScrollArea#guideScroll {{
                background: transparent;
                border: none;
            }}
            QLabel#guideTitle {{
                font-size: 30px;
                font-weight: 800;
                color: {self.theme.text};
            }}
            QLabel#guideHint, QLabel#guideSectionBody {{
                font-size: 13px;
                color: {self.theme.muted};
            }}
            QLabel#guideSectionTitle {{
                font-size: 15px;
                font-weight: 800;
                color: {self.theme.text};
            }}
            QLabel#guideProgressPercent {{
                font-size: 20px;
                font-weight: 900;
                color: {self.theme.text};
                min-width: 52px;
            }}
            QLabel#guideProgressStage {{
                font-size: 11px;
                font-weight: 800;
                color: {self.theme.blue};
                background: {self.theme.surface};
                border: 1px solid {self.theme.border};
                border-radius: 999px;
                padding: 6px 10px;
                min-width: 84px;
            }}
            QLabel#guidePathText {{
                font-size: 13px;
                color: {self.theme.text};
                background: {self.theme.surface};
                border: 1px solid {self.theme.border};
                border-radius: 16px;
                padding: 12px 14px;
            }}
            QLabel#guideStatusName {{
                font-size: 14px;
                font-weight: 700;
                color: {self.theme.text};
            }}
            QLabel#guideRowProgressMeta {{
                font-size: 12px;
                color: {self.theme.muted};
            }}
            QPushButton#guideStatusButton {{
                min-width: 94px;
                padding: 8px 14px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: 800;
                text-align: center;
            }}
            QPushButton#guideStatusButton[ready="true"] {{
                background: rgba(34, 197, 94, 0.12);
                color: {self.theme.green};
                border: 1px solid rgba(34, 197, 94, 0.26);
            }}
            QPushButton#guideStatusButton[ready="false"] {{
                background: rgba(239, 68, 68, 0.12);
                color: {self.theme.red};
                border: 1px solid rgba(239, 68, 68, 0.24);
            }}
            QPushButton#guideStatusButton[ready="false"]:hover {{
                background: rgba(239, 68, 68, 0.20);
            }}
            QPushButton#guideStatusButton:disabled {{
                opacity: 1.0;
            }}
            QFrame#guideStatusCard, QFrame#guideInfoCard, QFrame#guideProgressCard {{
                background: {self.theme.panel_alt};
                border: 1px solid {self.theme.border};
                border-radius: 26px;
            }}
            QFrame#guideStatusRow {{
                background: {self.theme.surface};
                border: 1px solid {self.theme.border};
                border-radius: 22px;
            }}
            QProgressBar#guideRowProgress {{
                background: {self.theme.surface_alt if hasattr(self.theme, "surface_alt") else self.theme.panel_alt};
                border: 1px solid {self.theme.border};
                border-radius: 999px;
            }}
            QProgressBar#guideRowProgress::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.theme.blue},
                    stop:0.5 {self.theme.blue_hover},
                    stop:1 {self.theme.blue});
                border-radius: 999px;
            }}
            QProgressBar#guideInstallProgress {{
                background: {self.theme.surface};
                border: 1px solid {self.theme.border};
                border-radius: 999px;
            }}
            QProgressBar#guideInstallProgress::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.theme.blue},
                    stop:0.5 {self.theme.blue_hover},
                    stop:1 {self.theme.blue});
                border-radius: 999px;
            }}
            QPushButton#dialogSecondaryButton, QPushButton#dialogPrimaryButton {{
                min-width: 134px;
                min-height: 44px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 800;
            }}
            QPushButton#dialogSecondaryButton {{
                background: {self.theme.soft_btn};
                color: {self.theme.text};
                border: 1px solid {self.theme.border};
            }}
            QPushButton#dialogSecondaryButton:hover {{
                background: {self.theme.soft_btn_hover};
            }}
            QPushButton#dialogPrimaryButton {{
                background: {self.theme.red if self.has_missing else self.theme.blue};
                color: white;
                border: none;
            }}
            QPushButton#dialogPrimaryButton:hover {{
                background: {"#e54858" if self.has_missing else self.theme.blue_hover};
            }}
            """
        )

class SetupStatusRow(QFrame):
    def __init__(self, title: str, theme: Theme):
        super().__init__()
        self.theme = theme
        self.ready = False
        self.state_kind = "missing"
        self.setObjectName("setupStatusRow")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("setupRowTitle")
        self.detail_label = QLabel("")
        self.detail_label.setObjectName("setupRowDetail")
        self.detail_label.setWordWrap(True)
        self.progress = QProgressBar()
        self.progress.setObjectName("setupRowProgress")
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)
        self.progress.setRange(0, 100)
        self.progress.setVisible(False)
        self.progress_meta = QLabel("")
        self.progress_meta.setObjectName("setupRowMeta")
        self.progress_meta.setWordWrap(True)
        self.progress_meta.setVisible(False)
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.detail_label)
        text_layout.addWidget(self.progress)
        text_layout.addWidget(self.progress_meta)

        self.badge = QLabel("")
        self.badge.setObjectName("setupRowBadge")
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setMinimumWidth(110)
        self.badge.setFixedHeight(34)

        layout.addLayout(text_layout, 1)
        layout.addWidget(self.badge, 0, Qt.AlignRight | Qt.AlignVCenter)
        self.apply_theme(theme)

    def apply_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.setStyleSheet(
            f"""
            QFrame#setupStatusRow {{
                background: {theme.surface};
                border: 1px solid {theme.border};
                border-radius: 22px;
            }}
            QLabel#setupRowTitle {{
                color: {theme.text};
                font-size: 14px;
                font-weight: 800;
            }}
            QLabel#setupRowDetail, QLabel#setupRowMeta {{
                color: {theme.muted};
                font-size: 12px;
            }}
            QProgressBar#setupRowProgress {{
                background: {theme.surface_alt};
                border: 1px solid {theme.border};
                border-radius: 999px;
            }}
            QProgressBar#setupRowProgress::chunk {{
                background: {theme.blue};
                border-radius: 999px;
            }}
            """
        )
        self.update_badge(self.ready, self.state_kind)

    def update_badge(self, ready: bool, state_kind: str = "missing") -> None:
        self.ready = ready
        self.state_kind = state_kind
        if ready:
            text = "Установлено"
            bg = "rgba(34, 197, 94, 0.12)"
            fg = self.theme.green
            border = "rgba(34, 197, 94, 0.24)"
        elif state_kind == "unavailable":
            text = "Недоступно"
            bg = "rgba(250, 204, 21, 0.12)"
            fg = "#f59e0b"
            border = "rgba(250, 204, 21, 0.24)"
        else:
            text = "Не хватает"
            bg = "rgba(239, 68, 68, 0.12)"
            fg = self.theme.red
            border = "rgba(239, 68, 68, 0.24)"
        self.badge.setText(text)
        self.badge.setStyleSheet(
            f"background: {bg}; color: {fg}; border: 1px solid {border}; border-radius: 17px; font-size: 12px; font-weight: 800; padding: 0 12px;"
        )

    def set_state(self, ready: bool, detail: str, state_kind: str = "missing") -> None:
        self.detail_label.setText(detail)
        self.update_badge(ready, state_kind)
        if ready:
            self.clear_progress()

    def set_progress(self, percent: int | None, meta_text: str = "") -> None:
        if percent is None:
            self.progress.setRange(0, 0)
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(max(0, min(100, int(percent))))
        self.progress.setVisible(True)
        self.progress_meta.setText(meta_text)
        self.progress_meta.setVisible(bool(meta_text))

    def clear_progress(self) -> None:
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        self.progress_meta.clear()
        self.progress_meta.setVisible(False)


class SetupSectionCard(QFrame):
    action_requested = Signal(str)

    def __init__(self, key: str, title: str, action_text: str, theme: Theme):
        super().__init__()
        self.key = key
        self.theme = theme
        self.collapsed = True
        self.setObjectName("setupSectionCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(10)
        self.toggle_button = QPushButton("▸")
        self.toggle_button.setObjectName("setupChevronButton")
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.toggle_button.setFixedSize(34, 34)
        self.toggle_button.clicked.connect(self.toggle_collapsed)
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("setupSectionTitle")
        self.summary_label = QLabel("")
        self.summary_label.setObjectName("setupSectionSummary")
        self.summary_label.setWordWrap(True)
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.summary_label)
        self.action_button = QPushButton(action_text)
        self.action_button.setObjectName("setupActionButton")
        self.action_button.setCursor(Qt.PointingHandCursor)
        self.action_button.setFixedHeight(40)
        self.action_button.clicked.connect(lambda: self.action_requested.emit(self.key))
        header.addWidget(self.toggle_button, 0, Qt.AlignTop)
        header.addLayout(title_layout, 1)
        header.addWidget(self.action_button, 0, Qt.AlignRight | Qt.AlignVCenter)

        self.progress_shell = QWidget()
        progress_layout = QVBoxLayout(self.progress_shell)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(6)
        self.progress_detail = QLabel("")
        self.progress_detail.setObjectName("setupProgressDetail")
        self.progress_detail.setWordWrap(True)
        self.progress_meta = QLabel("")
        self.progress_meta.setObjectName("setupProgressMeta")
        self.progress_meta.setWordWrap(True)
        self.progress = QProgressBar()
        self.progress.setObjectName("setupSectionProgress")
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(10)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        progress_layout.addWidget(self.progress_detail)
        progress_layout.addWidget(self.progress_meta)
        progress_layout.addWidget(self.progress)
        self.progress_shell.setVisible(False)

        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(10)
        self.body.setVisible(False)

        layout.addLayout(header)
        layout.addWidget(self.progress_shell)
        layout.addWidget(self.body)
        self.apply_theme(theme)

    def add_row(self, row: SetupStatusRow) -> None:
        self.body_layout.addWidget(row)

    def set_collapsed(self, collapsed: bool) -> None:
        self.collapsed = collapsed
        self.toggle_button.setText("▸" if collapsed else "▾")
        self.body.setVisible(not collapsed)

    def toggle_collapsed(self) -> None:
        self.set_collapsed(not self.collapsed)

    def set_summary(self, text: str) -> None:
        self.summary_label.setText(text)

    def set_action_state(self, text: str, enabled: bool, busy: bool = False) -> None:
        self.action_button.setText(text)
        self.action_button.setEnabled(enabled)
        self.action_button.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)
        if busy:
            style = f"background: {self.theme.blue}; color: white; border: none; border-radius: 18px; padding: 0 18px; font-size: 13px; font-weight: 800;"
        elif enabled:
            style = f"background: {self.theme.red}; color: white; border: none; border-radius: 18px; padding: 0 18px; font-size: 13px; font-weight: 800;"
        else:
            style = f"background: {self.theme.soft_btn}; color: {self.theme.text}; border: 1px solid {self.theme.border}; border-radius: 18px; padding: 0 18px; font-size: 13px; font-weight: 800;"
        self.action_button.setStyleSheet(style)

    def set_progress(self, percent: int | None, detail: str, meta: str = "", visible: bool = True) -> None:
        self.progress_shell.setVisible(visible)
        self.progress_detail.setText(detail)
        self.progress_meta.setText(meta)
        self.progress_meta.setVisible(bool(meta))
        if percent is None:
            self.progress.setRange(0, 0)
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(max(0, min(100, int(percent))))

    def clear_progress(self) -> None:
        self.progress_shell.setVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress_detail.clear()
        self.progress_meta.clear()
        self.progress_meta.setVisible(False)

    def apply_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.setStyleSheet(
            f"""
            QFrame#setupSectionCard {{
                background: {theme.panel_alt};
                border: 1px solid {theme.border};
                border-radius: 26px;
            }}
            QPushButton#setupChevronButton {{
                background: {theme.soft_btn};
                color: {theme.text};
                border: 1px solid {theme.border};
                border-radius: 17px;
                font-size: 16px;
                font-weight: 800;
                padding: 0px;
            }}
            QPushButton#setupChevronButton:hover {{
                background: {theme.soft_btn_hover};
            }}
            QLabel#setupSectionTitle {{
                color: {theme.text};
                font-size: 18px;
                font-weight: 800;
            }}
            QLabel#setupSectionSummary, QLabel#setupProgressDetail, QLabel#setupProgressMeta {{
                color: {theme.muted};
                font-size: 12px;
            }}
            QProgressBar#setupSectionProgress {{
                background: {theme.surface};
                border: 1px solid {theme.border};
                border-radius: 999px;
            }}
            QProgressBar#setupSectionProgress::chunk {{
                background: {theme.blue};
                border-radius: 999px;
            }}
            """
        )
        self.set_action_state(self.action_button.text(), self.action_button.isEnabled(), False)


class LaunchChoiceDialog(QDialog):
    def __init__(self, theme: Theme, parent: QWidget | None = None):
        super().__init__(parent)
        self.selected_mode = ""
        self.theme = theme
        self.setWindowTitle("Comfy launch mode")
        self.setModal(True)
        self.setFixedSize(420, 220)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        title = QLabel("Как запускать ComfyUI?")
        title.setObjectName("dialogTitle")
        subtitle = QLabel("Выбери запуск на видеокарте или CPU-режим. Это можно поменять потом в Settings.")
        subtitle.setObjectName("dialogHint")
        subtitle.setWordWrap(True)

        buttons = QHBoxLayout()
        buttons.setSpacing(12)
        gpu_button = QPushButton("GPU / NVIDIA")
        gpu_button.setObjectName("dialogPrimaryButton")
        gpu_button.setCursor(Qt.PointingHandCursor)
        cpu_button = QPushButton("CPU")
        cpu_button.setObjectName("dialogSecondaryButton")
        cpu_button.setCursor(Qt.PointingHandCursor)
        gpu_button.clicked.connect(lambda: self.pick("fp16"))
        cpu_button.clicked.connect(lambda: self.pick("cpu"))
        buttons.addWidget(gpu_button)
        buttons.addWidget(cpu_button)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch(1)
        layout.addLayout(buttons)
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {theme.panel_bg};
                color: {theme.text};
            }}
            QLabel#dialogTitle {{
                color: {theme.text};
                font-size: 24px;
                font-weight: 800;
            }}
            QLabel#dialogHint {{
                color: {theme.muted};
                font-size: 13px;
            }}
            QPushButton#dialogPrimaryButton, QPushButton#dialogSecondaryButton {{
                min-height: 46px;
                border-radius: 18px;
                font-size: 14px;
                font-weight: 800;
            }}
            QPushButton#dialogPrimaryButton {{
                background: {theme.blue};
                color: white;
                border: none;
            }}
            QPushButton#dialogSecondaryButton {{
                background: {theme.soft_btn};
                color: {theme.text};
                border: 1px solid {theme.border};
            }}
            """
        )

    def pick(self, mode: str) -> None:
        self.selected_mode = mode
        self.accept()


class ComfySetupPage(QWidget):
    install_requested = Signal(str)
    back_requested = Signal()

    def __init__(self, theme: Theme, status: dict, parent: QWidget | None = None):
        super().__init__(parent)
        self.theme = theme
        self.status = status
        self.status_rows: dict[str, SetupStatusRow] = {}
        self.active_scope = ""
        self.install_target_path = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self.header_card = CardFrame("logsHeaderCard")
        header_layout = QHBoxLayout(self.header_card)
        header_layout.setContentsMargins(18, 16, 18, 16)
        header_layout.setSpacing(14)

        self.back_button = QPushButton("")
        self.back_button.setObjectName("logsBackButton")
        self.back_button.setFixedSize(50, 50)
        self.back_button.setIconSize(QSize(18, 18))
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.clicked.connect(self.back_requested.emit)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        self.title_label = QLabel("Comfy setup")
        self.title_label.setObjectName("logsTitle")
        self.subtitle_label = QLabel("Два блока: отдельный полный setup ComfyUI и отдельный setup nodes. Каждый можно свернуть или раскрыть.")
        self.subtitle_label.setObjectName("logsSubtitle")
        self.subtitle_label.setWordWrap(True)
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.subtitle_label)

        header_layout.addWidget(self.back_button, 0, Qt.AlignLeft | Qt.AlignTop)
        header_layout.addLayout(title_layout, 1)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("guideScroll")
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.content = QWidget()
        self.scroll.setWidget(self.content)
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        self.folder_label = QLabel("")
        self.folder_label.setObjectName("guidePathText")
        self.folder_label.setWordWrap(True)
        content_layout.addWidget(self.folder_label)

        self.comfy_section = SetupSectionCard("comfy", "Comfy", "Установить Comfy", theme)
        self.nodes_section = SetupSectionCard("nodes", "Nodes", "Установить nodes", theme)
        self.comfy_section.action_requested.connect(self.install_requested.emit)
        self.nodes_section.action_requested.connect(self.install_requested.emit)

        self.status_rows["comfy"] = SetupStatusRow("Portable ComfyUI", theme)
        self.status_rows["manager"] = SetupStatusRow("ComfyUI Manager", theme)
        self.comfy_section.add_row(self.status_rows["comfy"])
        self.comfy_section.add_row(self.status_rows["manager"])
        for model in status.get("models", []):
            key = f"model:{model['title']}"
            row = SetupStatusRow(model["title"], theme)
            self.status_rows[key] = row
            self.comfy_section.add_row(row)
        for node in status.get("nodes", []):
            key = f"node:{node['folder']}"
            row = SetupStatusRow(node["title"], theme)
            self.status_rows[key] = row
            self.nodes_section.add_row(row)

        content_layout.addWidget(self.comfy_section)
        content_layout.addWidget(self.nodes_section)
        content_layout.addStretch(1)

        layout.addWidget(self.header_card)
        layout.addWidget(self.scroll, 1)
        self.apply_theme()
        self.refresh_status(status)

    def apply_theme(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget {{
                background: transparent;
            }}
            QScrollArea#guideScroll {{
                background: transparent;
                border: none;
            }}
            QLabel#guidePathText {{
                font-size: 13px;
                color: {self.theme.text};
                background: {self.theme.panel_bg};
                border: 1px solid {self.theme.border};
                border-radius: 18px;
                padding: 12px 14px;
            }}
            """
        )
        self.comfy_section.apply_theme(self.theme)
        self.nodes_section.apply_theme(self.theme)
        for row in self.status_rows.values():
            row.apply_theme(self.theme)

    def clear_row_progress(self, keep_key: str = "") -> None:
        for key, row in self.status_rows.items():
            if keep_key and key == keep_key:
                continue
            row.clear_progress()

    def refresh_status(self, status: dict) -> None:
        self.status = status
        comfy_ready = bool(status.get("comfy_ready"))
        manager_ready = bool(status.get("manager_ready"))
        root_text = str(status.get("root", "") or "").strip()
        if root_text:
            self.folder_label.setText(root_text)
            self.install_target_path = ""
        elif self.install_target_path:
            self.folder_label.setText(f"Папка установки: {self.install_target_path}")
        else:
            self.folder_label.setText("Папка пока не выбрана")
        if comfy_ready and status.get("comfy_update_available"):
            self.status_rows["comfy"].set_state(False, str(status.get("comfy_update_message", "") or "Доступно обновление ComfyUI."), "missing")
        else:
            self.status_rows["comfy"].set_state(comfy_ready, "Portable найден" if comfy_ready else "Нужно скачать portable ComfyUI")
        self.status_rows["manager"].set_state(
            manager_ready,
            "Manager уже установлен" if manager_ready else ("Сначала нужен portable ComfyUI" if not comfy_ready else "Будет поставлен в custom_nodes"),
            "ready" if manager_ready else "missing",
        )
        for model in status.get("models", []):
            row = self.status_rows.get(f"model:{model['title']}")
            if not row:
                continue
            if model.get("ready"):
                row.set_state(True, "Файл уже на месте.", "ready")
            elif not model.get("download_checked", False):
                row.set_state(False, "Проверяем, доступна ли прямая ссылка на скачивание.", "missing")
            elif not model.get("download_available", True):
                row.set_state(False, str(model.get("download_message", "") or "Сейчас скачать нельзя: ссылка недоступна."), "unavailable")
            elif not comfy_ready:
                row.set_state(False, "Сначала нужен portable ComfyUI.", "missing")
            else:
                row.set_state(False, "Будет скачан и положен в нужную папку.", "missing")
        for node in status.get("nodes", []):
            row = self.status_rows.get(f"node:{node['folder']}")
            if not row:
                continue
            if node.get("ready"):
                row.set_state(True, "Нода уже установлена.", "ready")
            elif not comfy_ready:
                row.set_state(False, "Сначала нужен portable ComfyUI.", "missing")
            else:
                row.set_state(False, "Будет поставлена через git clone в custom_nodes.", "missing")

        comfy_missing = comfy_core_missing_count(status)
        nodes_missing = comfy_nodes_missing_count(status)
        self.comfy_section.set_summary("Все для Comfy уже готово." if comfy_missing == 0 else f"Не хватает {comfy_missing} компонентов для полного Comfy setup.")
        if not comfy_ready and nodes_missing:
            self.nodes_section.set_summary("Nodes ставятся только после полного Comfy setup.")
        else:
            self.nodes_section.set_summary("Все nodes уже стоят." if nodes_missing == 0 else f"Не хватает {nodes_missing} nodes для workflow.")
        if self.active_scope == "comfy":
            self.comfy_section.set_action_state("Установка...", False, True)
        else:
            comfy_action = "Обновить Comfy" if status.get("comfy_update_available") else "Установить Comfy"
            self.comfy_section.set_action_state(comfy_action if comfy_missing else "Все установлено", comfy_missing > 0 and self.active_scope != "nodes", False)
        if self.active_scope == "nodes":
            self.nodes_section.set_action_state("Установка...", False, True)
        else:
            self.nodes_section.set_action_state(
                "Установить nodes" if nodes_missing else "Все установлено",
                comfy_ready and nodes_missing > 0 and self.active_scope != "comfy",
                False,
            )
        if self.active_scope != "comfy":
            self.comfy_section.clear_progress()
        if self.active_scope != "nodes":
            self.nodes_section.clear_progress()

    def set_install_target_path(self, path: Path | str | None) -> None:
        self.install_target_path = str(path or "").strip()
        root_text = str(self.status.get("root", "") or "").strip()
        if not root_text:
            self.folder_label.setText(f"Папка установки: {self.install_target_path}" if self.install_target_path else "Папка пока не выбрана")

    def begin_install(self, scope: str, eta_text: str) -> None:
        self.active_scope = scope
        target = self.comfy_section if scope == "comfy" else self.nodes_section
        target.set_progress(0, "Подготавливаем установку.", f"Примерное время: {eta_text}", True)
        target.set_action_state("Установка...", False, True)
        self.refresh_status(cached_comfy_setup_status(force=True))

    def update_install_progress(self, scope: str, detail: str, percent: int, meta: str = "") -> None:
        target = self.comfy_section if scope == "comfy" else self.nodes_section
        payload = parse_setup_progress_meta(meta)
        row_key = str(payload.get("row_key", "") or "")
        row_meta = str(payload.get("meta_text", "") or meta)
        raw_row_percent = payload.get("row_percent")
        row_percent = None if raw_row_percent is None else int(max(0, min(100, int(raw_row_percent))))
        stage = str(payload.get("stage", "") or "").strip().lower()
        if row_key:
            self.clear_row_progress(keep_key=row_key)
            row = self.status_rows.get(row_key)
            if row:
                if stage == "done":
                    row.set_state(True, row_meta or "Проверено.", "ready")
                elif stage == "error":
                    row.set_state(False, row_meta or "Ошибка установки.", "unavailable")
                else:
                    row.set_progress(row_percent, row_meta)
        else:
            self.clear_row_progress()
        target.set_progress(percent, detail, row_meta or meta, True)

    def finish_install(self, scope: str, message: str, is_error: bool) -> None:
        target = self.comfy_section if scope == "comfy" else self.nodes_section
        self.active_scope = ""
        target.set_progress(0 if is_error else 100, message, "Установка остановилась с ошибкой." if is_error else "Готово.", True)
        self.clear_row_progress()
        self.refresh_status(cached_comfy_setup_status(force=True))


class MainWindow(QWidget):
    def __init__(self, autorun_mode: bool = False) -> None:
        super().__init__()
        self.setObjectName("appRoot")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.bridge = UiBridge()
        self.bridge.finished.connect(self.on_job_finished)
        self.bridge.progress.connect(self.on_job_progress)
        self.bridge.snapshot_ready.connect(self.on_snapshot_ready)
        self.bridge.snapshot_failed.connect(self.on_snapshot_failed)
        self.bridge.setup_status_ready.connect(self.on_setup_status_ready)
        self.bridge.update_ready.connect(self.on_update_ready)
        self.bridge.update_failed.connect(self.on_update_failed)

        self.config = load_config()
        self.state_cache = load_state()
        self.theme = THEMES[self.config["theme"]]
        self.autorun_mode = autorun_mode
        self.applied_theme_name = None
        self.busy = False
        self.busy_dots = 0
        self.drawer_open = False
        self.friends_open = False
        self.friend_rows: dict[str, FriendLinkRow] = {}
        self.latest_snap: dict | None = None
        self.auto_restart_inflight = False
        self.comfy_restore_inflight = False
        self.friend_restore_inflight: set[str] = set()
        self.last_url = self.state_cache.get("last_url", "")
        self.last_footer = ""
        self.last_log_hint = ""
        self.action_visual_state = ""
        self.friends_visual_state = ""
        self.install_visual_state = ""
        self.settings_dirty = False
        self.syncing_controls = False
        self.overlay_animation_count = 0
        self.install_setup_inflight = False
        self.install_setup_paused_poll = False
        self.install_setup_eta = ""
        self.install_setup_progress_percent = 0
        self.install_setup_progress_detail = ""
        self.install_setup_progress_meta = ""
        self.install_setup_scope = ""
        self.install_setup_last_scope = ""
        self.install_setup_last_message = ""
        self.install_setup_last_error = False
        self.setup_page_widget: ComfySetupPage | None = None
        self.release_info: dict[str, object] | None = None
        self.update_banner_kind = "portal"
        self.update_check_inflight = False
        self.update_download_inflight = False
        self.update_banner_dismissed_tag = ""
        self.onboarding_step = "mode"
        self.onboarding_dismissed = False
        self.onboarding_install_expanded = False
        self.onboarding_force_space_step = False
        self.onboarding_install_target_parent: Path | None = None
        self.onboarding_install_rows: dict[str, SetupStatusRow] = {}
        self.refresh_inflight = False
        self.refresh_requested = False
        self.refresh_requested_logs = False
        self.drawer_hide_after_anim = False
        self.friends_hide_after_anim = False
        self.logs_view_open = False
        self.setup_view_open = False
        self.launch_choice_open = False
        self.launch_choice_hide_after_anim = False
        self.launch_choice_paused_poll = False
        self.last_comfy_log_full = ""
        self.logs_refresh_inflight = False
        self.last_setup_page_refresh_at = 0.0
        self.setup_status_refresh_inflight = False
        self.pending_page_index: int | None = None
        self.page_fade_phase = "idle"
        self.toast_timer = QTimer(self)
        self.toast_timer.setSingleShot(True)
        self.toast_timer.timeout.connect(self.hide_toast)

        self.setWindowTitle(APP_NAME)
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
        self.setMinimumSize(1060, 700)
        icon_path = resolve_asset_path("comfy_portal.ico")
        if not icon_path.exists():
            icon_path = resolve_asset_path("comfy_portal_icon.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.build_ui()
        self.apply_theme()
        self.load_controls_from_config()

        self.poll_timer = QTimer(self)
        self.poll_timer.setTimerType(Qt.CoarseTimer)
        self.poll_timer.timeout.connect(self.request_refresh_view)
        self.request_refresh_view()
        self.poll_timer.start(POLL_MS)

        self.busy_timer = QTimer(self)
        self.busy_timer.setTimerType(Qt.CoarseTimer)
        self.busy_timer.timeout.connect(self.animate_busy_button)

        self.logs_fast_timer = QTimer(self)
        self.logs_fast_timer.setTimerType(Qt.CoarseTimer)
        self.logs_fast_timer.timeout.connect(self.refresh_live_logs_fast)

        self.drawer_anim = QPropertyAnimation(self.drawer, b"pos", self)
        self.drawer_anim.setDuration(OVERLAY_ANIMATION_MS)
        self.drawer_anim.setEasingCurve(QEasingCurve.InOutCubic)

        self.friends_anim = QPropertyAnimation(self.friends_panel, b"pos", self)
        self.friends_anim.setDuration(OVERLAY_ANIMATION_MS)
        self.friends_anim.setEasingCurve(QEasingCurve.InOutCubic)

        self.drawer_fade_anim = QPropertyAnimation(self.drawer_opacity, b"opacity", self)
        self.drawer_fade_anim.setDuration(OVERLAY_ANIMATION_MS)
        self.drawer_fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.drawer_fade_anim.finished.connect(self.on_drawer_fade_finished)

        self.friends_fade_anim = QPropertyAnimation(self.friends_opacity, b"opacity", self)
        self.friends_fade_anim.setDuration(OVERLAY_ANIMATION_MS)
        self.friends_fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.friends_fade_anim.finished.connect(self.on_friends_fade_finished)

        self.backdrop_anim = QPropertyAnimation(self.drawer_backdrop, b"alpha", self)
        self.backdrop_anim.setDuration(BACKDROP_FADE_MS)
        self.backdrop_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.backdrop_anim.finished.connect(self.on_backdrop_animation_finished)

        self.page_stack_opacity = QGraphicsOpacityEffect(self.page_stack)
        self.page_stack_opacity.setOpacity(1.0)
        self.page_stack.setGraphicsEffect(self.page_stack_opacity)
        self.page_fade_anim = QPropertyAnimation(self.page_stack_opacity, b"opacity", self)
        self.page_fade_anim.setDuration(PAGE_FADE_MS)
        self.page_fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.page_fade_anim.finished.connect(self.on_page_fade_finished)

        self.launch_choice_anim = QPropertyAnimation(self.launch_choice_card, b"pos", self)
        self.launch_choice_anim.setDuration(220)
        self.launch_choice_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.launch_choice_fade_anim = QPropertyAnimation(self.launch_choice_opacity, b"opacity", self)
        self.launch_choice_fade_anim.setDuration(180)
        self.launch_choice_fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.launch_choice_fade_anim.finished.connect(self.on_launch_choice_fade_finished)

        self.launch_choice_backdrop_anim = QPropertyAnimation(self.launch_choice_backdrop, b"alpha", self)
        self.launch_choice_backdrop_anim.setDuration(220)
        self.launch_choice_backdrop_anim.setEasingCurve(QEasingCurve.OutCubic)

        if self.autorun_mode:
            QTimer.singleShot(900, self.run_autorun_sequence)
        else:
            QTimer.singleShot(320, self.prompt_launch_choice_if_needed)
        QTimer.singleShot(1600, self.request_update_check)

    def build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(0)

        self.page_stack = QStackedWidget()
        self.page_stack.setObjectName("pageStack")
        root.addWidget(self.page_stack, 1)

        self.main_scroll = QScrollArea()
        self.main_scroll.setObjectName("mainScroll")
        self.main_scroll.setFrameShape(QFrame.NoFrame)
        self.main_scroll.setWidgetResizable(True)
        self.main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.page_stack.addWidget(self.main_scroll)

        self.main_content = QWidget()
        self.main_content.setObjectName("mainContent")
        self.main_scroll.setWidget(self.main_content)

        content_layout = QVBoxLayout(self.main_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        self.topbar = CardFrame("topBar")
        topbar_layout = QHBoxLayout(self.topbar)
        topbar_layout.setContentsMargins(18, 16, 18, 16)
        topbar_layout.setSpacing(16)

        self.settings_button = QPushButton("")
        self.settings_button.setObjectName("gearButton")
        self.settings_button.setFixedSize(54, 54)
        self.settings_button.setIconSize(QSize(22, 22))
        self.settings_button.setToolTip("Settings")
        self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.clicked.connect(self.toggle_drawer)

        self.telegram_brand_button = QPushButton("")
        self.telegram_brand_button.setObjectName("telegramBrandButton")
        self.telegram_brand_button.setFixedSize(TELEGRAM_BRAND_SIZE, TELEGRAM_BRAND_SIZE)
        self.telegram_brand_button.setIconSize(QSize(TELEGRAM_BRAND_SIZE, TELEGRAM_BRAND_SIZE))
        self.telegram_brand_button.setToolTip("Открыть Telegram-канал ComfyUI Guide")
        self.telegram_brand_button.setCursor(Qt.PointingHandCursor)
        self.telegram_brand_button.clicked.connect(self.open_telegram_channel)

        self.github_brand_button = QPushButton("")
        self.github_brand_button.setObjectName("githubBrandButton")
        self.github_brand_button.setFixedSize(GITHUB_BRAND_SIZE, GITHUB_BRAND_SIZE)
        self.github_brand_button.setIconSize(QSize(GITHUB_BRAND_SIZE, GITHUB_BRAND_SIZE))
        self.github_brand_button.setToolTip("Открыть GitHub репозиторий Comfy Portal")
        self.github_brand_button.setCursor(Qt.PointingHandCursor)
        self.github_brand_button.clicked.connect(self.open_github_repo)

        brand_layout = QVBoxLayout()
        brand_layout.setSpacing(2)
        self.title_label = QLabel("Comfy Portal")
        self.title_label.setObjectName("titleLabel")
        self.subtitle_label = QLabel("Запуск, туннель и копирование ссылки в одном месте.")
        self.subtitle_label.setObjectName("subtitleLabel")
        brand_layout.addWidget(self.title_label)
        brand_layout.addWidget(self.subtitle_label)

        self.friends_button = QPushButton("Friends")
        self.friends_button.setObjectName("friendsButton")
        self.friends_button.setFixedHeight(52)
        self.friends_button.setMinimumWidth(122)
        self.friends_button.setCursor(Qt.PointingHandCursor)
        self.friends_button.clicked.connect(self.toggle_friends_panel)

        self.logs_button = QPushButton("Logs")
        self.logs_button.setObjectName("logsButton")
        self.logs_button.setFixedHeight(52)
        self.logs_button.setMinimumWidth(118)
        self.logs_button.setCursor(Qt.PointingHandCursor)
        self.logs_button.clicked.connect(lambda: self.set_logs_view_open(True))

        self.install_button = QPushButton("")
        self.install_button.setObjectName("installButton")
        self.install_button.setFixedSize(54, 52)
        self.install_button.setIconSize(QSize(24, 24))
        self.install_button.setToolTip("Открыть Comfy setup")
        self.install_button.setCursor(Qt.PointingHandCursor)
        self.install_button.clicked.connect(lambda: self.set_setup_view_open(True))
        self.install_badge = QLabel("!")
        self.install_badge.setParent(self.install_button)
        self.install_badge.setObjectName("installBadge")
        self.install_badge.setAlignment(Qt.AlignCenter)
        self.install_badge.setFixedSize(16, 16)
        self.install_badge.move(self.install_button.width() - 16, 0)
        self.install_badge.hide()

        self.action_button = QPushButton("Start")
        self.action_button.setObjectName("startButton")
        self.action_button.setFixedSize(148, 48)
        self.action_button.setCursor(Qt.PointingHandCursor)
        self.action_button.clicked.connect(self.on_action_button_clicked)

        self.refresh_button = QPushButton("")
        self.refresh_button.setObjectName("refreshButton")
        self.refresh_button.setFixedSize(48, 48)
        self.refresh_button.setIconSize(QSize(20, 20))
        self.refresh_button.setToolTip("Regenerate link")
        self.refresh_button.setCursor(Qt.PointingHandCursor)
        self.refresh_button.clicked.connect(self.on_refresh_main_link_clicked)

        top_actions_layout = QHBoxLayout()
        top_actions_layout.setSpacing(10)
        top_actions_layout.addWidget(self.install_button)
        top_actions_layout.addWidget(self.logs_button)
        top_actions_layout.addWidget(self.friends_button)

        topbar_layout.addWidget(self.settings_button, 0, Qt.AlignLeft)
        topbar_layout.addWidget(self.telegram_brand_button, 0, Qt.AlignLeft | Qt.AlignVCenter)
        topbar_layout.addWidget(self.github_brand_button, 0, Qt.AlignLeft | Qt.AlignVCenter)
        topbar_layout.addLayout(brand_layout, 0)
        topbar_layout.addStretch(1)
        topbar_layout.addLayout(top_actions_layout, 0)

        self.progress = QProgressBar()
        self.progress.setObjectName("launchProgress")
        self.progress.setFixedHeight(8)
        self.progress.setTextVisible(False)
        self.progress.setVisible(False)

        self.hero = CardFrame("heroCard")
        hero_layout = QVBoxLayout(self.hero)
        hero_layout.setContentsMargins(38, 34, 38, 34)
        hero_layout.setSpacing(16)

        self.hero_title = QLabel("LocalTunnel Link")
        self.hero_title.setObjectName("heroTitle")
        self.hero_title.setAlignment(Qt.AlignCenter)
        self.hero_subtitle = QLabel("Ссылка появится здесь, как только ComfyUI и туннель будут готовы.")
        self.hero_subtitle.setObjectName("heroSubtitle")
        self.hero_subtitle.setAlignment(Qt.AlignCenter)
        self.hero_subtitle.setWordWrap(True)

        self.link_shell = QFrame()
        self.link_shell.setObjectName("linkShell")
        link_layout = QHBoxLayout(self.link_shell)
        link_layout.setContentsMargins(22, 18, 18, 18)
        link_layout.setSpacing(12)

        self.link_field = QLineEdit()
        self.link_field.setObjectName("linkField")
        self.link_field.setReadOnly(True)
        self.link_field.setText("Публичной ссылки пока нет")
        self.link_field.setPlaceholderText("Публичной ссылки пока нет")
        self.link_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.copy_button = QPushButton("")
        self.copy_button.setObjectName("copyButton")
        self.copy_button.setFixedSize(48, 48)
        self.copy_button.setIconSize(QSize(20, 20))
        self.copy_button.setToolTip("Copy link")
        self.copy_button.setCursor(Qt.PointingHandCursor)
        self.copy_button.clicked.connect(self.copy_link)

        link_layout.addWidget(self.refresh_button, 0, Qt.AlignLeft)
        link_layout.addWidget(self.link_field, 1)
        link_layout.addWidget(self.action_button, 0, Qt.AlignRight)
        link_layout.addWidget(self.copy_button, 0, Qt.AlignRight)

        hero_layout.addWidget(self.hero_title)
        hero_layout.addWidget(self.hero_subtitle)
        hero_layout.addSpacing(10)
        hero_layout.addWidget(self.link_shell)
        hero_layout.addStretch(1)

        self.status_panel = CardFrame("statusPanel")
        status_layout = QVBoxLayout(self.status_panel)
        status_layout.setContentsMargins(28, 26, 28, 26)
        status_layout.setSpacing(16)

        self.status_title = QLabel("System status")
        self.status_title.setObjectName("sectionTitle")
        self.status_subtitle = QLabel("Что активно сейчас и что делает лаунчер.")
        self.status_subtitle.setObjectName("sectionSubtitle")
        self.status_subtitle.setWordWrap(True)

        self.status_cards_layout = QHBoxLayout()
        self.status_cards_layout.setSpacing(14)

        self.comfy_card = StatusCard("ComfyUI")
        self.tunnel_card = StatusCard("Tunnel")
        self.launcher_card = StatusCard("Launcher")

        self.status_cards_layout.addWidget(self.comfy_card, 1)
        self.status_cards_layout.addWidget(self.tunnel_card, 1)
        self.status_cards_layout.addWidget(self.launcher_card, 1)

        self.footer_hint = QLabel("")
        self.footer_hint.setObjectName("footerHint")
        self.footer_hint.setWordWrap(True)

        status_layout.addWidget(self.status_title)
        status_layout.addWidget(self.status_subtitle)
        status_layout.addLayout(self.status_cards_layout)
        status_layout.addWidget(self.footer_hint)

        self.bottom_space = QWidget()
        self.bottom_space.setObjectName("bottomSpacer")
        self.bottom_space.setFixedHeight(220)

        content_layout.addWidget(self.topbar)
        content_layout.addWidget(self.progress)
        content_layout.addWidget(self.hero)
        content_layout.addWidget(self.status_panel)
        content_layout.addWidget(self.bottom_space)

        self.logs_page = QWidget()
        self.logs_page.setObjectName("logsPage")
        self.page_stack.addWidget(self.logs_page)
        logs_page_layout = QVBoxLayout(self.logs_page)
        logs_page_layout.setContentsMargins(0, 0, 0, 0)
        logs_page_layout.setSpacing(16)

        self.logs_header_card = CardFrame("logsHeaderCard")
        logs_header_layout = QHBoxLayout(self.logs_header_card)
        logs_header_layout.setContentsMargins(18, 16, 18, 16)
        logs_header_layout.setSpacing(14)

        self.logs_back_button = QPushButton("Back")
        self.logs_back_button.setObjectName("logsBackButton")
        self.logs_back_button.setFixedHeight(52)
        self.logs_back_button.setMinimumWidth(120)
        self.logs_back_button.setIconSize(QSize(18, 18))
        self.logs_back_button.setCursor(Qt.PointingHandCursor)
        self.logs_back_button.clicked.connect(lambda: self.set_logs_view_open(False))

        logs_title_layout = QVBoxLayout()
        logs_title_layout.setSpacing(2)
        self.logs_title = QLabel("Comfy Logs")
        self.logs_title.setObjectName("logsTitle")
        self.logs_subtitle = QLabel("Живой вывод stdout и stderr ComfyUI прямо внутри портала.")
        self.logs_subtitle.setObjectName("logsSubtitle")
        self.logs_subtitle.setWordWrap(True)
        logs_title_layout.addWidget(self.logs_title)
        logs_title_layout.addWidget(self.logs_subtitle)

        self.logs_status_pill = QLabel("Оффлайн")
        self.logs_status_pill.setObjectName("logsStatusPill")

        logs_header_layout.addWidget(self.logs_back_button, 0, Qt.AlignLeft)
        logs_header_layout.addLayout(logs_title_layout, 1)
        logs_header_layout.addWidget(self.logs_status_pill, 0, Qt.AlignRight | Qt.AlignVCenter)

        self.logs_card = CardFrame("logsCard")
        logs_card_layout = QVBoxLayout(self.logs_card)
        logs_card_layout.setContentsMargins(20, 20, 20, 20)
        logs_card_layout.setSpacing(12)
        self.logs_viewer = QPlainTextEdit()
        self.logs_viewer.setObjectName("logsViewer")
        self.logs_viewer.setReadOnly(True)
        self.logs_viewer.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.logs_viewer.setPlaceholderText("Логи ComfyUI появятся здесь после запуска.")
        logs_card_layout.addWidget(self.logs_viewer, 1)

        logs_page_layout.addWidget(self.logs_header_card)
        logs_page_layout.addWidget(self.logs_card, 1)

        self.setup_page = ComfySetupPage(self.theme, cached_comfy_setup_status(self.config), self)
        self.setup_page_widget = self.setup_page
        self.setup_page.install_requested.connect(self.start_setup_install)
        self.setup_page.back_requested.connect(lambda: self.set_setup_view_open(False))
        self.page_stack.addWidget(self.setup_page)

        self.toast = QLabel("", self)
        self.toast.setObjectName("toast")
        self.toast.setVisible(False)
        self.toast.setAlignment(Qt.AlignCenter)

        self.update_banner = CardFrame("updateBanner")
        self.update_banner.setParent(self)
        self.update_banner.setAttribute(Qt.WA_StyledBackground, True)
        self.update_banner.hide()
        update_banner_layout = QVBoxLayout(self.update_banner)
        update_banner_layout.setContentsMargins(16, 14, 16, 14)
        update_banner_layout.setSpacing(10)
        update_header_layout = QHBoxLayout()
        update_header_layout.setSpacing(10)
        self.update_banner_title = QLabel("Доступно обновление")
        self.update_banner_title.setObjectName("updateBannerTitle")
        self.update_banner_close = QPushButton("×")
        self.update_banner_close.setObjectName("updateBannerClose")
        self.update_banner_close.setFixedSize(26, 26)
        self.update_banner_close.setCursor(Qt.PointingHandCursor)
        self.update_banner_close.clicked.connect(self.dismiss_update_banner)
        update_header_layout.addWidget(self.update_banner_title, 1)
        update_header_layout.addWidget(self.update_banner_close, 0, Qt.AlignRight)
        self.update_banner_subtitle = QLabel("На GitHub вышел новый релиз Comfy Portal.")
        self.update_banner_subtitle.setObjectName("updateBannerSubtitle")
        self.update_banner_subtitle.setWordWrap(True)
        update_actions_layout = QHBoxLayout()
        update_actions_layout.setSpacing(8)
        self.update_banner_view_button = QPushButton("Что нового")
        self.update_banner_view_button.setObjectName("updateBannerSecondaryButton")
        self.update_banner_view_button.setCursor(Qt.PointingHandCursor)
        self.update_banner_view_button.clicked.connect(self.open_github_releases)
        self.update_banner_install_button = QPushButton("Обновить")
        self.update_banner_install_button.setObjectName("updateBannerPrimaryButton")
        self.update_banner_install_button.setCursor(Qt.PointingHandCursor)
        self.update_banner_install_button.clicked.connect(self.install_github_update)
        update_actions_layout.addWidget(self.update_banner_view_button, 0)
        update_actions_layout.addWidget(self.update_banner_install_button, 0)
        update_banner_layout.addLayout(update_header_layout)
        update_banner_layout.addWidget(self.update_banner_subtitle)
        update_banner_layout.addLayout(update_actions_layout)

        self.drawer_backdrop = DrawerBackdrop(self)
        self.drawer_backdrop.clicked.connect(self.close_overlays)

        self.launch_choice_backdrop = DrawerBackdrop(self)
        self.launch_choice_backdrop.setObjectName("launchChoiceBackdrop")

        self.launch_choice_card = CardFrame("launchChoiceCard")
        self.launch_choice_card.setParent(self)
        self.launch_choice_card.setAttribute(Qt.WA_StyledBackground, True)
        self.launch_choice_card.setMinimumSize(680, 560)
        self.launch_choice_card.hide()
        self.launch_choice_opacity = QGraphicsOpacityEffect(self.launch_choice_card)
        self.launch_choice_opacity.setOpacity(1.0)
        self.launch_choice_card.setGraphicsEffect(self.launch_choice_opacity)

        launch_choice_layout = QVBoxLayout(self.launch_choice_card)
        launch_choice_layout.setContentsMargins(26, 22, 26, 24)
        launch_choice_layout.setSpacing(16)

        launch_choice_header = QHBoxLayout()
        launch_choice_header.setSpacing(10)
        launch_choice_header.addStretch(1)
        self.launch_choice_close_button = QPushButton("×")
        self.launch_choice_close_button.setObjectName("launchChoiceCloseButton")
        self.launch_choice_close_button.setFixedSize(34, 34)
        self.launch_choice_close_button.setCursor(Qt.PointingHandCursor)
        self.launch_choice_close_button.clicked.connect(self.dismiss_onboarding)
        launch_choice_header.addWidget(self.launch_choice_close_button, 0, Qt.AlignRight)
        launch_choice_layout.addLayout(launch_choice_header)

        self.launch_choice_stack = QStackedWidget()
        self.launch_choice_stack.setObjectName("launchChoiceStack")
        launch_choice_layout.addWidget(self.launch_choice_stack, 1)

        self.onboarding_space_page = QWidget()
        onboarding_space_layout = QVBoxLayout(self.onboarding_space_page)
        onboarding_space_layout.setContentsMargins(6, 6, 6, 6)
        onboarding_space_layout.setSpacing(14)
        self.onboarding_space_title = QLabel("У нас не хватает места для полной установки")
        self.onboarding_space_title.setObjectName("launchChoiceTitle")
        self.onboarding_space_hint = QLabel("Сейчас проверили свободное место. Если Comfy уже стоит, просто укажи папку и мы перепроверим. Если нет, можно закрыть онбординг и установить потом вручную.")
        self.onboarding_space_hint.setObjectName("launchChoiceSubtitle")
        self.onboarding_space_hint.setWordWrap(True)
        self.onboarding_space_stats = QLabel("")
        self.onboarding_space_stats.setObjectName("launchChoiceStats")
        self.onboarding_space_stats.setWordWrap(True)
        self.onboarding_space_folder_label = QLabel("Если Comfy уже установлен, укажи папку и мы сразу перепроверим.")
        self.onboarding_space_folder_label.setObjectName("launchChoiceStepHint")
        self.onboarding_space_folder_label.setWordWrap(True)
        self.onboarding_space_pick_button = QPushButton("Уже есть Comfy")
        self.onboarding_space_pick_button.setObjectName("launchChoicePrimaryButton")
        self.onboarding_space_pick_button.setMinimumHeight(52)
        self.onboarding_space_pick_button.setCursor(Qt.PointingHandCursor)
        self.onboarding_space_pick_button.clicked.connect(self.on_onboarding_choose_existing_clicked)
        self.onboarding_space_skip_button = QPushButton("Пропустить")
        self.onboarding_space_skip_button.setObjectName("launchChoiceContinueButton")
        self.onboarding_space_skip_button.setMinimumHeight(52)
        self.onboarding_space_skip_button.setCursor(Qt.PointingHandCursor)
        self.onboarding_space_skip_button.clicked.connect(self.skip_onboarding_install_step)
        onboarding_space_actions = QHBoxLayout()
        onboarding_space_actions.setSpacing(12)
        onboarding_space_actions.addWidget(self.onboarding_space_pick_button, 1)
        onboarding_space_actions.addWidget(self.onboarding_space_skip_button, 1)
        onboarding_space_layout.addWidget(self.onboarding_space_title)
        onboarding_space_layout.addWidget(self.onboarding_space_hint)
        onboarding_space_layout.addWidget(self.onboarding_space_stats)
        onboarding_space_layout.addStretch(1)
        onboarding_space_layout.addWidget(self.onboarding_space_folder_label)
        onboarding_space_layout.addLayout(onboarding_space_actions)
        self.launch_choice_stack.addWidget(self.onboarding_space_page)

        self.onboarding_install_page = QWidget()
        onboarding_install_layout = QVBoxLayout(self.onboarding_install_page)
        onboarding_install_layout.setContentsMargins(6, 6, 6, 6)
        onboarding_install_layout.setSpacing(14)
        self.onboarding_install_title = QLabel("Подключим ComfyUI к порталу")
        self.onboarding_install_title.setObjectName("launchChoiceTitle")
        self.onboarding_install_hint = QLabel("Если portable ComfyUI уже есть, укажи папку. Если нет, портал сам скачает сборку, создаст папки и разложит все файлы по местам.")
        self.onboarding_install_hint.setObjectName("launchChoiceSubtitle")
        self.onboarding_install_hint.setWordWrap(True)
        self.onboarding_install_path = QLabel("")
        self.onboarding_install_path.setObjectName("launchChoiceStats")
        self.onboarding_install_path.setWordWrap(True)

        onboarding_status = cached_comfy_setup_status(self.config)
        self.onboarding_install_section = SetupSectionCard("comfy", "Comfy setup", "Installing...", self.theme)
        self.onboarding_install_section.action_button.hide()
        self.onboarding_install_section.set_collapsed(True)
        self.onboarding_install_rows["comfy"] = SetupStatusRow("Portable ComfyUI", self.theme)
        self.onboarding_install_rows["manager"] = SetupStatusRow("ComfyUI Manager", self.theme)
        self.onboarding_install_section.add_row(self.onboarding_install_rows["comfy"])
        self.onboarding_install_section.add_row(self.onboarding_install_rows["manager"])
        for model in onboarding_status.get("models", []):
            key = f"model:{model['title']}"
            row = SetupStatusRow(model["title"], self.theme)
            self.onboarding_install_rows[key] = row
            self.onboarding_install_section.add_row(row)
        self.refresh_onboarding_install_rows(onboarding_status)

        self.onboarding_install_pick_button = QPushButton("Уже есть Comfy")
        self.onboarding_install_pick_button.setObjectName("launchChoiceSecondaryButton")
        self.onboarding_install_pick_button.setMinimumHeight(50)
        self.onboarding_install_pick_button.setCursor(Qt.PointingHandCursor)
        self.onboarding_install_pick_button.clicked.connect(self.on_onboarding_choose_existing_clicked)
        self.onboarding_install_start_button = QPushButton("Установить")
        self.onboarding_install_start_button.setObjectName("launchChoiceSuccessButton")
        self.onboarding_install_start_button.setMinimumHeight(50)
        self.onboarding_install_start_button.setCursor(Qt.PointingHandCursor)
        self.onboarding_install_start_button.clicked.connect(self.begin_onboarding_install)
        self.onboarding_install_skip_button = QPushButton("Пропустить")
        self.onboarding_install_skip_button.setObjectName("launchChoiceContinueButton")
        self.onboarding_install_skip_button.setMinimumHeight(50)
        self.onboarding_install_skip_button.setCursor(Qt.PointingHandCursor)
        self.onboarding_install_skip_button.clicked.connect(self.skip_onboarding_install_step)
        onboarding_install_actions = QHBoxLayout()
        onboarding_install_actions.setSpacing(12)
        onboarding_install_actions.addWidget(self.onboarding_install_pick_button, 1)
        onboarding_install_actions.addWidget(self.onboarding_install_start_button, 1)
        onboarding_install_actions.addWidget(self.onboarding_install_skip_button, 1)
        onboarding_install_layout.addWidget(self.onboarding_install_title)
        onboarding_install_layout.addWidget(self.onboarding_install_hint)
        onboarding_install_layout.addWidget(self.onboarding_install_path)
        onboarding_install_layout.addWidget(self.onboarding_install_section)
        onboarding_install_layout.addStretch(1)
        onboarding_install_layout.addLayout(onboarding_install_actions)
        self.launch_choice_stack.addWidget(self.onboarding_install_page)

        self.onboarding_mode_page = QWidget()
        onboarding_mode_layout = QVBoxLayout(self.onboarding_mode_page)
        onboarding_mode_layout.setContentsMargins(6, 6, 6, 6)
        onboarding_mode_layout.setSpacing(14)
        self.onboarding_mode_title = QLabel("Для начала использования выбери способ запуска ComfyUI")
        self.onboarding_mode_title.setObjectName("launchChoiceTitle")
        self.onboarding_mode_hint = QLabel("GPU режим рекомендуем для большинства ПК. CPU режим стоит брать только если видеокарты нет или она не подходит.")
        self.onboarding_mode_hint.setObjectName("launchChoiceSubtitle")
        self.onboarding_mode_hint.setWordWrap(True)
        self.onboarding_gpu_button = QPushButton("GPU")
        self.onboarding_gpu_button.setObjectName("launchChoiceModeGreenButton")
        self.onboarding_gpu_button.setMinimumHeight(58)
        self.onboarding_gpu_button.setCursor(Qt.PointingHandCursor)
        self.onboarding_gpu_button.clicked.connect(lambda: self.set_onboarding_mode("fp16"))
        self.onboarding_cpu_button = QPushButton("CPU")
        self.onboarding_cpu_button.setObjectName("launchChoiceModeRedButton")
        self.onboarding_cpu_button.setMinimumHeight(58)
        self.onboarding_cpu_button.setCursor(Qt.PointingHandCursor)
        self.onboarding_cpu_button.clicked.connect(lambda: self.set_onboarding_mode("cpu"))
        self.onboarding_mode_recommend = QLabel("Рекомендуется: GPU")
        self.onboarding_mode_recommend.setObjectName("launchChoiceStepHint")
        mode_buttons_layout = QHBoxLayout()
        mode_buttons_layout.setSpacing(12)
        mode_buttons_layout.addWidget(self.onboarding_gpu_button, 1)
        mode_buttons_layout.addWidget(self.onboarding_cpu_button, 1)
        self.onboarding_mode_continue = QPushButton("Продолжить")
        self.onboarding_mode_continue.setObjectName("launchChoiceContinueButton")
        self.onboarding_mode_continue.setMinimumHeight(52)
        self.onboarding_mode_continue.setCursor(Qt.PointingHandCursor)
        self.onboarding_mode_continue.clicked.connect(self.advance_onboarding_from_mode)
        onboarding_mode_layout.addWidget(self.onboarding_mode_title)
        onboarding_mode_layout.addWidget(self.onboarding_mode_hint)
        onboarding_mode_layout.addLayout(mode_buttons_layout)
        onboarding_mode_layout.addWidget(self.onboarding_mode_recommend)
        onboarding_mode_layout.addStretch(1)
        onboarding_mode_layout.addWidget(self.onboarding_mode_continue)
        self.launch_choice_stack.addWidget(self.onboarding_mode_page)

        self.onboarding_subdomain_page = QWidget()
        onboarding_subdomain_layout = QVBoxLayout(self.onboarding_subdomain_page)
        onboarding_subdomain_layout.setContentsMargins(6, 6, 6, 6)
        onboarding_subdomain_layout.setSpacing(14)
        self.onboarding_subdomain_title = QLabel("Придумай свою ссылку для Comfy")
        self.onboarding_subdomain_title.setObjectName("launchChoiceTitle")
        self.onboarding_subdomain_hint = QLabel("Минимум 6 символов. Разрешены только буквы, цифры и дефис.")
        self.onboarding_subdomain_hint.setObjectName("launchChoiceSubtitle")
        self.onboarding_subdomain_hint.setWordWrap(True)
        self.onboarding_subdomain_input = QLineEdit()
        self.onboarding_subdomain_input.setObjectName("launchChoiceInput")
        self.onboarding_subdomain_input.setMinimumHeight(54)
        self.onboarding_subdomain_input.setPlaceholderText("mycomfy01")
        self.onboarding_subdomain_input.textEdited.connect(self.on_onboarding_subdomain_changed)
        self.onboarding_subdomain_error = QLabel("Субдомен еще не подходит.")
        self.onboarding_subdomain_error.setObjectName("launchChoiceError")
        self.onboarding_subdomain_error.setWordWrap(True)
        self.onboarding_subdomain_continue = QPushButton("Продолжить")
        self.onboarding_subdomain_continue.setObjectName("launchChoiceContinueButton")
        self.onboarding_subdomain_continue.setMinimumHeight(52)
        self.onboarding_subdomain_continue.setCursor(Qt.PointingHandCursor)
        self.onboarding_subdomain_continue.clicked.connect(self.advance_onboarding_from_subdomain)
        onboarding_subdomain_layout.addWidget(self.onboarding_subdomain_title)
        onboarding_subdomain_layout.addWidget(self.onboarding_subdomain_hint)
        onboarding_subdomain_layout.addWidget(self.onboarding_subdomain_input)
        onboarding_subdomain_layout.addWidget(self.onboarding_subdomain_error)
        onboarding_subdomain_layout.addStretch(1)
        onboarding_subdomain_layout.addWidget(self.onboarding_subdomain_continue)
        self.launch_choice_stack.addWidget(self.onboarding_subdomain_page)

        self.onboarding_guide_page = QWidget()
        onboarding_guide_layout = QVBoxLayout(self.onboarding_guide_page)
        onboarding_guide_layout.setContentsMargins(6, 6, 6, 6)
        onboarding_guide_layout.setSpacing(14)
        self.onboarding_guide_title = QLabel("Все готово")
        self.onboarding_guide_title.setObjectName("launchChoiceTitle")
        self.onboarding_guide_hint = QLabel("Нажми Start, вставь ссылку в модуль `comfyui_url` и можно сразу пользоваться порталом.")
        self.onboarding_guide_hint.setObjectName("launchChoiceSubtitle")
        self.onboarding_guide_hint.setWordWrap(True)
        self.onboarding_guide_start = QPushButton("Начать")
        self.onboarding_guide_start.setObjectName("launchChoiceContinueButton")
        self.onboarding_guide_start.setMinimumHeight(52)
        self.onboarding_guide_start.setCursor(Qt.PointingHandCursor)
        self.onboarding_guide_start.clicked.connect(self.complete_onboarding)
        onboarding_guide_layout.addWidget(self.onboarding_guide_title)
        onboarding_guide_layout.addWidget(self.onboarding_guide_hint)
        onboarding_guide_layout.addStretch(1)
        onboarding_guide_layout.addWidget(self.onboarding_guide_start)
        self.launch_choice_stack.addWidget(self.onboarding_guide_page)

        self.drawer = DrawerFrame("settingsDrawer")
        self.drawer.setParent(self)
        self.drawer.setFixedWidth(DRAWER_WIDTH)
        self.drawer_opacity = QGraphicsOpacityEffect(self.drawer)
        self.drawer_opacity.setOpacity(1.0)
        drawer_shell_layout = QVBoxLayout(self.drawer)
        drawer_shell_layout.setContentsMargins(0, 0, 0, 0)
        drawer_shell_layout.setSpacing(0)

        self.drawer_scroll = QScrollArea()
        self.drawer_scroll.setObjectName("drawerScroll")
        self.drawer_scroll.setFrameShape(QFrame.NoFrame)
        self.drawer_scroll.setWidgetResizable(True)
        self.drawer_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.drawer_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.drawer_scroll.setViewportMargins(0, 0, 10, 0)

        self.drawer_content = QWidget()
        self.drawer_content.setObjectName("drawerContent")
        self.drawer_scroll.setWidget(self.drawer_content)
        drawer_shell_layout.addWidget(self.drawer_scroll)

        drawer_layout = QVBoxLayout(self.drawer_content)
        drawer_layout.setContentsMargins(24, 24, 24, 24)
        drawer_layout.setSpacing(14)

        drawer_title = QLabel("Settings")
        drawer_title.setObjectName("drawerTitle")
        drawer_layout.addWidget(drawer_title)

        self.comfy_root_label = QLabel("ComfyUI portable folder")
        self.comfy_root_label.setObjectName("drawerLabel")
        self.comfy_root_input = QLineEdit()
        self.comfy_root_input.setObjectName("drawerInput")
        self.comfy_root_input.setPlaceholderText("Auto-detect or choose folder")
        self.comfy_root_input.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.comfy_root_input.setMinimumHeight(44)
        self.comfy_root_input.textEdited.connect(self.mark_settings_dirty)
        self.comfy_root_pick_button = QPushButton("Выбрать папку")
        self.comfy_root_pick_button.setObjectName("saveSettingsButton")
        self.comfy_root_pick_button.setMinimumHeight(44)
        self.comfy_root_pick_button.setCursor(Qt.PointingHandCursor)
        self.comfy_root_pick_button.clicked.connect(self.pick_comfy_root)

        self.subdomain_label = QLabel("LocalTunnel subdomain")
        self.subdomain_label.setObjectName("drawerLabel")
        self.subdomain_input = QLineEdit()
        self.subdomain_input.setObjectName("drawerInput")
        self.subdomain_input.setPlaceholderText("comfylocal5618")
        self.subdomain_input.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.subdomain_input.setMinimumHeight(44)
        self.subdomain_input.textEdited.connect(self.mark_settings_dirty)

        self.port_label = QLabel("Port")
        self.port_label.setObjectName("drawerLabel")
        self.port_input = QLineEdit()
        self.port_input.setObjectName("drawerInput")
        self.port_input.setReadOnly(True)
        self.port_input.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.port_input.setMinimumHeight(44)

        self.launch_mode_label = QLabel("Comfy launch mode")
        self.launch_mode_label.setObjectName("drawerLabel")
        self.launch_mode_segment = QFrame()
        self.launch_mode_segment.setObjectName("themeSegment")
        self.launch_mode_segment.setFixedHeight(64)
        launch_mode_layout = QHBoxLayout(self.launch_mode_segment)
        launch_mode_layout.setContentsMargins(4, 4, 4, 4)
        launch_mode_layout.setSpacing(6)

        self.launch_mode_buttons: dict[str, QPushButton] = {}
        self.launch_mode_group = QButtonGroup(self)
        self.launch_mode_group.setExclusive(True)
        for mode_key in ("fp16", "fp8", "bf16", "cpu"):
            button = QPushButton(COMFY_LAUNCH_MODES[mode_key]["title"])
            button.setCheckable(True)
            button.setObjectName("segmentButton")
            button.setCursor(Qt.PointingHandCursor)
            button.setFixedHeight(40)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.clicked.connect(partial(self.set_launch_mode, mode_key))
            self.launch_mode_group.addButton(button)
            self.launch_mode_buttons[mode_key] = button
            launch_mode_layout.addWidget(button)

        self.extra_launch_args_label = QLabel("Extra Comfy args")
        self.extra_launch_args_label.setObjectName("drawerLabel")
        self.extra_launch_args_input = QLineEdit()
        self.extra_launch_args_input.setObjectName("drawerInput")
        self.extra_launch_args_input.setPlaceholderText("--disable-dynamic-vram")
        self.extra_launch_args_input.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.extra_launch_args_input.setMinimumHeight(44)
        self.extra_launch_args_input.setToolTip("Дополнительные аргументы запуска ComfyUI. По умолчанию стоит --disable-dynamic-vram.")
        self.extra_launch_args_input.textEdited.connect(self.mark_settings_dirty)

        self.theme_label = QLabel("Theme")
        self.theme_label.setObjectName("drawerLabel")
        self.theme_segment = QFrame()
        self.theme_segment.setObjectName("themeSegment")
        self.theme_segment.setFixedHeight(64)
        theme_segment_layout = QHBoxLayout(self.theme_segment)
        theme_segment_layout.setContentsMargins(4, 4, 4, 4)
        theme_segment_layout.setSpacing(6)

        self.light_button = QPushButton("Light")
        self.dark_button = QPushButton("Dark")
        for button in (self.light_button, self.dark_button):
            button.setCheckable(True)
            button.setObjectName("segmentButton")
            button.setCursor(Qt.PointingHandCursor)
            button.setFixedHeight(40)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            theme_segment_layout.addWidget(button)

        self.theme_group = QButtonGroup(self)
        self.theme_group.setExclusive(True)
        self.theme_group.addButton(self.light_button)
        self.theme_group.addButton(self.dark_button)
        self.light_button.clicked.connect(lambda: self.set_theme_mode("light"))
        self.dark_button.clicked.connect(lambda: self.set_theme_mode("dark"))

        self.auto_copy_row = ToggleRow("Auto-copy main link", "Когда основной туннель готов, ссылка сама улетает в буфер обмена.")
        self.auto_restart_row = ToggleRow("Auto-restart tunnel", "Если главный туннель падает, приложение поднимает его заново без ручного клика.")
        self.start_on_boot_row = ToggleRow("Start with Windows", "После входа в Windows приложение само откроется и поднимет ComfyUI с основным портом.")
        self.auto_copy_toggle = self.auto_copy_row.toggle
        self.auto_restart_toggle = self.auto_restart_row.toggle
        self.start_on_boot_toggle = self.start_on_boot_row.toggle
        for toggle in (
            self.auto_copy_toggle,
            self.auto_restart_toggle,
            self.start_on_boot_toggle,
        ):
            toggle.toggled.connect(self.mark_settings_dirty)

        self.save_settings_button = QPushButton("Save settings")
        self.save_settings_button.setObjectName("saveSettingsButton")
        self.save_settings_button.setCursor(Qt.PointingHandCursor)
        self.save_settings_button.clicked.connect(self.save_settings)

        drawer_layout.addWidget(self.comfy_root_label)
        drawer_layout.addWidget(self.comfy_root_input)
        drawer_layout.addWidget(self.comfy_root_pick_button)
        drawer_layout.addWidget(self.subdomain_label)
        drawer_layout.addWidget(self.subdomain_input)
        drawer_layout.addWidget(self.port_label)
        drawer_layout.addWidget(self.port_input)
        drawer_layout.addWidget(self.launch_mode_label)
        drawer_layout.addWidget(self.launch_mode_segment)
        drawer_layout.addWidget(self.extra_launch_args_label)
        drawer_layout.addWidget(self.extra_launch_args_input)
        drawer_layout.addWidget(self.theme_label)
        drawer_layout.addWidget(self.theme_segment)
        drawer_layout.addWidget(self.auto_copy_row)
        drawer_layout.addWidget(self.auto_restart_row)
        drawer_layout.addWidget(self.start_on_boot_row)
        drawer_layout.addWidget(self.save_settings_button)
        drawer_layout.addItem(QSpacerItem(0, 8, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.log_hint = QLabel("")
        self.log_hint.setObjectName("logHint")
        self.log_hint.setWordWrap(True)
        drawer_layout.addWidget(self.log_hint)

        self.friends_panel = DrawerFrame("friendsDrawer")
        self.friends_panel.setParent(self)
        self.friends_panel.setFixedWidth(FRIENDS_DRAWER_WIDTH)
        self.friends_opacity = QGraphicsOpacityEffect(self.friends_panel)
        self.friends_opacity.setOpacity(1.0)
        friends_shell_layout = QVBoxLayout(self.friends_panel)
        friends_shell_layout.setContentsMargins(0, 0, 0, 0)
        friends_shell_layout.setSpacing(0)

        self.friends_scroll = QScrollArea()
        self.friends_scroll.setObjectName("friendsScroll")
        self.friends_scroll.setFrameShape(QFrame.NoFrame)
        self.friends_scroll.setWidgetResizable(True)
        self.friends_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.friends_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.friends_scroll.setViewportMargins(0, 0, 10, 0)

        self.friends_content = QWidget()
        self.friends_content.setObjectName("friendsContent")
        self.friends_scroll.setWidget(self.friends_content)
        friends_shell_layout.addWidget(self.friends_scroll)

        friends_layout = QVBoxLayout(self.friends_content)
        friends_layout.setContentsMargins(24, 24, 24, 24)
        friends_layout.setSpacing(14)

        self.friends_title = QLabel("Friends")
        self.friends_title.setObjectName("drawerTitle")
        self.friends_subtitle = QLabel("Создай отдельную ссылку для друга, скопируй ее и в любой момент удаляй без мусора.")
        self.friends_subtitle.setObjectName("drawerHint")
        self.friends_subtitle.setWordWrap(True)

        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(8)
        self.friend_status_pill = QLabel("0 / 5 links")
        self.friend_status_pill.setObjectName("friendStatusPill")
        self.friend_subdomain_pill = QLabel("Нет активных ссылок")
        self.friend_subdomain_pill.setObjectName("friendMetaPill")
        self.friend_custom_button = QPushButton("Custom")
        self.friend_custom_button.setObjectName("friendCustomButton")
        self.friend_custom_button.setFixedHeight(38)
        self.friend_custom_button.setCursor(Qt.PointingHandCursor)
        self.friend_custom_button.clicked.connect(self.on_friend_custom_create_clicked)
        badges_layout.addWidget(self.friend_status_pill, 0, Qt.AlignLeft)
        badges_layout.addWidget(self.friend_subdomain_pill, 0, Qt.AlignLeft)
        badges_layout.addWidget(self.friend_custom_button, 0, Qt.AlignLeft)
        badges_layout.addStretch(1)

        self.friend_create_button = QPushButton("Create friend link")
        self.friend_create_button.setObjectName("friendCreateButton")
        self.friend_create_button.setFixedHeight(50)
        self.friend_create_button.setCursor(Qt.PointingHandCursor)
        self.friend_create_button.clicked.connect(self.on_friend_create_clicked)

        self.friend_hint = QLabel("При создании новая ссылка появляется сразу, а маленький индикатор крутится, пока туннель не станет живым.")
        self.friend_hint.setObjectName("drawerHint")
        self.friend_hint.setWordWrap(True)

        self.friend_links_label = QLabel("Friend Links")
        self.friend_links_label.setObjectName("drawerLabel")
        self.friend_links_container = QWidget()
        self.friend_links_container.setObjectName("friendLinksContainer")
        self.friend_links_layout = QVBoxLayout(self.friend_links_container)
        self.friend_links_layout.setContentsMargins(0, 0, 0, 0)
        self.friend_links_layout.setSpacing(12)
        self.friend_empty_label = QLabel("Здесь появятся отдельные ссылки для друзей. Можно создать до 5 штук.")
        self.friend_empty_label.setObjectName("drawerHint")
        self.friend_empty_label.setWordWrap(True)
        self.friend_links_layout.addWidget(self.friend_empty_label)

        friends_layout.addWidget(self.friends_title)
        friends_layout.addWidget(self.friends_subtitle)
        friends_layout.addLayout(badges_layout)
        friends_layout.addWidget(self.friend_create_button)
        friends_layout.addWidget(self.friend_hint)
        friends_layout.addSpacing(6)
        friends_layout.addWidget(self.friend_links_label)
        friends_layout.addWidget(self.friend_links_container)
        friends_layout.addStretch(1)

        self.settings_button.raise_()
        self.friends_button.raise_()
        self.drawer.hide()
        self.friends_panel.hide()
        self.drawer_backdrop.hide()
        self.launch_choice_backdrop.hide()
        self.launch_choice_card.hide()

    def apply_theme(self) -> None:
        if self.applied_theme_name == self.config["theme"]:
            self.update_action_button()
            self.update_friends_button()
            self.update_logs_button()
            return
        self.theme = THEMES[self.config["theme"]]

        self.setStyleSheet(
            f"""
            QWidget {{
                color: {self.theme.text};
                background: transparent;
                font-family: 'Segoe UI Variable Text', 'Segoe UI';
            }}
            QWidget#appRoot {{
                background: {self.theme.app_bg};
            }}
            QWidget#mainContent, QWidget#drawerContent, QWidget#friendsContent, QWidget#friendLinksContainer, QWidget#bottomSpacer, QWidget#logsPage {{
                background: transparent;
            }}
            QLabel {{
                background: transparent;
            }}
            QFrame#topBar, QFrame#statusPanel, QFrame#settingsDrawer, QFrame#friendsDrawer, QFrame#logsHeaderCard, QFrame#logsCard {{
                background: {self.theme.panel_bg};
                border: 1px solid {self.theme.border};
                border-radius: 28px;
            }}
            QFrame#launchChoiceCard {{
                background: {self.theme.panel_bg};
                border: 1px solid {self.theme.border};
                border-radius: 34px;
            }}
            QFrame#heroCard {{
                background: {self.theme.surface};
                border: 1px solid {self.theme.border};
                border-radius: 28px;
            }}
            QWidget#launchChoiceBackdrop {{
                background: transparent;
            }}
            QFrame#statusCard {{
                background: {self.theme.panel_alt};
                border: 1px solid {self.theme.border};
                border-radius: 24px;
            }}
            QFrame#toggleRow {{
                background: transparent;
                border: none;
                border-radius: 0px;
            }}
            QFrame#friendLinkCard {{
                background: {self.theme.panel_alt};
                border: 1px solid {self.theme.border};
                border-radius: 22px;
            }}
            QLabel#titleLabel {{
                font-size: 24px;
                font-weight: 700;
                color: {self.theme.text};
                background: transparent;
            }}
            QLabel#subtitleLabel {{
                font-size: 13px;
                color: {self.theme.muted};
                background: transparent;
            }}
            QLabel#heroTitle {{
                font-size: 28px;
                font-weight: 700;
                color: {self.theme.text};
                background: transparent;
            }}
            QLabel#heroSubtitle, QLabel#sectionSubtitle, QLabel#footerHint, QLabel#logHint, QLabel#drawerHint {{
                font-size: 14px;
                color: {self.theme.muted};
                background: transparent;
            }}
            QLabel#drawerHint {{
                font-size: 12px;
            }}
            QLabel#friendRowTitle {{
                font-size: 14px;
                font-weight: 800;
                color: {self.theme.text};
                background: transparent;
            }}
            QLabel#friendRowStatus {{
                background: transparent;
            }}
            QLabel#friendRowDetail {{
                font-size: 12px;
                color: {self.theme.muted};
                background: transparent;
            }}
            QLabel#sectionTitle {{
                font-size: 20px;
                font-weight: 700;
                color: {self.theme.text};
                background: transparent;
            }}
            QLabel#drawerTitle {{
                font-size: 26px;
                font-weight: 700;
                color: {self.theme.text};
                background: transparent;
            }}
            QLabel#logsTitle {{
                font-size: 24px;
                font-weight: 700;
                color: {self.theme.text};
                background: transparent;
            }}
            QLabel#logsSubtitle {{
                font-size: 13px;
                color: {self.theme.muted};
                background: transparent;
            }}
            QLabel#launchChoiceTitle {{
                font-size: 34px;
                font-weight: 800;
                color: {self.theme.text};
                background: transparent;
            }}
            QLabel#launchChoiceSubtitle {{
                font-size: 18px;
                color: {self.theme.muted};
                background: transparent;
            }}
            QLabel#drawerLabel {{
                font-size: 13px;
                font-weight: 700;
                color: {self.theme.text};
                background: transparent;
            }}
            QLabel#logsStatusPill {{
                background: {self.theme.surface_alt};
                color: {self.theme.text};
                border: 1px solid {self.theme.border};
                border-radius: 16px;
                padding: 9px 14px;
                font-size: 12px;
                font-weight: 800;
            }}
            QLabel#statusTitle {{
                font-size: 13px;
                font-weight: 700;
                color: {self.theme.muted};
                background: transparent;
            }}
            QLabel#statusValue {{
                font-size: 28px;
                font-weight: 800;
                color: {self.theme.text};
                background: transparent;
            }}
            QLabel#statusDetail {{
                font-size: 13px;
                color: {self.theme.muted};
                background: transparent;
            }}
            QLineEdit#linkField {{
                background: transparent;
                border: none;
                font-size: 27px;
                font-weight: 700;
                color: {self.theme.text};
                padding: 0px;
                selection-background-color: {self.theme.blue};
            }}
            QLineEdit#friendLinkField {{
                background: {self.theme.surface};
                border: 1px solid {self.theme.border};
                border-radius: 18px;
                padding: 10px 14px;
                font-size: 14px;
                font-weight: 700;
                color: {self.theme.text};
                selection-background-color: {self.theme.blue};
            }}
            QFrame#linkShell {{
                background: {self.theme.panel_alt};
                border: 1px solid {self.theme.border};
                border-radius: 30px;
            }}
            QLabel#friendStatusPill, QLabel#friendMetaPill {{
                border-radius: 15px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: 700;
                background: transparent;
            }}
            QPushButton#gearButton, QPushButton#copyButton, QPushButton#refreshButton, QPushButton#saveSettingsButton, QPushButton#friendsButton, QPushButton#friendCustomButton, QPushButton#installButton, QPushButton#logsBackButton, QPushButton#logsButton, QPushButton#githubBrandButton {{
                border: none;
                border-radius: 20px;
                padding: 12px 18px;
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton#telegramBrandButton, QPushButton#githubBrandButton {{
                background: transparent;
                border: none;
                padding: 0px;
            }}
            QPushButton#segmentButton {{
                border: none;
                border-radius: 18px;
                min-height: 44px;
                padding: 0px 14px;
                font-size: 15px;
                font-weight: 700;
            }}
            QPushButton#gearButton, QPushButton#copyButton, QPushButton#refreshButton, QPushButton#githubBrandButton {{
                padding: 0px;
            }}
            QPushButton#gearButton, QPushButton#copyButton, QPushButton#refreshButton, QPushButton#friendsButton, QPushButton#friendCustomButton, QPushButton#logsBackButton, QPushButton#logsButton {{
                background: {self.theme.soft_btn};
                color: {self.theme.text};
                border: 1px solid {self.theme.border};
            }}
            QPushButton#gearButton:hover, QPushButton#copyButton:hover, QPushButton#refreshButton:hover, QPushButton#friendsButton:hover, QPushButton#friendCustomButton:hover, QPushButton#logsBackButton:hover, QPushButton#logsButton:hover {{
                background: {self.theme.soft_btn_hover};
            }}
            QPushButton#installButton {{
                background: {self.theme.soft_btn};
                color: {self.theme.text};
                border: 1px solid {self.theme.border};
                border-radius: 18px;
                padding: 0px;
            }}
            QPushButton#installButton:hover {{
                background: {self.theme.soft_btn_hover};
            }}
            QLabel#installBadge {{
                background: {self.theme.red};
                color: white;
                border: 2px solid {self.theme.panel_bg};
                border-radius: 8px;
                font-size: 11px;
                font-weight: 900;
                padding: 0px;
            }}
            QPushButton#friendCustomButton {{
                padding: 8px 14px;
                font-size: 12px;
                font-weight: 800;
                border-radius: 15px;
                min-width: 88px;
            }}
            QFrame#updateBanner {{
                background: {self.theme.panel_bg};
                border: 1px solid {self.theme.border};
                border-radius: 24px;
            }}
            QLabel#updateBannerTitle {{
                color: {self.theme.text};
                font-size: 15px;
                font-weight: 800;
            }}
            QLabel#updateBannerSubtitle {{
                color: {self.theme.muted};
                font-size: 12px;
            }}
            QPushButton#updateBannerClose {{
                background: {self.theme.soft_btn};
                color: {self.theme.text};
                border: 1px solid {self.theme.border};
                border-radius: 13px;
                padding: 0px;
                font-size: 16px;
                font-weight: 800;
            }}
            QPushButton#updateBannerClose:hover {{
                background: {self.theme.soft_btn_hover};
            }}
            QPushButton#updateBannerPrimaryButton, QPushButton#updateBannerSecondaryButton {{
                min-height: 38px;
                border-radius: 16px;
                padding: 0px 16px;
                font-size: 13px;
                font-weight: 800;
            }}
            QPushButton#updateBannerPrimaryButton {{
                background: {self.theme.blue};
                color: white;
                border: none;
            }}
            QPushButton#updateBannerPrimaryButton:hover {{
                background: {self.theme.blue_hover};
            }}
            QPushButton#updateBannerSecondaryButton {{
                background: {self.theme.soft_btn};
                color: {self.theme.text};
                border: 1px solid {self.theme.border};
            }}
            QPushButton#updateBannerSecondaryButton:hover {{
                background: {self.theme.soft_btn_hover};
            }}
            QPushButton#friendMiniDeleteButton {{
                background: {self.theme.red};
                color: white;
                border: none;
                border-radius: 16px;
                padding: 0px;
            }}
            QPushButton#friendMiniDeleteButton:hover {{
                background: #e54858;
            }}
            QPushButton#startButton {{
                border: none;
                border-radius: 24px;
                padding: 14px 22px;
                font-size: 16px;
                font-weight: 800;
                color: white;
            }}
            QPushButton#saveSettingsButton {{
                background: {self.theme.blue};
                color: white;
                border: none;
            }}
            QLabel#launchChoiceStats {{
                background: {self.theme.panel_alt};
                border: 1px solid {self.theme.border};
                border-radius: 18px;
                color: {self.theme.text};
                padding: 12px 14px;
                font-size: 13px;
                font-weight: 600;
            }}
            QLabel#launchChoiceStepHint {{
                color: {self.theme.muted};
                font-size: 13px;
            }}
            QLabel#launchChoiceError {{
                color: {self.theme.red};
                font-size: 12px;
                font-weight: 700;
            }}
            QLineEdit#launchChoiceInput {{
                background: {self.theme.panel_alt};
                border: 2px solid {self.theme.border};
                border-radius: 18px;
                padding: 12px 14px;
                font-size: 15px;
                font-weight: 700;
                color: {self.theme.text};
                selection-background-color: {self.theme.blue};
            }}
            QPushButton#launchChoiceCloseButton {{
                background: {self.theme.soft_btn};
                color: {self.theme.text};
                border: 1px solid {self.theme.border};
                border-radius: 17px;
                padding: 0px;
                font-size: 18px;
                font-weight: 800;
            }}
            QPushButton#launchChoiceCloseButton:hover {{
                background: {self.theme.soft_btn_hover};
            }}
            QPushButton#launchChoicePrimaryButton, QPushButton#launchChoiceSecondaryButton, QPushButton#launchChoiceContinueButton, QPushButton#launchChoiceSuccessButton, QPushButton#launchChoiceModeGreenButton, QPushButton#launchChoiceModeRedButton {{
                min-height: 54px;
                border-radius: 22px;
                font-size: 16px;
                font-weight: 800;
                padding: 0px 20px;
            }}
            QPushButton#launchChoicePrimaryButton {{
                background: {self.theme.blue};
                color: white;
                border: none;
            }}
            QPushButton#launchChoicePrimaryButton:hover {{
                background: {self.theme.blue_hover};
            }}
            QPushButton#launchChoiceSecondaryButton {{
                background: {self.theme.soft_btn};
                color: {self.theme.text};
                border: 1px solid {self.theme.border};
            }}
            QPushButton#launchChoiceSecondaryButton:hover {{
                background: {self.theme.soft_btn_hover};
            }}
            QPushButton#launchChoiceContinueButton {{
                background: {self.theme.blue};
                color: white;
                border: none;
            }}
            QPushButton#launchChoiceContinueButton:hover {{
                background: {self.theme.blue_hover};
            }}
            QPushButton#launchChoiceSuccessButton {{
                background: {self.theme.green};
                color: white;
                border: none;
            }}
            QPushButton#launchChoiceSuccessButton:hover {{
                background: #159447;
            }}
            QPushButton#launchChoiceModeGreenButton {{
                background: {self.theme.green};
                color: white;
                border: none;
            }}
            QPushButton#launchChoiceModeRedButton {{
                background: {self.theme.red};
                color: white;
                border: none;
            }}
            QPushButton#saveSettingsButton:hover, QPushButton#friendCreateButton:hover {{
                background: {self.theme.blue_hover};
            }}
            QPushButton#friendCreateButton {{
                background: {self.theme.blue};
                color: white;
                border: none;
                border-radius: 20px;
                padding: 14px 18px;
                font-size: 15px;
                font-weight: 800;
            }}
            QProgressBar#launchProgress {{
                background: {self.theme.panel_alt};
                border: none;
                border-radius: 999px;
            }}
            QProgressBar#launchProgress::chunk {{
                background: {self.theme.blue};
                border-radius: 999px;
            }}
            QLineEdit#drawerInput {{
                background: {self.theme.panel_alt};
                border: 1px solid {self.theme.border};
                border-radius: 18px;
                padding: 12px 14px;
                font-size: 14px;
                color: {self.theme.text};
            }}
            QPlainTextEdit#logsViewer {{
                background: {self.theme.surface_alt};
                color: {self.theme.text};
                border: 1px solid {self.theme.border};
                border-radius: 22px;
                padding: 14px;
                selection-background-color: {self.theme.blue};
                font-family: 'Cascadia Mono', 'Consolas';
                font-size: 12px;
            }}
            QPlainTextEdit#logsViewer QScrollBar:vertical, QPlainTextEdit#logsViewer QScrollBar:horizontal {{
                background: transparent;
                border: none;
                margin: 8px;
            }}
            QPlainTextEdit#logsViewer QScrollBar:vertical {{
                width: 10px;
            }}
            QPlainTextEdit#logsViewer QScrollBar:horizontal {{
                height: 10px;
            }}
            QPlainTextEdit#logsViewer QScrollBar::handle:vertical, QPlainTextEdit#logsViewer QScrollBar::handle:horizontal {{
                background: {self.theme.border};
                border-radius: 5px;
                min-width: 36px;
                min-height: 36px;
            }}
            QPlainTextEdit#logsViewer QScrollBar::handle:vertical:hover, QPlainTextEdit#logsViewer QScrollBar::handle:horizontal:hover {{
                background: {self.theme.muted};
            }}
            QPlainTextEdit#logsViewer QScrollBar::add-line:vertical, QPlainTextEdit#logsViewer QScrollBar::sub-line:vertical,
            QPlainTextEdit#logsViewer QScrollBar::add-line:horizontal, QPlainTextEdit#logsViewer QScrollBar::sub-line:horizontal,
            QPlainTextEdit#logsViewer QScrollBar::add-page:vertical, QPlainTextEdit#logsViewer QScrollBar::sub-page:vertical,
            QPlainTextEdit#logsViewer QScrollBar::add-page:horizontal, QPlainTextEdit#logsViewer QScrollBar::sub-page:horizontal {{
                background: transparent;
                border: none;
                width: 0px;
                height: 0px;
            }}
            QFrame#themeSegment {{
                background: {self.theme.panel_alt};
                border: 1px solid {self.theme.border};
                border-radius: 22px;
                min-height: 64px;
            }}
            QScrollArea#mainScroll, QScrollArea#drawerScroll, QScrollArea#friendsScroll {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 8px 2px;
            }}
            QScrollArea#drawerScroll QScrollBar:vertical, QScrollArea#friendsScroll QScrollBar:vertical {{
                width: 6px;
                margin: 14px 6px 14px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.theme.border};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
                border: none;
                height: 0px;
            }}
            QProgressBar#friendMiniLoader {{
                background: {self.theme.surface_alt};
                border: none;
                border-radius: 999px;
            }}
            QProgressBar#friendMiniLoader::chunk {{
                background: {self.theme.blue};
                border-radius: 999px;
            }}
            QLabel#toast {{
                background: {self.theme.blue};
                color: white;
                border-radius: 18px;
                padding: 10px 18px;
                font-size: 13px;
                font-weight: 700;
            }}
            QWidget#drawerBackdrop {{
                background: transparent;
            }}
            """
        )
        self.applied_theme_name = self.config["theme"]
        self.action_visual_state = ""
        self.friends_visual_state = ""
        self.install_visual_state = ""
        self.update_button_icons()
        self.onboarding_install_section.apply_theme(self.theme)
        for row in self.onboarding_install_rows.values():
            row.apply_theme(self.theme)
        self.update_onboarding_mode_buttons()
        self.refresh_onboarding_subdomain_state()
        self.update_segment_buttons()
        self.update_action_button()
        self.update_friends_button()
        self.update_logs_button()
        self.update_install_button()

    def update_segment_buttons(self) -> None:
        def apply_segment_group(active_value: str, buttons: list[tuple[QPushButton, str]]) -> None:
            for button, value in buttons:
                if value == active_value:
                    button.setStyleSheet(
                        f"background: {self.theme.blue}; color: white; border: none; border-radius: 16px; padding: 0px 14px; font-weight: 700;"
                    )
                    button.setChecked(True)
                else:
                    button.setStyleSheet(
                        f"background: {self.theme.soft_btn}; color: {self.theme.text}; border: 1px solid {self.theme.border}; "
                        "border-radius: 16px; padding: 0px 14px; font-weight: 700;"
                    )
                    button.setChecked(False)

        apply_segment_group(self.config["theme"], [(self.light_button, "light"), (self.dark_button, "dark")])
        apply_segment_group(
            normalize_launch_mode(self.config.get("launch_mode", DEFAULT_LAUNCH_MODE)),
            [(button, mode) for mode, button in self.launch_mode_buttons.items()],
        )

    def update_button_icons(self) -> None:
        icon_color = self.theme.text
        copy_icon = build_icon_pixmap("copy", icon_color, 24)
        delete_icon = build_icon_pixmap("close", "#ffffff", 16)
        install_status = setup_status_snapshot() or {"comfy_ready": True, "manager_ready": True, "models": [], "nodes": []}
        install_icon_color = "#ffffff" if (self.install_setup_inflight or comfy_setup_has_missing(install_status)) else self.theme.text
        telegram_asset = resolve_asset_path("telegram_brand.png")
        settings_asset = resolve_asset_path("settings_brand.png")
        github_asset = resolve_asset_path("github_brand_dark.png" if self.config.get("theme") == "dark" else "github_brand_light.png")
        if settings_asset.exists():
            self.settings_button.setIcon(QIcon(str(settings_asset)))
        else:
            self.settings_button.setIcon(build_icon_pixmap("settings", icon_color, 26))
        self.copy_button.setIcon(copy_icon)
        self.refresh_button.setIcon(build_icon_pixmap("refresh", icon_color, 20))
        self.install_button.setIcon(build_icon_pixmap("install", install_icon_color, 26))
        self.logs_button.setIcon(build_icon_pixmap("logs", icon_color, 20))
        self.logs_back_button.setIcon(build_icon_pixmap("back", icon_color, 18))
        if self.setup_page_widget is not None:
            self.setup_page_widget.back_button.setIcon(build_icon_pixmap("back", icon_color, 18))
        if telegram_asset.exists():
            self.telegram_brand_button.setIcon(QIcon(str(telegram_asset)))
        else:
            self.telegram_brand_button.setIcon(build_icon_pixmap("telegram", "#ffffff", 28))
        if github_asset.exists():
            self.github_brand_button.setIcon(QIcon(str(github_asset)))
        else:
            self.github_brand_button.setIcon(build_icon_pixmap("logs", icon_color, 24))
        for row in self.friend_rows.values():
            row.apply_theme(self.theme, copy_icon, delete_icon)

    def update_friends_button(self, snap: dict | None = None) -> None:
        snap = snap or self.current_snapshot()
        if self.friends_open:
            state = "open"
            style = (
                f"background: {self.theme.blue}; color: white; border: none; border-radius: 20px; "
                f"padding: 12px 18px; font-size: 14px; font-weight: 700;"
            )
        elif snap["friend_count"]:
            state = "live"
            style = (
                f"background: {self.theme.surface_alt}; color: {self.theme.text}; border: 1px solid {self.theme.blue}; "
                f"border-radius: 20px; padding: 12px 18px; font-size: 14px; font-weight: 700;"
            )
        else:
            state = "idle"
            style = ""
        if self.friends_visual_state != state:
            self.friends_button.setStyleSheet(style)
            self.friends_visual_state = state
        button_text = f"Friends {snap['friend_count']}" if snap["friend_count"] else "Friends"
        if self.friends_button.text() != button_text:
            self.friends_button.setText(button_text)

    def update_install_button(self) -> None:
        status = setup_status_snapshot() or {"comfy_ready": True, "manager_ready": True, "models": [], "nodes": []}
        missing = comfy_setup_has_missing(status)
        if self.setup_view_open:
            state = "open"
            style = (
                f"background: {self.theme.blue}; color: white; border: none; "
                "border-radius: 18px; padding: 0px;"
            )
            tooltip = "Сейчас открыта страница Comfy setup"
        elif self.install_setup_inflight:
            state = "busy"
            style = (
                f"background: {self.theme.blue}; color: white; border: none; "
                "border-radius: 18px; padding: 0px;"
            )
            tooltip = "Установка идет прямо сейчас"
        elif missing:
            state = "missing"
            style = (
                f"background: {self.theme.red}; color: white; border: none; "
                "border-radius: 18px; padding: 0px;"
            )
            tooltip = "Не все готово. Нажми, чтобы установить недостающее"
        else:
            state = "ready"
            style = (
                f"background: {self.theme.soft_btn}; color: {self.theme.text}; border: 1px solid {self.theme.border}; "
                "border-radius: 18px; padding: 0px;"
            )
            tooltip = "Comfy setup уже собран. Нажми, чтобы открыть help"
        if self.install_visual_state != state:
            self.install_button.setStyleSheet(style)
            self.update_button_icons()
            self.install_visual_state = state
        if self.install_button.toolTip() != tooltip:
            self.install_button.setToolTip(tooltip)
        self.install_badge.setVisible(missing and not self.install_setup_inflight)

    def rebuild_friend_rows(self, entries: list[dict]) -> None:
        active_ids = {entry["id"] for entry in entries}
        for link_id in list(self.friend_rows):
            if link_id in active_ids:
                continue
            row = self.friend_rows.pop(link_id)
            self.friend_links_layout.removeWidget(row)
            row.deleteLater()

        copy_icon = build_icon_pixmap("copy", self.theme.text, 24)
        delete_icon = build_icon_pixmap("close", "#ffffff", 16)
        for entry in entries:
            row = self.friend_rows.get(entry["id"])
            if row is None:
                row = FriendLinkRow(entry["id"])
                row.copy_requested.connect(self.copy_friend_link_by_id)
                row.delete_requested.connect(self.request_friend_delete)
                self.friend_rows[entry["id"]] = row
                self.friend_links_layout.addWidget(row)
            row.apply_theme(self.theme, copy_icon, delete_icon)
            row.set_data(entry)

        self.friend_empty_label.setVisible(not entries)

    def update_friend_panel_state(self, snap: dict) -> None:
        entries = snap.get("friend_links", [])
        self.rebuild_friend_rows(entries)

        total_count = snap.get("friend_count", len(entries))
        live_count = snap.get("friend_active_count", 0)
        status_text = f"{total_count} / {MAX_FRIEND_LINKS} links"
        live_text = f"{live_count} активн." if live_count else "Нет активных ссылок"
        if self.friend_status_pill.text() != status_text:
            self.friend_status_pill.setText(status_text)
        if self.friend_subdomain_pill.text() != live_text:
            self.friend_subdomain_pill.setText(live_text)
        self.friend_status_pill.setStyleSheet(
            f"background: {self.theme.surface_alt}; color: {self.theme.text}; border: 1px solid {self.theme.border}; "
            "border-radius: 15px; padding: 8px 12px; font-size: 12px; font-weight: 700;"
        )
        self.friend_subdomain_pill.setStyleSheet(
            f"background: {self.theme.soft_btn}; color: {self.theme.muted}; border: 1px solid {self.theme.border}; "
            "border-radius: 15px; padding: 8px 12px; font-size: 12px; font-weight: 700;"
        )

        can_create = (not self.busy) and total_count < MAX_FRIEND_LINKS
        self.friend_create_button.setEnabled(can_create)
        self.friend_custom_button.setEnabled(can_create)
        create_text = "Create friend link" if total_count < MAX_FRIEND_LINKS else "Friend slots full"
        if self.friend_create_button.text() != create_text:
            self.friend_create_button.setText(create_text)

    def mark_settings_dirty(self, *_args) -> None:
        if self.syncing_controls:
            return
        self.settings_dirty = True

    def clear_settings_dirty(self) -> None:
        self.settings_dirty = False

    def load_controls_from_config(self, force: bool = False) -> None:
        sync_values = force or not (self.drawer_open and self.settings_dirty)
        self.syncing_controls = True
        try:
            if sync_values:
                comfy_root_text = self.config.get("comfy_root", "")
                if not self.comfy_root_input.hasFocus() and self.comfy_root_input.text() != comfy_root_text:
                    self.comfy_root_input.setText(comfy_root_text)
                self.comfy_root_input.setToolTip(comfy_root_text)
                if not self.comfy_root_input.hasFocus():
                    self.comfy_root_input.setCursorPosition(0)

                if not self.subdomain_input.hasFocus() and self.subdomain_input.text() != self.config["subdomain"]:
                    self.subdomain_input.setText(self.config["subdomain"])
                self.subdomain_input.setToolTip(self.config["subdomain"])
                if not self.subdomain_input.hasFocus():
                    self.subdomain_input.setCursorPosition(0)

                if self.port_input.text() != str(self.config["port"]):
                    self.port_input.setText(str(self.config["port"]))
                self.port_input.setCursorPosition(0)

                active_launch_mode = normalize_launch_mode(self.config.get("launch_mode", DEFAULT_LAUNCH_MODE))
                for mode_key, button in self.launch_mode_buttons.items():
                    should_check = mode_key == active_launch_mode
                    if button.isChecked() != should_check:
                        button.setChecked(should_check)

                extra_args_text = normalize_extra_launch_args(self.config.get("extra_launch_args", ""))
                if not self.extra_launch_args_input.hasFocus() and self.extra_launch_args_input.text() != extra_args_text:
                    self.extra_launch_args_input.setText(extra_args_text)
                self.extra_launch_args_input.setToolTip(extra_args_text or "Дополнительные аргументы запуска ComfyUI")
                if not self.extra_launch_args_input.hasFocus():
                    self.extra_launch_args_input.setCursorPosition(0)

                if self.auto_copy_toggle.isChecked() != self.config.get("auto_copy_url", True):
                    self.auto_copy_toggle.setChecked(self.config.get("auto_copy_url", True))
                if self.auto_restart_toggle.isChecked() != self.config.get("auto_restart_tunnel", True):
                    self.auto_restart_toggle.setChecked(self.config.get("auto_restart_tunnel", True))
                if self.start_on_boot_toggle.isChecked() != self.config.get("start_on_boot", False):
                    self.start_on_boot_toggle.setChecked(self.config.get("start_on_boot", False))
        finally:
            self.syncing_controls = False

        for toggle_row in (self.auto_copy_row, self.auto_restart_row, self.start_on_boot_row):
            toggle_row.apply_theme(self.theme)
        self.update_segment_buttons()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self.drawer_backdrop.setGeometry(0, 0, self.width(), self.height())
        self.position_overlays()
        self.place_launch_choice_overlay()
        self.place_toast()
        self.place_update_banner()

    def place_toast(self) -> None:
        self.toast.adjustSize()
        self.toast.move((self.width() - self.toast.width()) // 2, self.height() - self.toast.height() - 24)

    def place_update_banner(self) -> None:
        if not self.update_banner.isVisible():
            return
        banner_width = min(380, max(280, self.width() // 3))
        self.update_banner.resize(banner_width, self.update_banner.sizeHint().height())
        margin = 26
        self.update_banner.move(self.width() - self.update_banner.width() - margin, self.height() - self.update_banner.height() - margin)
        self.update_banner.raise_()

    def backdrop_target_alpha(self) -> float:
        return 88.0 if self.config.get("theme") == "dark" else 28.0

    def left_drawer_target(self, opened: bool) -> QPoint:
        return QPoint(20 if opened else -(DRAWER_WIDTH + 18), 20)

    def right_drawer_target(self, opened: bool) -> QPoint:
        return QPoint(self.width() - FRIENDS_DRAWER_WIDTH - 20 if opened else self.width() + 18, 20)

    def position_overlays(self) -> None:
        top_margin = 20
        self.drawer.resize(DRAWER_WIDTH, self.height() - top_margin * 2)
        self.friends_panel.resize(FRIENDS_DRAWER_WIDTH, self.height() - top_margin * 2)
        self.drawer.move(self.left_drawer_target(True) if self.drawer_open else self.left_drawer_target(False))
        self.friends_panel.move(self.right_drawer_target(True) if self.friends_open else self.right_drawer_target(False))
        if self.drawer_fade_anim.state() != QAbstractAnimation.Running:
            self.drawer.setVisible(self.drawer_open)
        if self.friends_fade_anim.state() != QAbstractAnimation.Running:
            self.friends_panel.setVisible(self.friends_open)

    def overlays_open(self) -> bool:
        return self.drawer_open or self.friends_open

    def launch_choice_backdrop_target_alpha(self) -> float:
        return 126.0 if self.config.get("theme") == "dark" else 54.0

    def launch_choice_target_pos(self, opened: bool) -> QPoint:
        card_width = self.launch_choice_card.width()
        card_height = self.launch_choice_card.height()
        base_x = max(32, (self.width() - card_width) // 2)
        base_y = max(34, (self.height() - card_height) // 2 - 12)
        if opened:
            return QPoint(base_x, base_y)
        return QPoint(base_x, max(18, base_y + 22))

    def place_launch_choice_overlay(self) -> None:
        self.launch_choice_backdrop.setGeometry(0, 0, self.width(), self.height())
        card_width = min(820, max(640, self.width() - 180))
        card_height = min(650, max(520, self.height() - 120))
        self.launch_choice_card.resize(card_width, card_height)
        if self.launch_choice_anim.state() != QAbstractAnimation.Running:
            self.launch_choice_card.move(self.launch_choice_target_pos(self.launch_choice_open))
        if self.launch_choice_fade_anim.state() != QAbstractAnimation.Running:
            self.launch_choice_card.setVisible(self.launch_choice_open)

    def ensure_launch_choice_stack(self) -> None:
        if not (self.launch_choice_open or self.launch_choice_card.isVisible() or self.launch_choice_backdrop.isVisible()):
            return
        self.launch_choice_backdrop.raise_()
        self.launch_choice_card.raise_()
        if self.update_banner.isVisible():
            self.update_banner.raise_()
        if self.toast.isVisible():
            self.toast.raise_()

    def update_backdrop_visibility(self) -> None:
        if self.overlays_open():
            self.drawer_backdrop.show()
            self.ensure_overlay_stack()
            self.backdrop_anim.stop()
            self.backdrop_anim.setStartValue(self.drawer_backdrop.alpha)
            self.backdrop_anim.setEndValue(self.backdrop_target_alpha())
            self.backdrop_anim.start()
        else:
            self.backdrop_anim.stop()
            self.backdrop_anim.setStartValue(self.drawer_backdrop.alpha)
            self.backdrop_anim.setEndValue(0.0)
            self.backdrop_anim.start()

    def ensure_overlay_stack(self) -> None:
        if not self.overlays_open():
            self.ensure_launch_choice_stack()
            if self.toast.isVisible():
                self.toast.raise_()
            return
        self.drawer_backdrop.raise_()
        if self.drawer_open:
            self.drawer.raise_()
            self.settings_button.raise_()
        if self.friends_open:
            self.friends_panel.raise_()
            self.friends_button.raise_()
        self.ensure_launch_choice_stack()
        if self.update_banner.isVisible():
            self.update_banner.raise_()
        if self.toast.isVisible():
            self.toast.raise_()

    def set_launch_choice_open(self, opened: bool) -> None:
        if self.launch_choice_open == opened and self.launch_choice_fade_anim.state() != QAbstractAnimation.Running:
            if opened:
                self.ensure_launch_choice_stack()
            return
        self.launch_choice_open = opened
        self.launch_choice_hide_after_anim = False
        self.place_launch_choice_overlay()
        if opened:
            if self.drawer_open:
                self.set_drawer_open(False)
            if self.friends_open:
                self.set_friends_panel_open(False)
            if self.logs_view_open:
                self.set_logs_view_open(False)
            if self.setup_view_open:
                self.set_setup_view_open(False)
            if self.poll_timer.isActive():
                self.launch_choice_paused_poll = True
                self.poll_timer.stop()
            self.launch_choice_backdrop.show()
            self.launch_choice_card.show()
            self.ensure_launch_choice_stack()
        if self.overlay_animation_count == 0 and self.poll_timer.isActive():
            self.poll_timer.stop()
        self.overlay_animation_count += 1
        self.launch_choice_anim.stop()
        self.launch_choice_fade_anim.stop()
        self.launch_choice_backdrop_anim.stop()
        self.launch_choice_anim.setStartValue(self.launch_choice_card.pos())
        self.launch_choice_anim.setEndValue(self.launch_choice_target_pos(opened))
        self.launch_choice_fade_anim.setStartValue(self.launch_choice_opacity.opacity())
        self.launch_choice_fade_anim.setEndValue(1.0 if opened else 0.0)
        self.launch_choice_backdrop_anim.setStartValue(self.launch_choice_backdrop.alpha)
        self.launch_choice_backdrop_anim.setEndValue(self.launch_choice_backdrop_target_alpha() if opened else 0.0)
        self.launch_choice_anim.start()
        self.launch_choice_backdrop_anim.start()
        self.launch_choice_fade_anim.start()

    def on_launch_choice_fade_finished(self) -> None:
        if not self.launch_choice_open and self.launch_choice_opacity.opacity() <= 0.01:
            self.launch_choice_card.hide()
            if self.launch_choice_backdrop.alpha <= 0.5:
                self.launch_choice_backdrop.hide()
        else:
            self.ensure_launch_choice_stack()
        if self.overlay_animation_count > 0:
            self.overlay_animation_count -= 1
        if not self.launch_choice_open and self.launch_choice_paused_poll:
            self.launch_choice_paused_poll = False
            if not self.poll_timer.isActive() and self.overlay_animation_count == 0:
                self.poll_timer.start(POLL_MS)
        elif self.overlay_animation_count == 0 and not self.poll_timer.isActive() and not self.launch_choice_open:
            self.poll_timer.start(POLL_MS)
        self.update_backdrop_visibility()
        self.ensure_launch_choice_stack()

    def set_logs_view_open(self, opened: bool) -> None:
        target_index = 1 if opened else 0
        if self.logs_view_open == opened and self.page_stack.currentIndex() == target_index and self.page_fade_anim.state() != QAbstractAnimation.Running:
            self.update_logs_button()
            self.update_install_button()
            return
        if opened:
            if self.drawer_open:
                self.set_drawer_open(False)
            if self.friends_open:
                self.set_friends_panel_open(False)
            if self.setup_view_open:
                self.setup_view_open = False
        else:
            self.logs_fast_timer.stop()
        self.logs_view_open = opened
        self.pending_page_index = target_index
        self.update_logs_button()
        self.update_install_button()
        self.page_fade_anim.stop()
        self.page_fade_phase = "out"
        self.page_fade_anim.setStartValue(self.page_stack_opacity.opacity())
        self.page_fade_anim.setEndValue(0.0)
        self.page_fade_anim.start()

    def set_setup_view_open(self, opened: bool) -> None:
        target_index = 2 if opened else 0
        if self.setup_view_open == opened and self.page_stack.currentIndex() == target_index and self.page_fade_anim.state() != QAbstractAnimation.Running:
            self.update_install_button()
            return
        if opened:
            if self.drawer_open:
                self.set_drawer_open(False)
            if self.friends_open:
                self.set_friends_panel_open(False)
            if self.logs_view_open:
                self.logs_view_open = False
            if self.setup_page_widget is not None:
                cached_status = setup_status_snapshot()
                if cached_status:
                    self.setup_page_widget.refresh_status(cached_status)
                    self.last_setup_page_refresh_at = time.monotonic()
        self.setup_view_open = opened
        self.pending_page_index = target_index
        self.update_logs_button()
        self.update_install_button()
        self.page_fade_anim.stop()
        self.page_fade_phase = "out"
        self.page_fade_anim.setStartValue(self.page_stack_opacity.opacity())
        self.page_fade_anim.setEndValue(0.0)
        self.page_fade_anim.start()

    def request_setup_status_refresh(self, force_links: bool = False) -> None:
        if self.setup_status_refresh_inflight:
            return
        self.setup_status_refresh_inflight = True
        config_snapshot = dict(self.config)

        def worker() -> None:
            try:
                if force_links:
                    refresh_setup_download_links(config_snapshot)
                status = cached_comfy_setup_status(config_snapshot, force=True)
                try:
                    self.bridge.setup_status_ready.emit(status)
                except RuntimeError:
                    return
            except Exception:
                self.setup_status_refresh_inflight = False

        threading.Thread(target=worker, daemon=True).start()

    def on_setup_status_ready(self, status: dict) -> None:
        self.setup_status_refresh_inflight = False
        self.last_setup_page_refresh_at = time.monotonic()
        if self.setup_page_widget is not None:
            self.setup_page_widget.refresh_status(status)
        if self.launch_choice_open:
            self.refresh_onboarding_install_rows(status)
        self.update_install_button()

    def on_page_fade_finished(self) -> None:
        if self.page_fade_phase == "out":
            if self.pending_page_index is not None:
                self.page_stack.setCurrentIndex(self.pending_page_index)
            self.page_fade_phase = "in"
            self.page_fade_anim.setStartValue(0.0)
            self.page_fade_anim.setEndValue(1.0)
            self.page_fade_anim.start()
            self.update_logs_button()
            return
        self.page_fade_phase = "idle"
        self.pending_page_index = None
        self.update_logs_button()
        self.update_install_button()
        if self.logs_view_open:
            self.refresh_live_logs_fast()
            if not self.logs_fast_timer.isActive():
                self.logs_fast_timer.start(LOG_VIEW_POLL_MS)
        else:
            self.logs_fast_timer.stop()
        if self.setup_view_open:
            self.request_setup_status_refresh(force_links=True)
        self.request_refresh_view(include_logs=False)

    def update_logs_button(self) -> None:
        snap = self.latest_snap or self.current_snapshot()
        button_text = "Logs"
        if self.logs_button.text() != button_text:
            self.logs_button.setText(button_text)
        if snap.get("comfy_active"):
            style = (
                f"background: {self.theme.surface_alt}; color: {self.theme.text}; border: 1px solid {self.theme.blue}; "
                f"border-radius: 20px; padding: 12px 18px; font-size: 14px; font-weight: 700;"
            )
        else:
            style = (
                f"background: {self.theme.soft_btn}; color: {self.theme.text}; border: 1px solid {self.theme.border}; "
                f"border-radius: 20px; padding: 12px 18px; font-size: 14px; font-weight: 700;"
            )
        self.logs_button.setStyleSheet(style)

    def apply_comfy_log_viewer_text(self, viewer_text: str) -> None:
        normalized_text = viewer_text or "Логи ComfyUI появятся здесь после запуска."
        if self.last_comfy_log_full == normalized_text:
            return
        log_scroll = self.logs_viewer.verticalScrollBar()
        stick_to_bottom = log_scroll.value() >= max(0, log_scroll.maximum() - 8)
        self.logs_viewer.setPlainText(normalized_text)
        if stick_to_bottom:
            log_scroll.setValue(log_scroll.maximum())
        self.last_comfy_log_full = normalized_text

    def refresh_live_logs_fast(self) -> None:
        if not self.logs_view_open or self.overlay_animation_count != 0 or self.logs_refresh_inflight:
            return
        self.logs_refresh_inflight = True

        def worker() -> None:
            try:
                viewer_text = combined_comfy_log_text(max_bytes=98304).strip() or "Логи ComfyUI появятся здесь после запуска."
                QTimer.singleShot(0, lambda text=viewer_text: self.on_logs_fast_ready(text))
            except Exception:
                QTimer.singleShot(0, lambda: self.on_logs_fast_ready("Логи ComfyUI появятся здесь после запуска."))

        threading.Thread(target=worker, daemon=True).start()

    def on_logs_fast_ready(self, viewer_text: str) -> None:
        self.logs_refresh_inflight = False
        if not self.logs_view_open:
            return
        self.apply_comfy_log_viewer_text(viewer_text)

    def run_intro_animation(self) -> None:
        return

    def set_drawer_open(self, opened: bool) -> None:
        if opened and self.friends_open:
            self.set_friends_panel_open(False)
        if self.drawer_open == opened:
            if opened:
                self.update_backdrop_visibility()
            return
        self.drawer_open = opened
        self.update_backdrop_visibility()
        self.drawer_anim.stop()
        self.drawer_fade_anim.stop()
        self.drawer_hide_after_anim = False
        target = self.left_drawer_target(True)
        anim_start = QPoint(target.x() - PANEL_SLIDE_OFFSET, target.y())
        if self.drawer_fade_anim.state() != QAbstractAnimation.Running:
            self.overlay_animation_count += 1
            if self.poll_timer.isActive():
                self.poll_timer.stop()
        if opened:
            self.drawer.move(anim_start)
            self.drawer.show()
            self.drawer_opacity.setOpacity(0.0)
            self.drawer_anim.setStartValue(anim_start)
            self.drawer_anim.setEndValue(target)
            self.drawer_fade_anim.setStartValue(0.0)
            self.drawer_fade_anim.setEndValue(1.0)
            self.ensure_overlay_stack()
        else:
            self.drawer_hide_after_anim = True
            self.drawer_anim.setStartValue(self.drawer.pos())
            self.drawer_anim.setEndValue(anim_start)
            self.drawer_fade_anim.setStartValue(self.drawer_opacity.opacity())
            self.drawer_fade_anim.setEndValue(0.0)
        self.drawer_anim.start()
        self.drawer_fade_anim.start()

    def set_friends_panel_open(self, opened: bool) -> None:
        if opened and self.drawer_open:
            self.set_drawer_open(False)
        if self.friends_open == opened:
            if opened:
                self.update_backdrop_visibility()
            return
        self.friends_open = opened
        self.update_backdrop_visibility()
        self.friends_anim.stop()
        self.friends_fade_anim.stop()
        self.friends_hide_after_anim = False
        target = self.right_drawer_target(True)
        anim_start = QPoint(target.x() + PANEL_SLIDE_OFFSET, target.y())
        if self.friends_fade_anim.state() != QAbstractAnimation.Running:
            self.overlay_animation_count += 1
            if self.poll_timer.isActive():
                self.poll_timer.stop()
        if opened:
            self.friends_panel.move(anim_start)
            self.friends_panel.show()
            self.friends_opacity.setOpacity(0.0)
            self.friends_anim.setStartValue(anim_start)
            self.friends_anim.setEndValue(target)
            self.friends_fade_anim.setStartValue(0.0)
            self.friends_fade_anim.setEndValue(1.0)
            self.ensure_overlay_stack()
        else:
            self.friends_hide_after_anim = True
            self.friends_anim.setStartValue(self.friends_panel.pos())
            self.friends_anim.setEndValue(anim_start)
            self.friends_fade_anim.setStartValue(self.friends_opacity.opacity())
            self.friends_fade_anim.setEndValue(0.0)
        self.friends_anim.start()
        self.friends_fade_anim.start()
        self.update_friends_button()

    def on_drawer_fade_finished(self) -> None:
        if self.drawer_hide_after_anim and not self.drawer_open:
            self.drawer.hide()
            self.drawer.move(self.left_drawer_target(False))
            self.drawer_opacity.setOpacity(1.0)
            self.drawer_hide_after_anim = False
        self.on_overlay_animation_finished()

    def on_friends_fade_finished(self) -> None:
        if self.friends_hide_after_anim and not self.friends_open:
            self.friends_panel.hide()
            self.friends_panel.move(self.right_drawer_target(False))
            self.friends_opacity.setOpacity(1.0)
            self.friends_hide_after_anim = False
        self.on_overlay_animation_finished()

    def on_backdrop_animation_finished(self) -> None:
        if not self.overlays_open() and self.drawer_backdrop.alpha <= 0.5:
            self.drawer_backdrop.hide()

    def on_overlay_animation_finished(self) -> None:
        if self.overlay_animation_count > 0:
            self.overlay_animation_count -= 1
        if self.overlay_animation_count == 0 and not self.poll_timer.isActive():
            self.poll_timer.start(POLL_MS)
        self.update_backdrop_visibility()
        self.update_friends_button()

    def toggle_drawer(self) -> None:
        self.set_drawer_open(not self.drawer_open)

    def toggle_friends_panel(self) -> None:
        self.set_friends_panel_open(not self.friends_open)

    def close_overlays(self) -> None:
        self.set_drawer_open(False)
        self.set_friends_panel_open(False)

    def open_telegram_channel(self) -> None:
        QDesktopServices.openUrl(QUrl(TELEGRAM_CHANNEL_URL))

    def open_github_repo(self) -> None:
        QDesktopServices.openUrl(QUrl(GITHUB_REPO_URL))

    def open_github_releases(self) -> None:
        if self.update_banner_kind == "comfy":
            target = str((self.release_info or {}).get("html_url", "") or COMFY_GITHUB_REPO_URL)
        else:
            target = str((self.release_info or {}).get("html_url", "") or GITHUB_RELEASES_URL)
        QDesktopServices.openUrl(QUrl(target))

    def refresh_onboarding_install_rows(self, status: dict) -> None:
        comfy_ready = bool(status.get("comfy_ready"))
        manager_ready = bool(status.get("manager_ready"))
        if "comfy" in self.onboarding_install_rows:
            if comfy_ready and status.get("comfy_update_available"):
                self.onboarding_install_rows["comfy"].set_state(False, str(status.get("comfy_update_message", "") or "Доступно обновление ComfyUI."), "missing")
            else:
                self.onboarding_install_rows["comfy"].set_state(comfy_ready, "Portable найден" if comfy_ready else "Нужно скачать portable ComfyUI")
        if "manager" in self.onboarding_install_rows:
            self.onboarding_install_rows["manager"].set_state(
                manager_ready,
                "Manager уже установлен" if manager_ready else ("Сначала нужен portable ComfyUI" if not comfy_ready else "Будет поставлен в custom_nodes"),
                "ready" if manager_ready else "missing",
            )
        for model in status.get("models", []):
            row = self.onboarding_install_rows.get(f"model:{model['title']}")
            if not row:
                continue
            if model.get("ready"):
                row.set_state(True, "Файл уже на месте.", "ready")
            elif not model.get("download_checked", False):
                row.set_state(False, "Проверяем прямую ссылку на скачивание.", "missing")
            elif not model.get("download_available", True):
                row.set_state(False, str(model.get("download_message", "") or "Сейчас скачать нельзя: ссылка недоступна."), "unavailable")
            elif not comfy_ready:
                row.set_state(False, "Сначала нужен portable ComfyUI.", "missing")
            else:
                row.set_state(False, "Будет скачан и положен в нужную папку.", "missing")
        summary = "Все для Comfy уже готово." if comfy_core_missing_count(status) == 0 else f"Не хватает {comfy_core_missing_count(status)} компонентов для полного setup."
        self.onboarding_install_section.set_summary(summary)
        if not self.install_setup_inflight:
            self.onboarding_install_section.clear_progress()

    def update_onboarding_mode_buttons(self) -> None:
        selected_mode = normalize_launch_mode(self.config.get("launch_mode", DEFAULT_LAUNCH_MODE))
        gpu_selected = selected_mode != "cpu"
        selected_style = "background: #16a34a; color: white; border: none; border-radius: 22px; font-size: 16px; font-weight: 800;"
        unselected_style = f"background: {self.theme.red}; color: white; border: none; border-radius: 22px; font-size: 16px; font-weight: 800;"
        self.onboarding_gpu_button.setStyleSheet(selected_style if gpu_selected else unselected_style)
        self.onboarding_cpu_button.setStyleSheet(selected_style if not gpu_selected else unselected_style)
        self.onboarding_mode_recommend.setText("Рекомендуется: GPU" if gpu_selected else "Выбран CPU режим")

    def refresh_onboarding_subdomain_state(self) -> None:
        current = sanitize_subdomain(self.onboarding_subdomain_input.text())
        valid = is_valid_main_subdomain(current)
        border = "#16a34a" if valid else self.theme.red
        self.onboarding_subdomain_input.setStyleSheet(
            f"background: {self.theme.panel_alt}; border: 2px solid {border}; border-radius: 18px; padding: 12px 14px; font-size: 15px; font-weight: 700; color: {self.theme.text}; selection-background-color: {self.theme.blue};"
        )
        if valid:
            self.onboarding_subdomain_error.setText(f"Будет ссылка: https://{current}.loca.lt")
            self.onboarding_subdomain_error.setStyleSheet(f"color: {self.theme.green}; font-size: 12px; font-weight: 700;")
            self.onboarding_subdomain_continue.setEnabled(True)
            self.onboarding_subdomain_continue.setStyleSheet(
                f"background: {self.theme.blue}; color: white; border: none; border-radius: 22px; font-size: 16px; font-weight: 800;"
            )
        else:
            self.onboarding_subdomain_error.setText("Минимум 6 символов: только буквы, цифры и дефис.")
            self.onboarding_subdomain_error.setStyleSheet(f"color: {self.theme.red}; font-size: 12px; font-weight: 700;")
            self.onboarding_subdomain_continue.setEnabled(False)
            self.onboarding_subdomain_continue.setStyleSheet(
                f"background: {self.theme.red}; color: white; border: none; border-radius: 22px; font-size: 16px; font-weight: 800;"
            )

    def set_onboarding_step(self, step: str) -> None:
        mapping = {"space": 0, "install": 1, "mode": 2, "subdomain": 3, "guide": 4}
        self.onboarding_step = step
        self.launch_choice_stack.setCurrentIndex(mapping.get(step, 2))
        if step == "mode":
            self.update_onboarding_mode_buttons()
        elif step == "subdomain":
            self.refresh_onboarding_subdomain_state()
            self.onboarding_subdomain_input.setFocus()

    def refresh_onboarding_flow(self) -> None:
        status = cached_comfy_setup_status(self.config, force=True)
        self.refresh_onboarding_install_rows(status)
        enough_space, free_bytes, needed_bytes = has_enough_space_for_setup(status)
        self.onboarding_space_stats.setText(f"Свободно: {format_bytes(free_bytes)}\nНужно примерно: {format_bytes(needed_bytes)}")
        current_root = current_comfy_root(self.config)
        self.onboarding_install_path.setText(
            f"Portable-папка: {current_root}" if current_root else "Portable-папка пока не найдена. Можно выбрать существующую или поставить все с нуля."
        )
        if not comfy_core_has_missing(status):
            self.set_onboarding_step("mode")
            return
        if not enough_space:
            self.set_onboarding_step("space")
            return
        self.set_onboarding_step("install")

    def dismiss_onboarding(self) -> None:
        self.onboarding_dismissed = True
        self.set_launch_choice_open(False)

    def on_onboarding_choose_existing_clicked(self) -> None:
        start_dir = self.config.get("comfy_root", "") or str(Path.home() / "Desktop")
        chosen = QFileDialog.getExistingDirectory(self, "Выбери portable-папку ComfyUI", start_dir)
        if not chosen:
            return
        resolved_root = coerce_comfy_root(chosen)
        if not resolved_root:
            self.show_toast("В выбранной папке не найден portable ComfyUI.", True)
            return
        self.config["comfy_root"] = str(resolved_root)
        save_config(self.config)
        self.load_controls_from_config(force=True)
        self.request_refresh_view()
        self.refresh_onboarding_flow()
        if not comfy_core_has_missing(cached_comfy_setup_status(self.config, force=True)):
            self.set_onboarding_step("mode")

    def begin_onboarding_install(self) -> None:
        if self.busy or self.install_setup_inflight:
            return
        start_dir = self.config.get("comfy_root", "") or str(Path.home() / "Desktop")
        chosen = QFileDialog.getExistingDirectory(self, "Куда поставить portable ComfyUI", start_dir)
        if not chosen:
            return
        install_parent = Path(chosen)
        self.onboarding_install_target_parent = install_parent
        self.install_setup_inflight = True
        self.install_setup_scope = "comfy"
        self.install_setup_paused_poll = self.poll_timer.isActive()
        if self.install_setup_paused_poll:
            self.poll_timer.stop()
        self.install_setup_eta = estimate_setup_eta(cached_comfy_setup_status(self.config, force=True))
        self.install_setup_progress_percent = 0
        self.install_setup_progress_detail = "Ставим полный Comfy setup."
        self.install_setup_progress_meta = f"Примерное время: {self.install_setup_eta}"
        self.install_setup_last_scope = "comfy"
        self.install_setup_last_message = ""
        self.install_setup_last_error = False
        self.onboarding_install_section.set_collapsed(False)
        self.onboarding_install_section.set_progress(0, "Подготавливаем установку.", f"Примерное время: {self.install_setup_eta}", True)
        self.onboarding_install_start_button.setEnabled(False)
        self.onboarding_install_start_button.setText("Установка...")
        self.update_install_button()
        self.run_background(
            lambda progress, current_parent=install_parent: install_comfy_core_setup(current_parent, progress),
            job_kind="installsetup:comfy",
            set_busy=False,
            show_toast=False,
            with_progress=True,
        )

    def skip_onboarding_install_step(self) -> None:
        self.set_onboarding_step("mode")

    def set_onboarding_mode(self, mode: str) -> None:
        self.config["launch_mode"] = normalize_launch_mode(mode)
        self.update_onboarding_mode_buttons()

    def advance_onboarding_from_mode(self) -> None:
        self.config["launch_mode"] = normalize_launch_mode(self.config.get("launch_mode", DEFAULT_LAUNCH_MODE))
        self.config["launch_mode_confirmed"] = True
        save_config(self.config)
        self.load_controls_from_config(force=True)
        current_value = sanitize_subdomain(self.config.get("subdomain", ""))
        self.onboarding_subdomain_input.setText(current_value if len(current_value) >= ONBOARDING_MIN_SUBDOMAIN_LEN else "")
        self.set_onboarding_step("subdomain")

    def on_onboarding_subdomain_changed(self) -> None:
        self.refresh_onboarding_subdomain_state()

    def advance_onboarding_from_subdomain(self) -> None:
        value = sanitize_subdomain(self.onboarding_subdomain_input.text())
        if not is_valid_main_subdomain(value):
            self.refresh_onboarding_subdomain_state()
            return
        self.config["subdomain"] = value
        save_config(self.config)
        self.load_controls_from_config(force=True)
        self.set_onboarding_step("guide")

    def complete_onboarding(self) -> None:
        self.config["launch_mode_confirmed"] = True
        self.config["onboarding_completed"] = True
        save_config(self.config)
        self.load_controls_from_config(force=True)
        self.onboarding_dismissed = False
        self.set_launch_choice_open(False)
        self.show_toast("Портал готов к работе.")

    def request_update_check(self, force: bool = False) -> None:
        if self.update_check_inflight:
            return
        self.update_check_inflight = True

        def worker() -> None:
            try:
                info = fetch_latest_release_info(force=force)
                if not info.get("newer"):
                    safe_latest_comfy_release_info(force=force)
                    setup_status = cached_comfy_setup_status(load_config(), force=True)
                    if setup_status.get("comfy_update_available"):
                        info = {
                            "kind": "comfy",
                            "tag_name": setup_status.get("comfy_latest_tag", ""),
                            "html_url": COMFY_GITHUB_REPO_URL,
                            "portable_url": setup_status.get("comfy_latest_url", COMFYUI_PORTABLE_URL),
                            "available": True,
                            "newer": True,
                            "message": setup_status.get("comfy_update_message", ""),
                        }
                    else:
                        info["kind"] = "portal"
                else:
                    info["kind"] = "portal"
                try:
                    self.bridge.update_ready.emit(info)
                except RuntimeError:
                    return
            except Exception as exc:
                try:
                    self.bridge.update_failed.emit(str(exc))
                except RuntimeError:
                    return

        threading.Thread(target=worker, daemon=True).start()

    def on_update_ready(self, info: dict) -> None:
        self.update_check_inflight = False
        self.release_info = dict(info)
        banner_id = f"{info.get('kind', 'portal')}:{info.get('tag_name', '')}"
        if info.get("newer") and banner_id != self.update_banner_dismissed_tag:
            self.show_update_banner(info)
        else:
            self.update_banner.hide()

    def on_update_failed(self, _error_text: str) -> None:
        self.update_check_inflight = False

    def show_update_banner(self, info: dict) -> None:
        self.update_banner_kind = str(info.get("kind", "portal") or "portal")
        version_text = str(info.get("tag_name", "") or "").strip()
        if self.update_banner_kind == "comfy":
            self.update_banner_title.setText(f"Доступна ComfyUI {version_text}" if version_text else "Доступно обновление ComfyUI")
            self.update_banner_subtitle.setText(str(info.get("message", "") or "Можно обновить ComfyUI до latest-сборки. Models, custom_nodes и output сохраняются."))
            self.update_banner_install_button.setText("Обновить Comfy")
        else:
            self.update_banner_title.setText(f"Доступно обновление {version_text}" if version_text else "Доступно обновление")
            self.update_banner_subtitle.setText("На GitHub вышел новый релиз. Можно скачать и обновить портал прямо из приложения.")
            self.update_banner_install_button.setText("Обновить")
        self.update_banner_install_button.setEnabled(True)
        self.update_banner.show()
        self.place_update_banner()

    def dismiss_update_banner(self) -> None:
        if self.release_info:
            self.update_banner_dismissed_tag = f"{self.release_info.get('kind', 'portal')}:{self.release_info.get('tag_name', '')}"
        self.update_banner.hide()

    def install_github_update(self) -> None:
        if self.update_download_inflight or not self.release_info:
            return
        if self.update_banner_kind == "comfy":
            self.update_banner.hide()
            self.set_setup_view_open(True)
            self.start_setup_install("comfy")
            return
        self.update_download_inflight = True
        self.update_banner_install_button.setEnabled(False)
        self.update_banner_install_button.setText("Скачиваем...")
        self.run_background(lambda: prepare_release_update(self.release_info or {}), job_kind="appupdate", set_busy=False, show_toast=False)

    def open_comfy_guide(self) -> None:
        self.set_setup_view_open(True)

    def start_comfy_setup_install(self) -> None:
        self.start_setup_install("comfy")

    def start_setup_install(self, scope: str) -> None:
        if self.busy or self.install_setup_inflight:
            return
        updated_config = dict(load_config())
        comfy_root_input = normalize_root_path(self.comfy_root_input.text())
        comfy_root = str(coerce_comfy_root(comfy_root_input) or "")
        updated_config["comfy_root"] = comfy_root
        updated_config["subdomain"] = normalize_subdomain(self.subdomain_input.text())
        updated_config["launch_mode"] = normalize_launch_mode(
            next((mode for mode, button in self.launch_mode_buttons.items() if button.isChecked()), self.config.get("launch_mode", DEFAULT_LAUNCH_MODE))
        )
        updated_config["extra_launch_args"] = normalize_extra_launch_args(self.extra_launch_args_input.text())
        updated_config["launch_mode_confirmed"] = True
        updated_config["auto_copy_url"] = self.auto_copy_toggle.isChecked()
        updated_config["auto_restart_tunnel"] = self.auto_restart_toggle.isChecked()
        updated_config["start_on_boot"] = self.start_on_boot_toggle.isChecked()
        self.config = updated_config
        save_config(self.config)
        if comfy_root and self.comfy_root_input.text() != comfy_root:
            self.comfy_root_input.setText(comfy_root)
        try:
            sync_windows_autostart(self.config["start_on_boot"])
        except Exception:
            pass
        self.clear_settings_dirty()
        self.load_controls_from_config(force=True)
        status = cached_comfy_setup_status(self.config, force=True)
        if self.setup_page_widget is not None:
            self.setup_page_widget.refresh_status(status)
        if scope == "nodes" and not status.get("comfy_ready"):
            self.install_setup_last_scope = "nodes"
            self.install_setup_last_message = "Сначала установи полный Comfy setup, потом уже nodes."
            self.install_setup_last_error = True
            if self.setup_page_widget is not None:
                self.setup_page_widget.finish_install("nodes", self.install_setup_last_message, True)
            self.show_toast(self.install_setup_last_message, True)
            self.update_install_button()
            return
        install_parent: Path | None = None
        if scope == "comfy" and not current_comfy_root(self.config):
            start_dir = comfy_root_input or normalize_root_path(self.config.get("comfy_root", "")) or str(Path.home() / "Desktop")
            chosen = QFileDialog.getExistingDirectory(self, "Выбери папку для portable ComfyUI", start_dir)
            if not chosen:
                self.install_setup_last_scope = scope
                self.install_setup_last_message = "Установка отменена: папка не выбрана."
                self.install_setup_last_error = True
                if self.setup_page_widget is not None:
                    self.setup_page_widget.finish_install(scope, "Установка отменена: папка не выбрана.", True)
                else:
                    self.show_toast("Установка отменена: папка не выбрана.", True)
                return
            chosen_path = Path(chosen).expanduser().resolve()
            chosen_root = coerce_comfy_root(chosen_path)
            if chosen_root:
                self.config["comfy_root"] = str(chosen_root)
                save_config(self.config)
                self.load_controls_from_config(force=True)
                status = cached_comfy_setup_status(self.config, force=True)
                if self.setup_page_widget is not None:
                    self.setup_page_widget.set_install_target_path("")
                    self.setup_page_widget.refresh_status(status)
            else:
                install_parent = chosen_path
                if self.setup_page_widget is not None:
                    self.setup_page_widget.set_install_target_path(chosen_path)
        missing = comfy_core_has_missing(status) if scope == "comfy" else comfy_nodes_have_missing(status)
        if not missing:
            self.install_setup_last_scope = scope
            self.install_setup_last_message = "Все уже установлено."
            self.install_setup_last_error = False
            if self.setup_page_widget is not None:
                self.setup_page_widget.finish_install(scope, "Все уже установлено.", False)
            else:
                self.show_toast("Все уже установлено.")
            self.update_install_button()
            return
        self.install_setup_inflight = True
        self.install_setup_scope = scope
        self.install_setup_paused_poll = self.poll_timer.isActive()
        if self.install_setup_paused_poll:
            self.poll_timer.stop()
        self.install_setup_eta = estimate_setup_eta(status)
        self.install_setup_progress_percent = 0
        self.install_setup_progress_detail = "Ставим полный Comfy setup." if scope == "comfy" else "Ставим nodes для workflow."
        self.install_setup_progress_meta = f"Примерное время: {self.install_setup_eta}"
        self.install_setup_last_scope = scope
        self.install_setup_last_message = ""
        self.install_setup_last_error = False
        self.update_install_button()
        if self.setup_page_widget is not None:
            self.setup_page_widget.begin_install(scope, self.install_setup_eta)
        self.run_background(
            (lambda progress, current_parent=install_parent: install_comfy_core_setup(current_parent, progress))
            if scope == "comfy"
            else (lambda progress: install_nodes_setup(progress)),
            job_kind=f"installsetup:{scope}",
            set_busy=False,
            show_toast=True,
            with_progress=True,
        )

    def run_autorun_sequence(self) -> None:
        if self.busy:
            return
        snap = self.latest_snap or runtime_snapshot()
        if snap["comfy_active"] or snap["tunnel_active"]:
            return
        if not self.save_settings(silent=True):
            return
        active_friend_targets = any(not entry.get("paused", False) for entry in snap.get("friend_links", []))
        if snap.get("desired_running"):
            self.run_background(start_all, job_kind="autorun", set_busy=True, show_toast=False)
        elif active_friend_targets:
            self.run_background(start_comfy_if_needed, job_kind="autorunfriends", set_busy=False, show_toast=False)

    def set_theme_mode(self, mode: str) -> None:
        if self.config["theme"] == mode:
            return
        self.config["theme"] = mode
        save_config(self.config)
        self.theme = THEMES[mode]
        self.apply_theme()
        self.show_toast(f"Тема переключена: {mode}.")

    def prompt_launch_choice_if_needed(self) -> None:
        if self.autorun_mode or self.onboarding_dismissed or self.config.get("onboarding_completed", False):
            return
        self.refresh_onboarding_flow()
        self.set_launch_choice_open(True)

    def choose_launch_mode(self, mode: str) -> None:
        self.set_onboarding_mode(mode)
        self.advance_onboarding_from_mode()

    def set_launch_mode(self, mode: str) -> None:
        mode = normalize_launch_mode(mode)
        button = self.launch_mode_buttons.get(mode)
        if button and not button.isChecked():
            button.setChecked(True)
        if self.syncing_controls:
            return
        if self.config.get("launch_mode", DEFAULT_LAUNCH_MODE) == mode:
            return
        self.config["launch_mode"] = mode
        self.config["launch_mode_confirmed"] = True
        self.update_segment_buttons()
        self.mark_settings_dirty()

    def set_busy(self, busy: bool) -> None:
        self.busy = busy
        if busy:
            self.progress.setVisible(True)
            self.progress.setRange(0, 0)
            self.busy_dots = 0
            self.busy_timer.start(420)
        else:
            self.progress.setVisible(False)
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
            self.busy_timer.stop()
            self.busy_dots = 0
        self.update_action_button()
        if self.latest_snap:
            self.update_friend_panel_state(self.latest_snap)
            self.update_friends_button(self.latest_snap)
        self.update_install_button()

    def animate_busy_button(self) -> None:
        self.busy_dots = (self.busy_dots + 1) % 4
        dots = "." * self.busy_dots
        text = f"Загрузка{dots}"
        if self.action_button.text() != text:
            self.action_button.setText(text)

    def current_snapshot(self) -> dict:
        if self.latest_snap is not None:
            return self.latest_snap
        comfy_root = normalize_root_path(self.config.get("comfy_root", ""))
        return {
            "config": self.config,
            "state": self.state_cache,
            "url": "",
            "comfy_root": comfy_root,
            "internet_ok": True,
            "comfy_active": False,
            "tunnel_active": False,
            "friend_active": False,
            "friend_links": [],
            "friend_active_count": 0,
            "friend_count": 0,
            "desired_running": False,
            "retry_in": 0,
            "tunnel_error": "",
            "logs": {"comfy": "", "comfy_full": "", "tunnel": "", "friend": ""},
        }

    def update_action_button(self, snap: dict | None = None) -> None:
        snap = snap or self.current_snapshot()
        if self.busy:
            if self.action_visual_state != "busy":
                self.action_button.setStyleSheet(
                    f"background: {self.theme.blue}; color: white; border: none; border-radius: 24px; font-size: 16px; font-weight: 800;"
                )
                self.action_visual_state = "busy"
            return
        # Keep the main action in "Start" mode when only ComfyUI is already up.
        # "Stop" should represent a live public tunnel/friend links, not the app server alone.
        should_stop = snap["tunnel_active"] or snap["friend_active"]
        if should_stop:
            if self.action_button.text() != "Stop":
                self.action_button.setText("Stop")
            if self.action_visual_state != "stop":
                self.action_button.setStyleSheet(
                    f"background: {self.theme.red}; color: white; border: none; border-radius: 24px; font-size: 16px; font-weight: 800;"
                )
                self.action_visual_state = "stop"
        else:
            if self.action_button.text() != "Start":
                self.action_button.setText("Start")
            if self.action_visual_state != "start":
                self.action_button.setStyleSheet(
                    f"background: {self.theme.green}; color: white; border: none; border-radius: 24px; font-size: 16px; font-weight: 800;"
                )
                self.action_visual_state = "start"

    def on_action_button_clicked(self) -> None:
        if self.busy:
            return
        snap = self.latest_snap or runtime_snapshot(include_logs=self.logs_view_open)
        if not self.save_settings(silent=True):
            return
        if snap["tunnel_active"] or snap["friend_active"]:
            self.run_background(stop_all, job_kind="manual", set_busy=True, show_toast=True)
        else:
            self.run_background(start_all, job_kind="manual", set_busy=True, show_toast=True)

    def run_background(self, job, job_kind: str = "manual", set_busy: bool = True, show_toast: bool = True, with_progress: bool = False) -> None:
        if set_busy:
            self.set_busy(True)

        def worker() -> None:
            try:
                if with_progress:
                    def progress(detail: str, percent: int, meta: str = "") -> None:
                        try:
                            self.bridge.progress.emit(job_kind, int(percent), detail, meta)
                        except RuntimeError:
                            return
                    message = job(progress)
                else:
                    message = job()
                try:
                    self.bridge.finished.emit(message, False, job_kind if show_toast else f"{job_kind}:silent")
                except RuntimeError:
                    return
            except Exception as exc:
                try:
                    self.bridge.finished.emit(str(exc), True, job_kind if show_toast else f"{job_kind}:silent")
                except RuntimeError:
                    return

        threading.Thread(target=worker, daemon=True).start()

    def on_job_progress(self, job_kind: str, percent: int, detail: str, meta: str) -> None:
        kind, _, scope = job_kind.partition(":")
        if kind != "installsetup":
            return
        self.install_setup_progress_percent = max(0, min(100, int(percent)))
        self.install_setup_progress_detail = detail
        self.install_setup_progress_meta = meta
        self.install_setup_scope = scope or self.install_setup_scope or "comfy"
        if self.setup_page_widget is not None:
            self.setup_page_widget.update_install_progress(self.install_setup_scope, detail, percent, meta)
        if self.launch_choice_open and self.onboarding_step == "install" and self.install_setup_scope == "comfy":
            payload = parse_setup_progress_meta(meta)
            row_key = str(payload.get("row_key", "") or "")
            row_meta = str(payload.get("meta_text", "") or meta)
            raw_row_percent = payload.get("row_percent")
            row_percent = None if raw_row_percent is None else int(max(0, min(100, int(raw_row_percent))))
            stage = str(payload.get("stage", "") or "").strip().lower()
            if row_key:
                for current_key, row in self.onboarding_install_rows.items():
                    if current_key == row_key:
                        if stage == "done":
                            row.set_state(True, row_meta or "Проверено.", "ready")
                        elif stage == "error":
                            row.set_state(False, row_meta or "Ошибка установки.", "unavailable")
                        else:
                            row.set_progress(row_percent, row_meta)
                    else:
                        row.clear_progress()
            else:
                for row in self.onboarding_install_rows.values():
                    row.clear_progress()
            self.onboarding_install_section.set_progress(percent, detail, row_meta or meta, True)

    def on_job_finished(self, message: str, is_error: bool, job_kind: str) -> None:
        silent = job_kind.endswith(":silent")
        clean_job_kind = job_kind[:-7] if silent else job_kind
        kind, _, meta = clean_job_kind.partition(":")
        if kind == "autorestart":
            self.auto_restart_inflight = False
        elif kind == "restorecomfy":
            self.comfy_restore_inflight = False
        elif kind == "friendrestore" and meta:
            self.friend_restore_inflight.discard(meta)
        elif kind == "friendcreate" and meta and is_error:
            schedule_friend_retry(meta, message)
        elif kind == "installsetup":
            self.install_setup_inflight = False
            should_resume_poll = self.install_setup_paused_poll
            self.install_setup_paused_poll = False
            scope = meta or self.install_setup_scope or "comfy"
            self.install_setup_last_scope = scope
            self.install_setup_last_message = message
            self.install_setup_last_error = is_error
            self.install_setup_progress_percent = 100 if not is_error else self.install_setup_progress_percent
            self.install_setup_progress_detail = message
            self.install_setup_progress_meta = "Готово." if not is_error else "Установка остановилась с ошибкой."
            if self.setup_page_widget is not None:
                self.setup_page_widget.finish_install(scope, message, is_error)
            if self.launch_choice_open and scope == "comfy":
                self.onboarding_install_start_button.setEnabled(True)
                self.onboarding_install_start_button.setText("Установить")
                status = cached_comfy_setup_status(self.config, force=True)
                self.refresh_onboarding_install_rows(status)
                self.onboarding_install_section.set_progress(0 if is_error else 100, message, "Установка остановилась с ошибкой." if is_error else "Готово.", True)
            self.install_setup_scope = ""
            if should_resume_poll and self.overlay_animation_count == 0 and not self.poll_timer.isActive():
                self.poll_timer.start(POLL_MS)
        elif kind == "appupdate":
            self.update_download_inflight = False
            self.update_banner_install_button.setEnabled(True)
            self.update_banner_install_button.setText("Обновить")
            if not is_error:
                self.update_banner_subtitle.setText(message)
                self.update_banner_install_button.setText("Перезапуск...")
                QTimer.singleShot(180, QApplication.instance().quit)
        if self.busy:
            self.set_busy(False)
        if kind == "autorestart" and is_error and load_state().get("desired_running"):
            schedule_tunnel_retry(message)
        if kind == "friendrestore" and meta and is_error:
            schedule_friend_retry(meta, message)
        if kind == "installsetup" and meta == "comfy" and not is_error and self.launch_choice_open and self.onboarding_step == "install":
            self.set_onboarding_step("mode")
        self.request_refresh_view()
        if not silent:
            self.show_toast(message, is_error)

    def copy_value(self, text: str, empty_value: str, success_text: str) -> None:
        clean = text.strip()
        if not clean or clean == empty_value:
            self.show_toast("Ссылки пока нет.", True)
            return
        QApplication.clipboard().setText(clean)
        self.show_toast(success_text)

    def copy_link(self) -> None:
        self.copy_value(self.link_field.text(), "Публичной ссылки пока нет", "Ссылка скопирована.")

    def on_refresh_main_link_clicked(self) -> None:
        if self.busy:
            return
        if not self.save_settings(silent=True):
            return
        self.run_background(regenerate_main_tunnel, job_kind="retunnel", set_busy=True, show_toast=True)

    def copy_friend_link_by_id(self, link_id: str) -> None:
        snap = self.current_snapshot()
        for entry in snap.get("friend_links", []):
            if entry["id"] != link_id:
                continue
            self.copy_value(entry["url"], "", "Friend link скопирован.")
            return
        self.show_toast("Эта ссылка уже удалена.", True)

    def on_friend_create_clicked(self) -> None:
        if self.busy:
            return
        if not self.save_settings(silent=True):
            return
        try:
            entry = reserve_friend_link()
        except Exception as exc:
            self.show_toast(str(exc), True)
            return
        self.request_refresh_view()
        self.run_background(lambda: start_friend_tunnel(entry["id"]), job_kind=f"friendcreate:{entry['id']}", set_busy=False, show_toast=True)

    def on_friend_custom_create_clicked(self) -> None:
        if self.busy:
            return
        if not self.save_settings(silent=True):
            return
        snap = self.current_snapshot()
        dialog = FriendSubdomainDialog(
            self.theme,
            self.config.get("subdomain", ""),
            {entry.get("subdomain", "") for entry in snap.get("friend_links", [])},
            self,
        )
        if dialog.exec() != QDialog.Accepted or not dialog.result_subdomain:
            return
        try:
            entry = reserve_friend_link(dialog.result_subdomain)
        except Exception as exc:
            self.show_toast(str(exc), True)
            return
        self.request_refresh_view()
        self.run_background(lambda: start_friend_tunnel(entry["id"]), job_kind=f"friendcreate:{entry['id']}", set_busy=False, show_toast=True)

    def request_friend_delete(self, link_id: str) -> None:
        row = self.friend_rows.get(link_id)
        if row:
            row.delete_button.setEnabled(False)
            row.copy_button.setEnabled(False)
        self.run_background(lambda: stop_friend_tunnel(link_id), job_kind=f"frienddelete:{link_id}", set_busy=False, show_toast=True)

    def pick_comfy_root(self) -> None:
        start_dir = self.comfy_root_input.text().strip() or str(Path.home())
        chosen = QFileDialog.getExistingDirectory(self, "Choose ComfyUI portable folder", start_dir)
        if not chosen:
            return
        normalized = normalize_root_path(chosen)
        resolved_root = coerce_comfy_root(normalized)
        self.comfy_root_input.setText(str(resolved_root or normalized))
        self.mark_settings_dirty()
        if resolved_root:
            self.show_toast("Папка ComfyUI выбрана.")
        else:
            self.show_toast("Выбрана папка, но внутри не найден portable ComfyUI.", True)

    def save_settings(self, silent: bool = False) -> bool:
        updated_config = dict(load_config())
        comfy_root_input = normalize_root_path(self.comfy_root_input.text())
        comfy_root = str(coerce_comfy_root(comfy_root_input) or "")
        if comfy_root_input and not comfy_root:
            if not silent:
                self.show_toast("В этой папке не найден portable ComfyUI.", True)
            return False
        updated_config["comfy_root"] = comfy_root
        updated_config["subdomain"] = normalize_subdomain(self.subdomain_input.text())
        updated_config["launch_mode"] = normalize_launch_mode(
            next((mode for mode, button in self.launch_mode_buttons.items() if button.isChecked()), self.config.get("launch_mode", DEFAULT_LAUNCH_MODE))
        )
        updated_config["extra_launch_args"] = normalize_extra_launch_args(self.extra_launch_args_input.text())
        updated_config["launch_mode_confirmed"] = True
        updated_config["auto_copy_url"] = self.auto_copy_toggle.isChecked()
        updated_config["auto_restart_tunnel"] = self.auto_restart_toggle.isChecked()
        updated_config["start_on_boot"] = self.start_on_boot_toggle.isChecked()
        self.config = updated_config
        save_config(self.config)
        if comfy_root and self.comfy_root_input.text() != comfy_root:
            self.comfy_root_input.setText(comfy_root)
        try:
            sync_windows_autostart(self.config["start_on_boot"])
        except Exception as exc:
            if not silent:
                self.show_toast(f"Не удалось обновить автозапуск: {exc}", True)
        self.clear_settings_dirty()
        self.load_controls_from_config(force=True)
        self.request_refresh_view()
        if not silent:
            self.show_toast("Настройки сохранены.")
        return True

    def show_toast(self, text: str, is_error: bool = False) -> None:
        color = self.theme.red if is_error else self.theme.blue
        self.toast.setStyleSheet(
            f"background: {color}; color: white; border-radius: 18px; padding: 10px 18px; font-size: 13px; font-weight: 700;"
        )
        self.toast.setText(text)
        self.toast.adjustSize()
        self.place_toast()
        self.toast.setVisible(True)
        self.toast.raise_()
        self.toast_timer.start(2400)

    def hide_toast(self) -> None:
        self.toast.setVisible(False)

    def maybe_restart_tunnel(self, snap: dict) -> None:
        if self.busy or self.auto_restart_inflight:
            return
        if not self.config.get("auto_restart_tunnel", True):
            return
        if not snap["desired_running"] or not snap["comfy_active"] or snap["tunnel_active"]:
            return
        if snap["retry_in"] > 0:
            return
        if not snap.get("internet_ok", True):
            return
        self.auto_restart_inflight = True
        mark_tunnel_retry_pending()
        self.run_background(start_tunnel_if_needed, job_kind="autorestart", set_busy=False, show_toast=False)

    def maybe_restore_comfy(self, snap: dict) -> None:
        wants_runtime = snap["desired_running"] or any(not entry.get("paused", False) for entry in snap.get("friend_links", []))
        if self.busy or self.comfy_restore_inflight:
            return
        if not wants_runtime or snap["comfy_active"]:
            return
        self.comfy_restore_inflight = True
        self.run_background(start_comfy_if_needed, job_kind="restorecomfy", set_busy=False, show_toast=False)

    def maybe_restore_friend_links(self, snap: dict) -> None:
        if self.busy or not snap["comfy_active"]:
            return
        if not snap["friend_links"] or not snap.get("internet_ok", True):
            return

        for entry in snap["friend_links"]:
            if entry.get("paused", False):
                continue
            link_id = entry.get("id", "")
            if not link_id or link_id in self.friend_restore_inflight:
                continue
            if entry.get("retry_in", 0) > 0:
                continue
            if entry.get("status") == "active" and pid_is_running(entry.get("pid")):
                continue
            self.friend_restore_inflight.add(link_id)
            self.run_background(
                lambda current_id=link_id: start_friend_tunnel(current_id),
                job_kind=f"friendrestore:{link_id}",
                set_busy=False,
                show_toast=False,
            )

    def request_refresh_view(self, include_logs: bool | None = None) -> None:
        if include_logs is None:
            include_logs = False
        include_logs = bool(include_logs)
        if self.refresh_inflight:
            self.refresh_requested = True
            self.refresh_requested_logs = self.refresh_requested_logs or include_logs
            return
        self.refresh_inflight = True
        self.refresh_requested = False
        self.refresh_requested_logs = False

        def worker(current_include_logs: bool) -> None:
            try:
                snap = runtime_snapshot(include_logs=current_include_logs)
                try:
                    self.bridge.snapshot_ready.emit(snap)
                except RuntimeError:
                    return
            except Exception as exc:
                try:
                    self.bridge.snapshot_failed.emit(str(exc))
                except RuntimeError:
                    return

        threading.Thread(target=worker, args=(include_logs,), daemon=True).start()

    def refresh_view(self) -> None:
        self.request_refresh_view()

    def on_snapshot_ready(self, snap: dict) -> None:
        self.refresh_inflight = False
        self.apply_snapshot(snap)
        if self.refresh_requested:
            pending_logs = self.refresh_requested_logs
            self.refresh_requested = False
            self.refresh_requested_logs = False
            QTimer.singleShot(0, partial(self.request_refresh_view, pending_logs))

    def on_snapshot_failed(self, error_text: str) -> None:
        self.refresh_inflight = False
        if error_text and self.last_footer != error_text:
            self.footer_hint.setText(error_text)
            self.last_footer = error_text
        if self.refresh_requested:
            pending_logs = self.refresh_requested_logs
            self.refresh_requested = False
            self.refresh_requested_logs = False
            QTimer.singleShot(0, partial(self.request_refresh_view, pending_logs))

    def apply_snapshot(self, snap: dict) -> None:
        self.config = dict(snap.get("config") or load_config())
        self.state_cache = dict(snap.get("state") or self.state_cache)
        self.latest_snap = snap
        url = snap["url"] or "Публичной ссылки пока нет"
        if snap["url"] and snap["url"] != self.last_url and self.config.get("auto_copy_url", True):
            QApplication.clipboard().setText(snap["url"])
            self.show_toast("Ссылка готова и скопирована.")
        if snap["url"]:
            self.last_url = snap["url"]

        if self.link_field.text() != url:
            self.link_field.setText(url)
        self.update_friend_panel_state(snap)
        if self.drawer_open:
            self.load_controls_from_config()
        if self.overlays_open():
            self.ensure_overlay_stack()
        self.ensure_launch_choice_stack()

        comfy_detail = "Порт 8188 готов" if snap["comfy_active"] else "Ждем запуск"
        if snap["tunnel_active"]:
            tunnel_detail = self.config["subdomain"]
        elif snap["desired_running"] and snap["retry_in"] > 0:
            tunnel_detail = f"Повтор через {snap['retry_in']}с"
        elif snap["desired_running"]:
            tunnel_detail = "Переподключаем"
        else:
            tunnel_detail = "Ждем ссылку"
        any_live = snap["comfy_active"] or snap["tunnel_active"] or snap["friend_active"]
        launcher_value = "Работает" if self.busy else ("Онлайн" if any_live else "Готов")
        launcher_color = self.theme.blue if self.busy else (self.theme.green if any_live else self.theme.text)
        if snap["friend_count"] and not snap["tunnel_active"]:
            launcher_detail = (
                f"{snap['friend_active_count']} friend links активны"
                if snap["friend_active_count"]
                else "Friend links запускаются"
            )
        else:
            launcher_detail = "Авто-туннель включен" if self.config.get("auto_restart_tunnel", True) else "Авто-туннель выключен"

        self.comfy_card.set_status("Активен" if snap["comfy_active"] else "Оффлайн", self.theme.green if snap["comfy_active"] else self.theme.red, comfy_detail)
        self.tunnel_card.set_status("Активен" if snap["tunnel_active"] else "Оффлайн", self.theme.green if snap["tunnel_active"] else self.theme.red, tunnel_detail)
        self.launcher_card.set_status(launcher_value, launcher_color, launcher_detail)
        self.logs_status_pill.setText("Активен" if snap["comfy_active"] else "Оффлайн")
        self.logs_status_pill.setStyleSheet(
            f"background: {self.theme.surface_alt}; color: {(self.theme.green if snap['comfy_active'] else self.theme.red)}; "
            f"border: 1px solid {self.theme.border}; border-radius: 16px; padding: 9px 14px; font-size: 12px; font-weight: 800;"
        )

        comfy_log = snap["logs"]["comfy"].splitlines()[-1] if snap["logs"]["comfy"] else ""
        tunnel_log = snap["logs"]["tunnel"].splitlines()[-1] if snap["logs"]["tunnel"] else ""
        friend_log = snap["logs"]["friend"].splitlines()[-1] if snap["logs"]["friend"] else ""
        main_subdomain = normalize_subdomain(self.config.get("subdomain", ""))
        if tunnel_log and snap["tunnel_active"] and main_subdomain:
            detected_subdomain = extract_public_subdomain(tunnel_log)
            if detected_subdomain and detected_subdomain != main_subdomain:
                tunnel_log = f"your url is: {friend_url_for_subdomain(main_subdomain)}"
        footer = "Start сначала поднимает ComfyUI, а потом LocalTunnel."
        if not snap["comfy_root"]:
            footer = "Укажи portable-папку ComfyUI в настройках или держи exe рядом с ней."
        elif (snap["desired_running"] or snap["friend_count"]) and not snap.get("internet_ok", True):
            footer = "Нет интернета. Ждем сеть, чтобы поднять основной и friend tunnels."
        if snap["comfy_active"] and snap["tunnel_active"]:
            footer = "Все выглядит готовым."
        elif snap["friend_count"]:
            footer = "Friend links прогреваются." if snap["friend_active_count"] < snap["friend_count"] else "Friend links готовы к отправке."
        elif snap["desired_running"] and not snap["tunnel_active"] and snap["retry_in"] > 0:
            footer = f"Туннель упал. Автоповтор через {snap['retry_in']}с."
        elif snap["desired_running"] and snap["tunnel_error"]:
            footer = snap["tunnel_error"]
        if tunnel_log:
            footer = tunnel_log
        elif friend_log:
            footer = friend_log
        elif comfy_log and not snap["tunnel_active"]:
            footer = comfy_log
        if self.last_footer != footer:
            self.footer_hint.setText(footer)
            self.last_footer = footer

        log_lines = []
        if snap["logs"]["comfy"]:
            log_lines.append("ComfyUI: " + snap["logs"]["comfy"].splitlines()[-1])
        if snap["logs"]["tunnel"]:
            log_lines.append("Туннель: " + snap["logs"]["tunnel"].splitlines()[-1])
        if snap["logs"]["friend"]:
            log_lines.append("Друзья: " + snap["logs"]["friend"].splitlines()[-1])
        log_text = "\n".join(log_lines) if log_lines else "Логи появятся здесь после запуска."
        if self.last_log_hint != log_text:
            self.log_hint.setText(log_text)
            self.last_log_hint = log_text

        if self.logs_view_open or snap["logs"].get("comfy_full"):
            comfy_full_log = snap["logs"].get("comfy_full", "").strip()
            self.apply_comfy_log_viewer_text(comfy_full_log or "Логи ComfyUI появятся здесь после запуска.")

        self.theme = THEMES[self.config["theme"]]
        theme_changed = self.applied_theme_name != self.config["theme"]
        if theme_changed:
            self.apply_theme()
        if self.setup_page_widget is not None:
            self.setup_page_widget.theme = self.theme
            if theme_changed:
                self.setup_page_widget.apply_theme()
            now = time.monotonic()
            should_refresh_setup = self.install_setup_inflight or (
                self.setup_view_open and (theme_changed or now - self.last_setup_page_refresh_at >= 4.0)
            )
            if should_refresh_setup:
                self.setup_page_widget.refresh_status(cached_comfy_setup_status(self.config))
                self.last_setup_page_refresh_at = now
        self.update_action_button(snap)
        self.update_friends_button(snap)
        self.update_logs_button()
        self.update_install_button()
        self.maybe_restore_comfy(snap)
        self.maybe_restart_tunnel(snap)
        self.maybe_restore_friend_links(snap)


def main() -> None:
    if not acquire_single_instance():
        return
    migrate_legacy_storage()
    config = load_config()
    if not config.get("comfy_root") and is_comfy_root(BASE_DIR):
        config["comfy_root"] = str(BASE_DIR)
    if not config.get("comfy_root"):
        for candidate in (BASE_DIR.parent, Path.home() / "Desktop", Path.home() / "Downloads"):
            discovered = coerce_comfy_root(candidate)
            if discovered:
                config["comfy_root"] = str(discovered)
                break
    save_config(config)
    save_state(load_state())
    try:
        sync_windows_autostart(config.get("start_on_boot", False))
    except Exception:
        pass
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle(QStyleFactory.create("Fusion"))
    app_font = QFont("Segoe UI Variable Text", 10)
    if app_font.family().lower() == "segoe ui variable text":
        app_font.setStyleStrategy(QFont.PreferAntialias)
    else:
        app_font = QFont("Segoe UI", 10)
        app_font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(app_font)
    icon_path = resolve_asset_path("comfy_portal.ico")
    if not icon_path.exists():
        icon_path = resolve_asset_path("comfy_portal_icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow(autorun_mode="--autorun" in sys.argv[1:])
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
