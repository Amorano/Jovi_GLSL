"""
Jovi_GLSL - http://www.github.com/Amorano/Jovi_GLSL
GLSL Enumerations
"""

from enum import Enum

# ==============================================================================
# === ENUMERATION ===
# ==============================================================================

"""
Enumerations exposed to the shader scripts
"""
class EnumGLSLColorConvert(Enum):
    RGB2HSV = 0
    RGB2LAB = 1
    RGB2XYZ = 2
    HSV2RGB = 10
    HSV2LAB = 11
    HSV2XYZ = 12
    LAB2RGB = 20
    LAB2HSV = 21
    LAB2XYZ = 22
    XYZ2RGB = 30
    XYZ2HSV = 31
    XYZ2LAB = 32
