""" Jovi_GLSL - GLSL """

import re
import sys
from typing import Any

from comfy.utils import ProgressBar

from cozy_comfyui import \
    logger, TensorType, \
    IMAGE_SIZE_MIN, IMAGE_SIZE_DEFAULT, IMAGE_SIZE_MAX, \
    RGBAMaskType, EnumConvertType, \
    load_file, parse_value, parse_param, zip_longest_fill

from cozy_comfyui.node import \
    CozyImageNode

from cozy_comfyui.image.convert import \
    cv_to_tensor_full, tensor_to_cv

from cozy_comfyui.image.misc import \
    image_stack

from ..core import \
    GLSL_PROGRAMS, PTYPE, RE_VARIABLE, ROOT_GLSL, \
    CompileException, EnumEdgeWrap

from ..core.glsl_shader import GLSLShader
from ..core import glsl_enum as glslEnum

# ==============================================================================
# === GLOBAL ===
# ==============================================================================

RE_INCLUDE = re.compile(r"^\s*#include\s+([A-Za-z_\-\.\\\/]{3,})$", re.MULTILINE)
RE_SHADER_META = re.compile(r"^\/\/\s?([A-Za-z_]{3,}):\s?(.+)$", re.MULTILINE)

# ==============================================================================
# === SUPPORT ===
# ==============================================================================

def shader_meta(shader: str) -> dict[str, Any]:
    ret = {}
    for match in RE_SHADER_META.finditer(shader):
        key, value = match.groups()
        ret[key] = value
    ret['_'] = [match.groups() for match in RE_VARIABLE.finditer(shader)]
    return ret

def load_file_glsl(fname: str) -> str:

    # first file we load, starts the list of included
    include = set()

    def scan_include(file:str, idx:int=0) -> str:
        if idx > 8:
            raise CompileException(f"too many file include recursions ({idx})")

        file_path = ROOT_GLSL / file
        if file_path in include:
            return ""

        include.add(file_path)
        try:
            result = load_file(file_path)
        except FileNotFoundError:
            raise CompileException(f"File not found: {file_path}")

        # replace #include directives with their content
        def replace_include(match) -> str:
            lib_path = ROOT_GLSL / match.group(1)
            if lib_path not in include:
                return scan_include(lib_path, idx+1)
            return ""

        return RE_INCLUDE.sub(replace_include, result)

    return scan_include(fname)

def import_dynamic() -> tuple[str,...]:
    ret = []
    sort = 5000
    root = str(ROOT_GLSL)
    for name, fname in GLSL_PROGRAMS['fragment'].items():
        if (shader := load_file_glsl(fname)) is None:
            logger.error(f"missing shader file {fname}")
            continue

        meta = shader_meta(shader)
        if meta.get('hide', False):
            continue

        name = meta.get('name', name.split('.')[0]).upper()
        class_name = name.title().replace(' ', '_')
        class_name = f'GLSLNode_{class_name}'

        sort_order = sort
        # put custom user nodes last
        if fname.startswith(root):
            sort_order -= 5000

        # category = GLSLNodeDynamic.CATEGORY
        category = meta.get('category', "")

        class_def = type(class_name, (GLSLNodeDynamic,), {
            "NAME": name,
            "DESCRIPTION": meta.get('desc', name),
            "CATEGORY": category.upper(),
            "FRAGMENT": shader,
            "PARAM": meta.get('_', []),
            "CONTROL": [x.upper().strip() for x in meta.get('control', "").split(",") if len(x) > 0],
            #"PASS": [x.strip() for x in meta.get('pass', "").split(",") if len(x) > 0],
            #"OUTPUT": [x.strip() for x in meta.get('output', "").split(",") if len(x) > 0],
            "SORT": sort_order,
        })

        sort += 10
        ret.append((class_name, class_def,))
    return ret

# ==============================================================================
# === CLASS ===
# ==============================================================================

class GLSLNodeDynamic(CozyImageNode):
    CONTROL = []
    PARAM = []

    # res, frame. framerate, time, matte, edge, seed, batch

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        original_params = super().INPUT_TYPES()
        optional = original_params.get('optional', {})
        if 'RES' in cls.CONTROL:
            optional["iRes"] = ("VEC2", {
                "default": (IMAGE_SIZE_DEFAULT, IMAGE_SIZE_DEFAULT),
                "mij":IMAGE_SIZE_MIN, "label": ['W', 'H'], "int": True,
                "tooltip": "Width and Height as a Vector2 Integer (x, y)"
            })

        if 'FRAME' in cls.CONTROL:
            optional["iFrame"] = ("INT", {
                "default": 0, "min": 0, "max": sys.maxsize,
                "tooltip": "Current frame to render"
            })

        if 'FRAMERATE' in cls.CONTROL:
            optional["iFrameRate"] = ("INT", {
                "default": 24, "min": 1, "max": 120,
                "tooltip": "Used to calculate frame step size and iTime"
            })

        if 'TIME' in cls.CONTROL:
            optional["iTime"] = ("INT", {
                "default": -1, "min": -1, "max": sys.maxsize,
                "tooltip": "Value to use directly; if > -1 will override iFrame/iFrameRate calculation."
            })

        if 'MATTE' in cls.CONTROL:
            optional["matte"] = ("VEC4", {
                "default": (0, 0, 0, 255),
                "rgb": True,
                "tooltip": "Define a background color for padding. Useful when images do not fit and need a filler color"
            })

        if 'EDGE' in cls.CONTROL:
            optional["edge_x"] = (EnumEdgeWrap._member_names_, {
                "default": EnumEdgeWrap.CLAMP.name,
                "tooltip": "Clamp, Wrap or Mirror the Image Edge"
            })
            optional["edge_y"] = (EnumEdgeWrap._member_names_, {
                "default": EnumEdgeWrap.CLAMP.name,
                "tooltip": "Clamp, Wrap or Mirror the Image Edge"
            })
        else:
            if 'EDGEX' in cls.CONTROL:
                optional["edge_x"] = (EnumEdgeWrap._member_names_, {
                    "default": EnumEdgeWrap.CLAMP.name,
                    "tooltip": "Clamp, Wrap or Mirror the Image Edge"
                })
            if 'EDGEY' in cls.CONTROL:
                optional["edge_y"] = (EnumEdgeWrap._member_names_, {
                    "default": EnumEdgeWrap.CLAMP.name,
                    "tooltip": "Clamp, Wrap or Mirror the Image Edge"
                })

        if 'SEED' in cls.CONTROL:
            optional["seed"] = ("INT", {
                "default": 0, "min": 0, "max": sys.maxsize,
                "tooltip": "Number of frames to generate. 0 (continuous mode) means continue from the last queue generating the next single frame based on iFrameRate."
            })

        if 'BATCH' in cls.CONTROL:
            optional["batch"] = ("INT", {
                "default": 1, "min": 1, "max": sys.maxsize,
                "tooltip": "Number of frames to generate. 0 (continuous mode) means continue from the last queue generating the next single frame based on iFrameRate. In the shader this will be the index of the batch iteration or 0."
            })

        """
        'MODE': (EnumScaleMode._member_names_, {"default": EnumScaleMode.MATTE.name})
        'SAMPLE': (EnumInterpolation._member_names_, {"default": EnumInterpolation.LANCZOS4.name})
        """

        # parameter list first...
        data = {}
        # default, min, max, step, metadata, tooltip
        # 1., 1., 1.; 0; 1; 0.01; rgb | End of the Range
        # ;;;; mask | mask image
        # ;;;; rgb  | color with default (255, 255, 255, 255)
        for glsl_type, name, default, val_min, val_max, val_step, meta, tooltip in cls.PARAM:
            typ = PTYPE[glsl_type]
            params = {"default": None}

            d = None
            type_name = "IMAGE,MASK"
            if glsl_type == 'sampler2D':
                if meta is not None and "mask" in meta:
                    type_name = "MASK"
                else:
                    type_name = "IMAGE"
            else:
                type_name = typ.name

                if default is not None:
                    if default.startswith('EnumGLSL'):
                        params['default'] = 0
                        if (target_enum := getattr(glslEnum, default.strip(), None)) is not None:
                            # this be an ENUM....
                            type_name = target_enum._member_names_
                            params['default'] = type_name[0]
                    elif default != "":
                        d = default.split(',')
                        params['default'] = parse_value(d, typ, 0)
                    elif meta is not None:
                        if "rgba" in meta:
                            params['default'] = [255,255,255,255]
                        elif "rgb" in meta:
                            params['default'] = [255,255,255]

                def minmax(mm: str, what: str) -> str:
                    match glsl_type:
                        case 'int'|'float':
                            mm = what
                    return mm

                if val_min is not None:
                    if val_min == "":
                        val_min = -sys.maxsize
                    params[minmax('mij', 'min')] = parse_value(val_min, EnumConvertType.FLOAT, -sys.maxsize)

                if val_max is not None:
                    if val_max == "":
                        val_max = sys.maxsize
                    params[minmax('maj', 'max')] = parse_value(val_max, EnumConvertType.FLOAT, sys.maxsize)

                if val_step is not None:
                    d = 0.01
                    params['precision'] = 3
                    if typ.name.endswith('INT'):
                        d = 1
                        params['precision'] = 0
                    params['step'] = parse_value(val_step, EnumConvertType.FLOAT, d)

                if meta is not None:
                    if "linear" in meta:
                        params['linear'] = True
                    elif "rgb" in meta or "rgba" in meta:
                        params['rgb'] = True
                        params['mij'] = 0
                        params['maj'] = 255
                        params['step'] = 1

            if tooltip is not None:
                params["tooltip"] = tooltip
            data[name] = (type_name, params,)

        optional['FRAGMENT'] = ("STRING", {"default": cls.FRAGMENT})
        data.update(optional)
        original_params['optional'] = data
        return original_params

    def __init__(self, *arg, **kw) -> None:
        super().__init__(*arg, **kw)
        self.__glsl = None

    def run(self, ident, **kw) -> RGBAMaskType:
        # IRES, MATTE, EDGE, IFRAME, IFRAMERATE, ITIME, SEED, BATCH
        iResolution = parse_param(kw, 'iRes', EnumConvertType.VEC2INT,
                                  [(IMAGE_SIZE_DEFAULT, IMAGE_SIZE_DEFAULT)],
                                  IMAGE_SIZE_MIN, IMAGE_SIZE_MAX)

        matte = parse_param(kw, 'matte', EnumConvertType.VEC4INT, [(0, 0, 0, 255)], 0, 255)

        edge_x = parse_param(kw, 'edge_x', EnumEdgeWrap, EnumEdgeWrap.CLAMP.name)
        edge_y = parse_param(kw, 'edge_y', EnumEdgeWrap, EnumEdgeWrap.CLAMP.name)
        edge = [(edge_x[idx], edge_y[idx]) for idx in range(len(edge_x))]

        iFrame = parse_param(kw, 'iFrame', EnumConvertType.FLOAT, 0)
        iFrameRate = parse_param(kw, 'iFrameRate', EnumConvertType.INT, 24)
        iTime = parse_param(kw, 'iTime', EnumConvertType.INT, -1)
        seed = parse_param(kw, 'seed', EnumConvertType.INT, 0)
        # batch is a single value entry -- drives everyone else.
        batch = parse_param(kw, 'batch', EnumConvertType.INT, 1, 1, 1048576)[0]

        variables = kw.copy()
        for k in ['iRes', 'iFrame', 'iFrameRate', 'iTime', 'matte', 'edge_x', 'edge_y', 'batch', 'seed']:
            variables.pop(k, None)

        if self.__glsl is None:
            try:
                vertex = getattr(self, 'VERTEX', kw.pop('VERTEX', None))
                fragment = getattr(self, 'FRAGMENT', kw.pop('FRAGMENT', None))
            except Exception as e:
                logger.error(self.NAME)
                logger.error(e)
                return

            self.__glsl = GLSLShader(self, vertex, fragment)

        defines = self.INPUT_TYPES()['optional']
        for k in variables.keys():
            variables[k] = parse_param(variables, k, EnumConvertType.ANY, None)
            if defines[k][1].get('rgb', False):
                ret = []
                for v in variables[k]:
                    ret.append([a/255.0 for a in v])
                variables[k] = ret
            batch = max(batch, len(variables[k]))

        start_frame = iFrame[0]
        for x in range(1, batch):
            iFrame.append(start_frame + x)
        iTime = [frame/rate for (frame, rate) in list(zip_longest_fill(iFrame, iFrameRate))]

        images = []
        # iResolution, iFrame, iFrameRate, iTime, iSeed
        params = list(zip_longest_fill(iResolution, iFrame, iFrameRate, iTime, matte, edge, seed))
        pbar = ProgressBar(len(params))
        # logger.debug(f"batch size {batch} :: param count {len(params)}")
        for idx, (iResolution, iFrame, iFrameRate, iTime, matte, edge, seed) in enumerate(params):
            vars = {}
            firstImage = None
            for k in variables.keys():
                vars[k] = variables[k][idx % len(variables[k])]
                if isinstance(vars[k], (TensorType,)):
                    vars[k] = tensor_to_cv(vars[k])
                    if firstImage is None and 'iRes' not in self.CONTROL:
                        firstImage = True
                        iResolution = vars[k].shape[:2][::-1]

            coreVar = {
                'iResolution': iResolution,
                'iFrame': iFrame,
                'iFrameRate': iFrameRate,
                'iTime': iTime,
                'batch': idx,
                'matte': matte,
                'edge': edge,
                'seed': seed
            }

            img = self.__glsl.render(coreVar, **vars)
            images.append(cv_to_tensor_full(img, matte))
            pbar.update_absolute(idx)
        return image_stack(images)
