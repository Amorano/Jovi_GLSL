"""
     ██  ██████  ██    ██ ██ ███    ███ ███████ ████████ ██████  ██ ██   ██ 
     ██ ██    ██ ██    ██ ██ ████  ████ ██         ██    ██   ██ ██  ██ ██  
     ██ ██    ██ ██    ██ ██ ██ ████ ██ █████      ██    ██████  ██   ███  
██   ██ ██    ██  ██  ██  ██ ██  ██  ██ ██         ██    ██   ██ ██  ██ ██ 
 █████   ██████    ████   ██ ██      ██ ███████    ██    ██   ██ ██ ██   ██ 

                            OPENGL Shaders for ComfyUI
                    http://www.github.com/Amorano/Jovi_GLSL

@title: Jovi_GLSL
@author: amorano
@category: GLSL
@reference: https://github.com/Amorano/Jovi_GLSL
@tags: GLSL, HLSL, shaders
@description: Integrates GLSL shader support.
@node list:
    GLSLNode
@version: 1.0.1
"""

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
__author__ = """Alexander G. Morano"""
__email__ = "amorano@gmail.com"
__version__ = "1.0.2"

import os
import sys
import json
import inspect
import importlib
from pathlib import Path

from loguru import logger

# ==============================================================================
# === GLOBAL ===
# ==============================================================================

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
WEB_DIRECTORY = "./web"

ROOT = Path(__file__).resolve().parent
ROOT_COMFY = ROOT.parent.parent
ROOT_DOC = ROOT / 'res/doc'

JOV_WEB = ROOT / 'web'
JOV_INTERNAL = os.getenv("JOV_INTERNAL", 'false').strip().lower() in ('true', '1', 't')
JOV_LOG_LEVEL = os.getenv("JOV_LOG_LEVEL", "INFO")
logger.configure(handlers=[{"sink": sys.stdout, "level": JOV_LOG_LEVEL}])

JOV_PACKAGE = "Jovi_GLSL"

# ==============================================================================
# === SUPPORT ===
# ==============================================================================

def load_file(fname: str) -> str | None:
    try:
        with open(fname, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(e)

# ==============================================================================
# === LOADER ===
# ==============================================================================

def loader():
    global NODE_DISPLAY_NAME_MAPPINGS, NODE_CLASS_MAPPINGS
    NODE_LIST_MAP = {}

    for fname in ROOT.glob('core/**/*.py'):
        if fname.stem.startswith('_'):
            continue

        try:
            route = str(fname).replace("\\", "/").split(f"{JOV_PACKAGE}/core/")[1]
            route = route.split('.')[0].replace('/', '.')
            module = f"{JOV_PACKAGE}.core.{route}"
            module = importlib.import_module(module)
        except Exception as e:
            logger.warning(f"module failed {fname}")
            logger.warning(str(e))
            continue

        # check if there is a dynamic register function....
        try:
            for class_name, class_def in module.import_dynamic():
                setattr(module, class_name, class_def)
                # logger.debug(f"shader: {class_name}")
        except Exception as e:
            pass

        classes = inspect.getmembers(module, inspect.isclass)
        for class_name, class_object in classes:
            if not class_name.endswith('BaseNode') and hasattr(class_object, 'NAME') and hasattr(class_object, 'CATEGORY'):
                name = class_object.NAME
                NODE_DISPLAY_NAME_MAPPINGS[name] = name
                NODE_CLASS_MAPPINGS[name] = class_object
                desc = class_object.DESCRIPTION if hasattr(class_object, 'DESCRIPTION') else name
                NODE_LIST_MAP[name] = desc.split('.')[0].strip('\n')

    NODE_CLASS_MAPPINGS = {x[0] : x[1] for x in sorted(NODE_CLASS_MAPPINGS.items(),
                                                            key=lambda item: getattr(item[1], 'SORT', 0))}

    keys = NODE_CLASS_MAPPINGS.keys()
    for name in keys:
        logger.debug(f"✅ {name} :: {NODE_DISPLAY_NAME_MAPPINGS[name]}")
    logger.info(f"{len(keys)} nodes loaded")

    # only do the list on local runs...
    if JOV_INTERNAL:
        with open(str(ROOT) + "/node_list.json", "w", encoding="utf-8") as f:
            json.dump(NODE_LIST_MAP, f, sort_keys=True, indent=4 )

loader()
