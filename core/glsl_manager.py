""" Jovi_GLSL - GLSL Manager """

import gc

import glfw

from cozy_comfyui import \
    logger

from cozy_comfyui.node import \
    Singleton

# ==============================================================================
# === SUPPORT ===
# ==============================================================================

def error_callback(error, description):
    logger.error(f"GLFW Error ({error}): {description}")

# ==============================================================================
# === CLASS ===
# ==============================================================================

class GLSLManager(metaclass=Singleton):
    """GLFW initialization and global shader resources"""

    def __init__(self):
        if not glfw.init():
                raise RuntimeError("GLFW failed to initialize")
        self.__active_shaders = set()
        logger.debug(f"GLSL Manager init")
        glfw.set_error_callback(error_callback)

    def register_shader(self, node, shader):
        gc.collect()
        self.__active_shaders.add(shader)
        logger.debug(f"{node.NAME} registered")

    def unregister_shader(self, shader):
        self.__active_shaders.discard(shader)
        logger.debug(f"{shader} unregistered")
