""" Jovi_GLSL - Core """

import os
import re
from enum import Enum
from pathlib import Path

from cozy_comfyui import \
    logger, \
    EnumConvertType, \
    load_file

from .. import \
    ROOT

# ==============================================================================
# === EXCEPTION ===
# ==============================================================================

class CompileException(Exception): pass

# ==============================================================================
# === GLOBAL ===
# ==============================================================================

RE_VARIABLE = re.compile(r"^\s*uniform\s+(\w+)\s+(\w+)\s*;\s*(?:\/\/\s*([^;|]*))?(?:\s*;\s*([^;|]*))?(?:\s*;\s*([^;|]*))?(?:\s*;\s*([^;|]*))?(?:\s*;\s*([^;|]*))?(?:\s*\|[\t\f ]*([^\r\n]*))?$", re.MULTILINE)

# SHADER LOADER
ROOT_GLSL = ROOT / 'glsl'
GLSL_PROGRAMS = {
    "vertex": {  },
    "fragment": { }
}

GLSL_PROGRAMS['vertex'].update({str(f.relative_to(ROOT_GLSL).as_posix()):
                                str(f) for f in Path(ROOT_GLSL).rglob('*.vert')})

USER_GLSL = ROOT / 'user'
USER_GLSL.mkdir(parents=True, exist_ok=True)
logger.debug(f"user shader folder: {USER_GLSL}")
if (USER_GLSL := os.getenv("JOV_GLSL", str(USER_GLSL))) is not None:
    GLSL_PROGRAMS['vertex'].update({str(f.relative_to(USER_GLSL).as_posix()):
                                    str(f) for f in Path(USER_GLSL).rglob('*.vert')})

GLSL_PROGRAMS['fragment'].update({str(f.relative_to(ROOT_GLSL).as_posix()):
                                  str(f) for f in Path(ROOT_GLSL).rglob('*.frag')})

if USER_GLSL is not None:
    GLSL_PROGRAMS['fragment'].update({str(f.relative_to(USER_GLSL).as_posix()):
                                      str(f) for f in Path(USER_GLSL).rglob('*.frag')})

PROG_VERTEX = None
try:
    prog = GLSL_PROGRAMS['vertex'].pop('.lib/_.vert')
    PROG_VERTEX = load_file(prog)
except Exception as e:
    logger.error(e)
    raise Exception("failed load default vertex program .lib/_.vert")

PROG_FRAGMENT = None
try:
    prog = GLSL_PROGRAMS['fragment'].pop('.lib/_.frag')
    PROG_FRAGMENT = load_file(prog)
except Exception as e:
    logger.error(e)
    raise Exception("failed load default fragment program .lib/_.frag")

PROG_HEADER = load_file(ROOT_GLSL / '.lib/_.head')
PROG_FOOTER = load_file(ROOT_GLSL / '.lib/_.foot')

logger.info(f"  vertex programs: {len(GLSL_PROGRAMS['vertex'])}")
logger.info(f"fragment programs: {len(GLSL_PROGRAMS['fragment'])}")

# ==============================================================================
# === ENUMERATION ===
# ==============================================================================

PTYPE = {
    'bool': EnumConvertType.BOOLEAN,
    'int': EnumConvertType.INT,
    'ivec2': EnumConvertType.VEC2INT,
    'ivec3': EnumConvertType.VEC3INT,
    'ivec4': EnumConvertType.VEC4INT,
    'float': EnumConvertType.FLOAT,
    'vec2': EnumConvertType.VEC2,
    'vec3': EnumConvertType.VEC3,
    'vec4': EnumConvertType.VEC4,
    'sampler2D': EnumConvertType.IMAGE
}

class EnumEdgeWrap(Enum):
    CLAMP  = 10
    WRAP   = 20
    MIRROR = 30
