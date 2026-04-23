from pathlib import Path

from cx_Freeze import Executable, setup


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
PYTHON_HOME = Path(r"C:\Users\14\AppData\Local\Programs\Python\Python314")


build_exe_options = {
    "packages": [
        "json",
        "locale",
        "os",
        "re",
        "secrets",
        "shutil",
        "socket",
        "subprocess",
        "sys",
        "tempfile",
        "threading",
        "time",
        "urllib",
        "zipfile",
        "ctypes",
        "dataclasses",
        "functools",
        "pathlib",
        "psutil",
    ],
    "includes": [
        "winreg",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
    ],
    "excludes": [
        "PySide6.Qt3DAnimation",
        "PySide6.Qt3DCore",
        "PySide6.Qt3DExtras",
        "PySide6.Qt3DInput",
        "PySide6.Qt3DLogic",
        "PySide6.Qt3DRender",
        "PySide6.QtBluetooth",
        "PySide6.QtCharts",
        "PySide6.QtConcurrent",
        "PySide6.QtDataVisualization",
        "PySide6.QtDBus",
        "PySide6.QtDesigner",
        "PySide6.QtGraphs",
        "PySide6.QtHelp",
        "PySide6.QtHttpServer",
        "PySide6.QtLocation",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
        "PySide6.QtNetworkAuth",
        "PySide6.QtNfc",
        "PySide6.QtOpenGL",
        "PySide6.QtOpenGLWidgets",
        "PySide6.QtPdf",
        "PySide6.QtPdfWidgets",
        "PySide6.QtPositioning",
        "PySide6.QtPrintSupport",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtQuick3D",
        "PySide6.QtQuickControls2",
        "PySide6.QtQuickWidgets",
        "PySide6.QtRemoteObjects",
        "PySide6.QtScxml",
        "PySide6.QtSensors",
        "PySide6.QtSerialBus",
        "PySide6.QtSerialPort",
        "PySide6.QtSpatialAudio",
        "PySide6.QtSql",
        "PySide6.QtStateMachine",
        "PySide6.QtSvg",
        "PySide6.QtSvgWidgets",
        "PySide6.QtTest",
        "PySide6.QtTextToSpeech",
        "PySide6.QtUiTools",
        "PySide6.QtWebChannel",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebSockets",
        "PySide6.QtWebView",
        "PySide6.QtXml",
        "PySide6.QtXmlPatterns",
    ],
    "include_files": [
        (str(PYTHON_HOME / "vcruntime140.dll"), "vcruntime140.dll"),
        (str(PYTHON_HOME / "vcruntime140_1.dll"), "vcruntime140_1.dll"),
        (str(ASSETS / "comfy_portal.ico"), "assets/comfy_portal.ico"),
        (str(ASSETS / "comfy_portal_icon.png"), "assets/comfy_portal_icon.png"),
        (str(ASSETS / "telegram_brand.png"), "assets/telegram_brand.png"),
        (str(ASSETS / "settings_brand.png"), "assets/settings_brand.png"),
        (str(ASSETS / "telegram_button_icon.png"), "assets/telegram_button_icon.png"),
        (str(ASSETS / "telegram_button_round.png"), "assets/telegram_button_round.png"),
    ],
    "include_msvcr": False,
    "optimize": 0,
}


executables = [
    Executable(
        script=str(ROOT / "comfy_portal.py"),
        base="gui",
        target_name="Comfy Portal.exe",
        icon=str(ASSETS / "comfy_portal.ico"),
    )
]


setup(
    name="Comfy Portal",
    version="1.0.4",
    description="ComfyUI launcher and tunnel manager",
    options={"build_exe": build_exe_options},
    executables=executables,
)
