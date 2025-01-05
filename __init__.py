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
__version__ = "1.0.1"

import os
import sys
import json
import inspect
import importlib
from pathlib import Path
from typing import Any, Generator, Tuple

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
# === THERE CAN BE ONLY ONE ===
# ==============================================================================

class Singleton(type):
    _instances = {}

    def __call__(cls, *arg, **kw) -> Any:
        # If the instance does not exist, create and store it
        if cls not in cls._instances:
            instance = super().__call__(*arg, **kw)
            cls._instances[cls] = instance
        return cls._instances[cls]

# ==============================================================================
# === CORE NODES ===
# ==============================================================================

class JOVBaseNode:
    NOT_IDEMPOTENT = True
    CATEGORY = f"{JOV_PACKAGE.upper()} 🦚"
    RETURN_TYPES = ("IMAGE", "IMAGE", "MASK")
    RETURN_NAMES = ('RGBA', 'RGB', 'MASK')
    FUNCTION = "run"

    @classmethod
    def VALIDATE_INPUTS(cls, *arg, **kw) -> bool:
        return True

    @classmethod
    def INPUT_TYPES(cls, prompt:bool=False, extra_png:bool=False, dynprompt:bool=False) -> dict:
        data = {
            "required": {},
            "optional": {},
            "outputs": {
                0: ("IMAGE", {"tooltips":"Full channel [RGBA] image. If there is an alpha, the image will be masked out with it when using this output."}),
                1: ("IMAGE", {"tooltips":"Three channel [RGB] image. There will be no alpha."}),
                2: ("MASK", {"tooltips":"Single channel mask output."}),
            },
            "hidden": {
                "ident": "UNIQUE_ID"
            }
        }
        if prompt:
            data["hidden"]["prompt"] = "PROMPT"
        if extra_png:
            data["hidden"]["extra_pnginfo"] = "EXTRA_PNGINFO"

        if dynprompt:
            data["hidden"]["dynprompt"] = "DYNPROMPT"
        return data

class AnyType(str):
    """AnyType input wildcard trick taken from pythongossss's:

    https://github.com/pythongosssss/ComfyUI-Custom-Scripts
    """
    def __ne__(self, __value: object) -> bool:
        return False

JOV_TYPE_ANY = AnyType("*")

# want to make explicit entries; comfy only looks for single type
JOV_TYPE_COMFY = "BOOLEAN|FLOAT|INT"
JOV_TYPE_VECTOR = "VEC2|VEC3|VEC4|VEC2INT|VEC3INT|VEC4INT|COORD2D"
JOV_TYPE_NUMBER = f"{JOV_TYPE_COMFY}|{JOV_TYPE_VECTOR}"
JOV_TYPE_IMAGE = "IMAGE|MASK"
JOV_TYPE_FULL = f"{JOV_TYPE_NUMBER}|{JOV_TYPE_IMAGE}"

JOV_TYPE_COMFY = JOV_TYPE_ANY
JOV_TYPE_VECTOR = JOV_TYPE_ANY
JOV_TYPE_NUMBER = JOV_TYPE_ANY
JOV_TYPE_IMAGE = JOV_TYPE_ANY
JOV_TYPE_FULL = JOV_TYPE_ANY

GLSL_INTERNAL = '🌈'
GLSL_CUSTOM = '🦄'

# ==============================================================================
# === CORE SUPPORT ===
# ==============================================================================

def load_file(fname: str) -> str | None:
    try:
        with open(fname, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(e)

def deep_merge(d1: dict, d2: dict) -> dict:
    """
    Deep merge multiple dictionaries recursively.

    Args:
        *dicts: Variable number of dictionaries to be merged.

    Returns:
        dict: Merged dictionary.
    """
    for key in d2:
        if key in d1:
            if isinstance(d1[key], dict) and isinstance(d2[key], dict):
                deep_merge(d1[key], d2[key])
            else:
                d1[key] = d2[key]
        else:
            d1[key] = d2[key]
    return d1

def zip_longest_fill(*iterables: Any) -> Generator[Tuple[Any, ...], None, None]:
    """
    Zip longest with fill value.

    This function behaves like itertools.zip_longest, but it fills the values
    of exhausted iterators with their own last values instead of None.
    """
    try:
        iterators = [iter(iterable) for iterable in iterables]
    except Exception as e:
        logger.error(iterables)
        logger.error(str(e))
    else:
        while True:
            values = [next(iterator, None) for iterator in iterators]

            # Check if all iterators are exhausted
            if all(value is None for value in values):
                break

            # Fill in the last values of exhausted iterators with their own last values
            for i, _ in enumerate(iterators):
                if values[i] is None:
                    iterator_copy = iter(iterables[i])
                    while True:
                        current_value = next(iterator_copy, None)
                        if current_value is None:
                            break
                        values[i] = current_value

            yield tuple(values)

# ==============================================================================
# === NODE LOADER ===
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
