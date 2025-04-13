"""
     ██╗ ██████╗ ██╗   ██╗██╗     ██████╗ ██╗     ███████╗██╗
     ██║██╔═══██╗██║   ██║██║    ██╔════╝ ██║     ██╔════╝██║
     ██║██║   ██║██║   ██║██║    ██║  ███╗██║     ███████╗██║
██   ██║██║   ██║╚██╗ ██╔╝██║    ██║   ██║██║     ╚════██║██║
╚█████╔╝╚██████╔╝ ╚████╔╝ ██║    ╚██████╔╝███████╗███████║███████╗
 ╚════╝  ╚═════╝   ╚═══╝  ╚═╝     ╚═════╝ ╚══════╝╚══════╝╚══════╝

                  OPENGL Shaders for ComfyUI
"""

__author__ = "Alexander G. Morano"
__email__ = "amorano@gmail.com"

from pathlib import Path
from cozy_comfyui.node import loader

# ==============================================================================
# === GLOBAL ===
# ==============================================================================

PACKAGE = "JOV_GL"
WEB_DIRECTORY = "./web"
ROOT = Path(__file__).resolve().parent
NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS = loader(ROOT,
                                                         PACKAGE,
                                                         "core",
                                                         f"{PACKAGE} 🌈")
