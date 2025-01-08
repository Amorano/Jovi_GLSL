"""
Jovi_GLSL - http://www.github.com/Amorano/Jovi_GLSL
Core
"""

import os
import re
import json
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union, Generator

import cv2
import torch
import numpy as np
from loguru import logger

from .. import JOV_TYPE_ANY, ROOT, \
    JOVBaseNode, \
    load_file

# ==============================================================================
# === SHADER LOADER ===
# ==============================================================================

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
# === EXCEPTION ===
# ==============================================================================

class CompileException(Exception): pass

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

class JOVBaseGLSLNode(JOVBaseNode):
    NOT_IDEMPOTENT = True
    RETURN_TYPES = ("IMAGE", "IMAGE", "MASK")
    RETURN_NAMES = ('RGBA', 'RGB', 'MASK')
    FUNCTION = "run"

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        d = super().INPUT_TYPES()
        d = deep_merge(d, {
            "outputs": {
                0: ("IMAGE", {"tooltips":"Full channel [RGBA] image. If there is an alpha, the image will be masked out with it when using this output."}),
                1: ("IMAGE", {"tooltips":"Three channel [RGB] image. There will be no alpha."}),
                2: ("MASK", {"tooltips":"Single channel mask output."}),
            }
        })
        return d

# ==============================================================================
# === CONSTANT ===
# ==============================================================================

RE_VARIABLE = re.compile(r"uniform\s+(\w+)\s+(\w+);\s*(?:\/\/\s*([^;|]*))?\s*(?:;\s*([^;|]*))?\s*(?:;\s*([^;|]*))?\s*(?:;\s*([^;|]*))?\s*(?:;\s*([^;|]*))?\s*(?:\|\s*(.*))?$", re.MULTILINE)

IMAGE_SIZE_DEFAULT: int = 512
IMAGE_SIZE_MIN: int = 64
IMAGE_SIZE_MAX: int = 8192

# ==============================================================================
# === ENUMERATION ===
# ==============================================================================

class EnumConvertType(Enum):
    BOOLEAN = 1
    FLOAT = 10
    INT = 12
    VEC2 = 20
    VEC2INT = 25
    VEC3 = 30
    VEC3INT = 35
    VEC4 = 40
    VEC4INT = 45
    COORD2D = 22
    STRING = 0
    LIST = 2
    DICT = 3
    IMAGE = 4
    LATENT = 5
    # ENUM = 6
    ANY = 9
    MASK = 7
    # MIXLAB LAYER
    LAYER = 8

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

# ==============================================================================
# === TYPE ===
# ==============================================================================

TYPE_fCOORD2D = Tuple[float, float]

TYPE_iRGB  = Tuple[int, int, int]
TYPE_iRGBA = Tuple[int, int, int, int]
TYPE_fRGB  = Tuple[float, float, float]
TYPE_fRGBA = Tuple[float, float, float, float]

TYPE_PIXEL = Union[int, float, TYPE_iRGB, TYPE_iRGBA, TYPE_fRGB, TYPE_fRGBA]
TYPE_IMAGE = Union[np.ndarray, torch.Tensor]

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

# ==============================================================================
# === SUPPORT ===
# ==============================================================================

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

def parse_value(val:Any, typ:EnumConvertType, default: Any,
                clip_min: Optional[float]=None, clip_max: Optional[float]=None,
                zero:int=0) -> List[Any]:
    """Convert target value into the new specified type."""

    if typ == EnumConvertType.ANY:
        return val

    if isinstance(default, torch.Tensor) and typ not in [EnumConvertType.IMAGE,
                                                         EnumConvertType.MASK,
                                                         EnumConvertType.LATENT]:
        h, w = default.shape[:2]
        cc = default.shape[2] if len(default.shape) > 2 else 1
        default = (w, h, cc)

    if val is None:
        if default is None:
            return None
        val = default

    if isinstance(val, dict):
        # old index?
        if '0' in val or 0 in val:
            val = [val.get(i, val.get(str(i), 0)) for i in range(min(len(val), 4))]
        # coord2d?
        elif 'x' in val:
            val = [val.get(c, 0) for c in 'xyzw']
        # wacky color struct?
        elif 'r' in val:
            val = [val.get(c, 0) for c in 'rgba']
    elif isinstance(val, torch.Tensor) and typ not in [EnumConvertType.IMAGE,
                                                       EnumConvertType.MASK,
                                                       EnumConvertType.LATENT]:
        h, w = val.shape[:2]
        cc = val.shape[2] if len(val.shape) > 2 else 1
        val = (w, h, cc)

    new_val = val
    if typ in [EnumConvertType.FLOAT, EnumConvertType.INT,
            EnumConvertType.VEC2, EnumConvertType.VEC2INT,
            EnumConvertType.VEC3, EnumConvertType.VEC3INT,
            EnumConvertType.VEC4, EnumConvertType.VEC4INT,
            EnumConvertType.COORD2D]:

        if not isinstance(val, (list, tuple, torch.Tensor)):
            val = [val]
        elif isinstance(val, (tuple, )):
            val = list(val)

        size = max(1, int(typ.value / 10))
        new_val = []
        for idx in range(size):
            try:
                d = default[idx] if idx < len(default) else 0
            except:
                try:
                    d = default.get(str(idx), 0)
                except:
                    d = default

            v = d if val is None else val[idx] if idx < len(val) else d
            if isinstance(v, (str, )):
                v = v.strip('\n').strip()
                if v == '':
                    v = 0

            try:
                if typ in [EnumConvertType.FLOAT, EnumConvertType.VEC2, EnumConvertType.VEC3, EnumConvertType.VEC4]:
                    v = round(float(v or 0), 16)
                else:
                    v = int(v)
                if clip_min is not None:
                    v = max(v, clip_min)
                if clip_max is not None:
                    v = min(v, clip_max)
            except Exception as e:
                logger.exception(e)
                logger.error(f"Error converting value: {val} -- {v}")
                v = 0

            if v == 0:
                v = zero
            new_val.append(v)
        new_val = new_val[0] if size == 1 else tuple(new_val)
    elif typ == EnumConvertType.DICT:
        try:
            if isinstance(new_val, (str,)):
                try:
                    new_val = json.loads(new_val)
                except json.decoder.JSONDecodeError:
                    new_val = {}
            else:
                if not isinstance(new_val, (list, tuple,)):
                    new_val = [new_val]
                new_val = {i: v for i, v in enumerate(new_val)}
        except Exception as e:
            logger.exception(e)
    elif typ == EnumConvertType.LIST:
        new_val = list(new_val)
    elif typ == EnumConvertType.STRING:
        if isinstance(new_val, (str, list, int, float,)):
            new_val = [new_val]
        new_val = ", ".join(map(str, new_val)) if not isinstance(new_val, str) else new_val
    elif typ == EnumConvertType.BOOLEAN:
        if isinstance(new_val, (torch.Tensor,)):
            new_val = True
        elif isinstance(new_val, (dict,)):
            new_val = len(new_val.keys()) > 0
        elif isinstance(new_val, (list, tuple,)) and len(new_val) > 0 and (nv := new_val[0]) is not None:
            if isinstance(nv, (bool, str,)):
                new_val = bool(nv)
            elif isinstance(nv, (int, float,)):
                new_val = nv > 0
    elif typ == EnumConvertType.LATENT:
        # covert image into latent
        if isinstance(new_val, (torch.Tensor,)):
            new_val = {'samples': new_val.unsqueeze(0)}
        else:
            # convert whatever into a latent sample...
            new_val = torch.empty((4, 64, 64), dtype=torch.uint8).unsqueeze(0)
            new_val = {'samples': new_val}
    elif typ == EnumConvertType.IMAGE:
        # covert image into image? just skip if already an image
        if not isinstance(new_val, (torch.Tensor,)):
            color = parse_value(new_val, EnumConvertType.VEC4INT, (0,0,0,255), 0, 255)
            color = torch.tensor(color, dtype=torch.int32).tolist()
            new_val = torch.empty((IMAGE_SIZE_MIN, IMAGE_SIZE_MIN, 4), dtype=torch.uint8)
            new_val[0,:,:] = color[0]
            new_val[1,:,:] = color[1]
            new_val[2,:,:] = color[2]
            new_val[3,:,:] = color[3]
    elif typ == EnumConvertType.MASK:
        # @TODO: FIX FOR MULTI-CHAN?
        if not isinstance(new_val, (torch.Tensor,)):
            color = parse_value(new_val, EnumConvertType.INT, 0, 0, 255)
            color = torch.tensor(color, dtype=torch.int32).tolist()
            new_val = torch.empty((IMAGE_SIZE_MIN, IMAGE_SIZE_MIN, 1), dtype=torch.uint8)
            new_val[0,:,:] = color

    elif issubclass(typ, Enum):
        new_val = typ[val]

    if typ == EnumConvertType.COORD2D:
        new_val = {'x': new_val[0], 'y': new_val[1]}
    return new_val

def parse_param(data:dict, key:str, typ:EnumConvertType, default: Any,
                clip_min: Optional[float]=None, clip_max: Optional[float]=None,
                zero:int=0) -> List[Any]:
    """Convenience because of the dictionary parameters.
    Convert list of values into a list of specified type.
    """
    val = data.get(key, default)
    if typ == EnumConvertType.ANY:
        if val is None:
            val = [default]
            return val
        elif isinstance(val, (list,)):
            val = val[0]

    if isinstance(val, (str,)):
        try: val = json.loads(val.replace("'", '"'))
        except json.JSONDecodeError: pass
    # see if we are a hacked vector blob... {0:x, 1:y, 2:z, 3:w}
    elif isinstance(val, dict):
        # mixlab layer?
        if (image := val.get('image', None)) is not None:
            ret = image
            if (mask := val.get('mask', None)) is not None:
                while len(mask.shape) < len(image.shape):
                    mask = mask.unsqueeze(-1)
                ret = torch.cat((image, mask), dim=-1)
            if ret.ndim > 3:
                val = [t for t in ret]
            elif ret.ndim == 3:
                val = [v.unsqueeze(-1) for v in ret]
        # vector patch....
        elif 'xyzw' in val:
            val = tuple(x for x in val["xyzw"])
        # latents....
        elif 'samples' in val:
            val = tuple(x for x in val["samples"])
        elif ('0' in val) or (0 in val):
            val = tuple(val.get(i, val.get(str(i), 0)) for i in range(min(len(val), 4)))
        elif 'x' in val and 'y' in val:
            val = tuple(val.get(c, 0) for c in 'xyzw')
        elif 'r' in val and 'g' in val:
            val = tuple(val.get(c, 0) for c in 'rgba')
        elif len(val) == 0:
            val = tuple()
    elif isinstance(val, (torch.Tensor,)):
        # a batch of RGB(A)
        if val.ndim > 3:
            val = [t for t in val]
        # a batch of Grayscale
        else:
            val = [t.unsqueeze(-1) for t in val]
    elif isinstance(val, (list, tuple, set)):
        if isinstance(val, (tuple, set,)):
            val = list(val)
    elif issubclass(type(val), (Enum,)):
        val = [str(val.name)]

    if not isinstance(val, (list,)):
        val = [val]
    return [parse_value(v, typ, default, clip_min, clip_max, zero) for v in val]

# ==============================================================================
# === IMAGE SUPPORT ===
# ==============================================================================

def cv2tensor_full(image: TYPE_IMAGE, matte:TYPE_PIXEL=(0,0,0,255)) \
    -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:

    rgba = image_convert(image, 4)
    rgb = image_matte(rgba, matte)[...,:3]
    mask = image_mask(image)
    rgba = torch.from_numpy(rgba.astype(np.float32) / 255.0)
    rgb = torch.from_numpy(rgb.astype(np.float32) / 255.0)
    mask = torch.from_numpy(mask.astype(np.float32) / 255.0)
    return rgba, rgb, mask

def tensor2cv(tensor: torch.Tensor, invert_mask:bool=True) -> TYPE_IMAGE:
    """Convert a torch Tensor to a numpy ndarray."""
    if tensor.ndim > 3:
        raise Exception("Tensor is batch of tensors")

    if tensor.ndim < 3:
        tensor = tensor.unsqueeze(-1)

    if tensor.shape[2] == 1 and invert_mask:
        tensor = 1. - tensor

    tensor = tensor.cpu().numpy()
    return np.clip(255.0 * tensor, 0, 255).astype(np.uint8)

def image_convert(image: TYPE_IMAGE, channels: int, width: int=None, height: int=None,
                  matte: Tuple[int, ...]=(0, 0, 0, 255)) -> TYPE_IMAGE:
    """Force image format to a specific number of channels.
    Args:
        image (TYPE_IMAGE): Input image.
        channels (int): Desired number of channels (1, 3, or 4).
        width (int): Desired width. `None` means leave unchanged.
        height (int): Desired height. `None` means leave unchanged.
        matte (tuple): RGBA color to use as background color for transparent areas.
    Returns:
        TYPE_IMAGE: Image with the specified number of channels.
    """
    if image.ndim == 2:
        image = np.expand_dims(image, axis=-1)

    if (cc := image.shape[2]) != channels:
        if   cc == 1 and channels == 3:
            image = np.repeat(image, 3, axis=2)
        elif cc == 1 and channels == 4:
            rgb = np.repeat(image, 3, axis=2)
            alpha = np.full(image.shape[:2] + (1,), matte[3], dtype=image.dtype)
            image = np.concatenate([rgb, alpha], axis=2)
        elif cc == 3 and channels == 1:
            image = np.mean(image, axis=2, keepdims=True).astype(image.dtype)
        elif cc == 3 and channels == 4:
            alpha = np.full(image.shape[:2] + (1,), matte[3], dtype=image.dtype)
            image = np.concatenate([image, alpha], axis=2)
        elif cc == 4 and channels == 1:
            rgb = image[..., :3]
            alpha = image[..., 3:4] / 255.0
            image = (np.mean(rgb, axis=2, keepdims=True) * alpha).astype(image.dtype)
        elif cc == 4 and channels == 3:
            image = image[..., :3]

    # Resize if width or height is specified
    h, w = image.shape[:2]
    new_width = width if width is not None else w
    new_height = height if height is not None else h
    if (new_width, new_height) != (w, h):
        # Create a new image with the matte color
        new_image = np.full((new_height, new_width, channels), matte[:channels], dtype=image.dtype)
        paste_x = (new_width - w) // 2
        paste_y = (new_height - h) // 2
        new_image[paste_y:paste_y+h, paste_x:paste_x+w] = image[:h, :w]
        image = new_image

    return image

def image_crop(image: TYPE_IMAGE, width:int=None, height:int=None, offset:Tuple[float, float]=(0, 0)) -> TYPE_IMAGE:
    h, w = image.shape[:2]
    width = width if width is not None else w
    height = height if height is not None else h
    x, y = offset
    x = max(0, min(width, x))
    y = max(0, min(width, y))
    x2 = max(0, min(width, x + width))
    y2 = max(0, min(height, y + height))
    points = [(x, y), (x2, y), (x2, y2), (x, y2)]
    return image_crop_polygonal(image, points)

def image_crop_center(image: TYPE_IMAGE, width:int=None, height:int=None) -> TYPE_IMAGE:
    """Helper crop function to find the "center" of the area of interest."""
    h, w = image.shape[:2]
    cx = w // 2
    cy = h // 2
    width = w if width is None else width
    height = h if height is None else height
    x1 = max(0, int(cx - width // 2))
    y1 = max(0, int(cy - height // 2))
    x2 = min(w, int(cx + width // 2)) - 1
    y2 = min(h, int(cy + height // 2)) - 1
    points = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    return image_crop_polygonal(image, points)

def image_crop_polygonal(image: TYPE_IMAGE, points: List[TYPE_fCOORD2D]) -> TYPE_IMAGE:
    cc = image.shape[2] if image.ndim == 3 else 1
    height, width = image.shape[:2]
    point_mask = np.zeros((height, width), dtype=np.uint8)
    points = np.array(points, np.int32).reshape((-1, 1, 2))
    point_mask = cv2.fillPoly(point_mask, [points], 255)
    x, y, w, h = cv2.boundingRect(point_mask)
    cropped_image = cv2.resize(image[y:y+h, x:x+w], (w, h)).astype(np.uint8)
    # Apply the mask to the cropped image
    point_mask_cropped = cv2.resize(point_mask[y:y+h, x:x+w], (w, h))
    if cc == 4:
        mask = image_mask(image, 0)
        alpha_channel = cv2.resize(mask[y:y+h, x:x+w], (w, h))
        cropped_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGRA2BGR)
        cropped_image = cv2.bitwise_and(cropped_image, cropped_image, mask=point_mask_cropped)
        return image_mask_add(cropped_image, alpha_channel)
    elif cc == 1:
        cropped_image = cv2.cvtColor(cropped_image, cv2.COLOR_GRAY2BGR)
        cropped_image = cv2.bitwise_and(cropped_image, cropped_image, mask=point_mask_cropped)
        return image_convert(cropped_image, cc)
    return cv2.bitwise_and(cropped_image, cropped_image, mask=point_mask_cropped)

def image_mask(image: TYPE_IMAGE, color: TYPE_PIXEL = 255) -> TYPE_IMAGE:
    """Create a mask from the image, preserving transparency.

    Args:
        image (TYPE_IMAGE): Input image, assumed to be 2D or 3D (with or without alpha channel).
        color (TYPE_PIXEL): Value to fill the mask (default is 255).

    Returns:
        TYPE_IMAGE: Mask of the image, either the alpha channel or a full mask of the given color.
    """
    if image.ndim == 3 and image.shape[2] == 4:
        return image[..., 3]

    h, w = image.shape[:2]
    return np.ones((h, w), dtype=np.uint8) * color

def image_mask_add(image:TYPE_IMAGE, mask:TYPE_IMAGE=None, alpha:float=255) -> TYPE_IMAGE:
    """Put custom mask into an image. If there is no mask, alpha is applied.
    Images are expanded to 4 channels.
    Existing 4 channel images with no mask input just return themselves.
    """
    image = image_convert(image, 4)
    mask = image_mask(image, alpha) if mask is None else image_convert(mask, 1)
    image[..., 3] = mask if mask.ndim == 2 else mask[:, :, 0]
    return image

def image_matte(image: TYPE_IMAGE, color: TYPE_iRGBA=(0,0,0,255), width: int=None, height: int=None) -> TYPE_IMAGE:
    """
    Puts an RGBA image atop a colored matte expanding or clipping the image if requested.

    Args:
        image (TYPE_IMAGE): The input RGBA image.
        color (TYPE_iRGBA): The color of the matte as a tuple (R, G, B, A).
        width (int, optional): The width of the matte. Defaults to the image width.
        height (int, optional): The height of the matte. Defaults to the image height.

    Returns:
        TYPE_IMAGE: Composited RGBA image on a matte with original alpha channel.
    """

    #if image.ndim != 4 or image.shape[2] != 4:
    #    return image

    # Determine the dimensions of the image and the matte
    image_height, image_width = image.shape[:2]
    width = width or image_width
    height = height or image_height

    # Create a solid matte with the specified color
    matte = np.full((height, width, 4), color, dtype=np.uint8)

    # Extract the alpha channel from the image
    alpha = None
    if image.ndim == 3 and image.shape[2] == 4:
        alpha = image[:, :, 3] / 255.0

    # Calculate the center position for the image on the matte
    x_offset = (width - image_width) // 2
    y_offset = (height - image_height) // 2

    if alpha is not None:
        # Place the image onto the matte using the alpha channel for blending
        for c in range(0, 3):
            matte[y_offset:y_offset + image_height, x_offset:x_offset + image_width, c] = \
                (1 - alpha) * matte[y_offset:y_offset + image_height, x_offset:x_offset + image_width, c] + \
                alpha * image[:, :, c]

        # Set the alpha channel of the matte to the maximum of the matte's and the image's alpha
        matte[y_offset:y_offset + image_height, x_offset:x_offset + image_width, 3] = \
            np.maximum(matte[y_offset:y_offset + image_height, x_offset:x_offset + image_width, 3], image[:, :, 3])
    else:
        image = image[y_offset:y_offset + image_height, x_offset:x_offset + image_width, :]
    return matte
