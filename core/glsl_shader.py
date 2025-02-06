"""
Jovi_GLSL - http://www.github.com/Amorano/Jovi_GLSL
GLSL Shader
"""

import sys
from typing import Any, Dict, Tuple
from enum import Enum, EnumMeta as EnumType

import cv2
import glfw
import numpy as np
import OpenGL.GL as gl
from loguru import logger

from ..core import \
    IMAGE_SIZE_MAX, IMAGE_SIZE_MIN, PROG_VERTEX, \
    PROG_FRAGMENT, PROG_FOOTER, PROG_HEADER, PTYPE, RE_VARIABLE, \
    CompileException, EnumEdgeWrap, \
    image_convert, parse_value

from ..core.glsl_manager import GLSLManager

# ==============================================================================
# === GLOBAL ===
# ==============================================================================

LAMBDA_UNIFORM = {
    'bool': gl.glUniform1i,
    'int': gl.glUniform1i,
    'ivec2': gl.glUniform2i,
    'ivec3': gl.glUniform3i,
    'ivec4': gl.glUniform4i,
    'float': gl.glUniform1f,
    'vec2': gl.glUniform2f,
    'vec3': gl.glUniform3f,
    'vec4': gl.glUniform4f,
}

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

# ==============================================================================
# === CLASS ===
# ==============================================================================

class GLSLShader:
    def __init__(self, node, vertex:str=None, fragment:str=None) -> None:
        self.__glsl_manager = GLSLManager()
        self.__glsl_manager.register_shader(node, self)

        self.__size: Tuple[int, int] = (IMAGE_SIZE_MIN, IMAGE_SIZE_MIN)
        self.__textures = {}
        self.__uniform_state = {}
        self.__texture_hashes = {}

        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        self.__window = glfw.create_window(self.__size[0], self.__size[1], "hidden", None, None)
        if not self.__window:
            raise RuntimeError("GLFW did not init window")
        logger.debug("window created")

        glfw.make_context_current(self.__window)

        # framebuffer
        self.__fbo = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.__fbo)
        logger.debug("framebuffer created")

        self.__fbo_texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.__fbo_texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA32F,
                        self.__size[0], self.__size[1], 0,
                        gl.GL_RGBA, gl.GL_FLOAT, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.__fbo_texture, 0)
        gl.glViewport(0, 0, self.__size[0], self.__size[1])
        logger.debug("framebuffer texture created")

        self.__empty_image: np.ndarray = np.zeros((self.__size[0], self.__size[1]), np.uint8)
        self.__last_frame: np.ndarray = np.zeros((self.__size[0], self.__size[1]), np.uint8)
        self.__shaderVar = {}
        self.__userVar = {}
        self.__program = None

        try:
            if vertex is None:
                logger.debug("vertex program is empty. using default.")
                vertex = PROG_VERTEX
            vertex_shader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
            gl.glShaderSource(vertex_shader, vertex)
            gl.glCompileShader(vertex_shader)
            if gl.glGetShaderiv(vertex_shader, gl.GL_COMPILE_STATUS) != gl.GL_TRUE:
                raise CompileException(gl.glGetShaderInfoLog(vertex_shader).decode())
            logger.debug("vertex program ready")

            if fragment is None:
                logger.debug("fragment program is empty. using default.")
                fragment = PROG_FRAGMENT
            fragment_raw = PROG_HEADER + fragment + PROG_FOOTER

            fragment_shader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
            gl.glShaderSource(fragment_shader, fragment_raw)
            gl.glCompileShader(fragment_shader)
            if gl.glGetShaderiv(fragment_shader, gl.GL_COMPILE_STATUS) != gl.GL_TRUE:
                gl.glDeleteShader(vertex_shader)
                raise CompileException(gl.glGetShaderInfoLog(fragment_shader).decode())
            logger.debug("fragment program ready")

            self.__program = gl.glCreateProgram()
            gl.glAttachShader(self.__program, vertex_shader)
            gl.glAttachShader(self.__program, fragment_shader)
            gl.glLinkProgram(self.__program)
            logger.debug("program linked")

            # Clean up shaders after linking
            gl.glDeleteShader(vertex_shader)
            gl.glDeleteShader(fragment_shader)

            if gl.glGetProgramiv(self.__program, gl.GL_LINK_STATUS) != gl.GL_TRUE:
                raise CompileException(gl.glGetProgramInfoLog(self.__program).decode())

            gl.glUseProgram(self.__program)

            # Setup uniforms
            statics = ['iResolution', 'iFrame', 'iFrameRate', 'iTime', 'iBatch', 'iSeed']
            for s in statics:
                val = gl.glGetUniformLocation(self.__program, s)
                self.__shaderVar[s] = val

            logger.debug("uniforms initialized")

            # Setup user variables
            for match in RE_VARIABLE.finditer(fragment):
                typ, name, default, *_ = match.groups()

                texture = None
                if typ in ['sampler2D']:
                    texture = self.__textures[name] = gl.glGenTextures(1)
                elif default:
                    default = default.strip()
                    if default.startswith('EnumGLSL'):
                        typ = 'int'
                        default = getattr(sys.modules[__name__], default, 0)

                index = gl.glGetUniformLocation(self.__program, name)
                self.__userVar[name] = [typ, index, default, texture]

            logger.debug("user uniforms initialized")
        except Exception as e:
            self.__cleanup()
            logger.debug(fragment_raw)
            raise CompileException(f"shader compilation failed: {str(e)}")

    def __cleanup(self):
        """Explicit cleanup of OpenGL resources"""
        if hasattr(self, '_cleanup_called'):
            return
        self._cleanup_called = True

        if self.__window:
            glfw.make_context_current(self.__window)

        texture_ids = [v[3] for v in self.__userVar.values() if v[0] == 'sampler2D']
        if texture_ids:
            gl.glDeleteTextures(len(texture_ids), texture_ids)
            logger.debug("texture disposed")

        if self.__fbo_texture:
            gl.glDeleteTextures(1, [self.__fbo_texture])
            self.__fbo_texture = None
            logger.debug("framebuffer texture disposed")

        if self.__fbo:
            gl.glDeleteFramebuffers(1, [self.__fbo])
            self.__fbo = None
            logger.debug("framebuffer disposed")

        if self.__program:
            gl.glDeleteProgram(self.__program)
            self.__program = None
            logger.debug("program disposed")

        if self.__window:
            glfw.destroy_window(self.__window)
            logger.debug("window disposed")
        self.__window = None

        self.__glsl_manager.unregister_shader(self)

    def __del__(self):
        """Cleanup during garbage collection"""
        try:
            self.__cleanup()
        except:
            pass

    def render(self, coreVar: Dict[str, Any], **kw) -> np.ndarray:
        glfw.make_context_current(self.__window)
        gl.glUseProgram(self.__program)

        iTimeVal = coreVar['iTime']
        iFrame = coreVar['iFrame']
        iFrameRate = coreVar['iFrameRate']

        if iTimeVal == -1:
            iTimeVal = iFrame / iFrameRate
        else:
            iFrame = int(iFrameRate * iTimeVal)

        if (loc := self.__shaderVar['iFrame']) > -1:
            gl.glUniform1i(loc, iFrame)

        if (loc := self.__shaderVar['iFrameRate']) > -1:
            gl.glUniform1f(loc, iFrameRate)

        if (loc := self.__shaderVar['iTime']) > -1:
            gl.glUniform1f(loc, iTimeVal)

        if (loc := self.__shaderVar['iBatch']) > -1:
            gl.glUniform1f(loc, coreVar['batch'])

        if (loc := self.__shaderVar['iSeed']) > -1:
            gl.glUniform1i(loc, coreVar['seed'])

        iResolution = coreVar['iResolution']
        if iResolution[0] != self.__size[0] or iResolution[1] != self.__size[1]:
            iResolution = (
                min(IMAGE_SIZE_MAX, max(IMAGE_SIZE_MIN, iResolution[0])),
                min(IMAGE_SIZE_MAX, max(IMAGE_SIZE_MIN, iResolution[1]))
            )

            """Update framebuffer and texture sizes without recreating them"""
            glfw.make_context_current(self.__window)
            glfw.set_window_size(self.__window, iResolution[0], iResolution[1])

            # Bind existing FBO and texture
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.__fbo)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.__fbo_texture)

            # Update sizes
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA32F,
                        iResolution[0], iResolution[1], 0,
                        gl.GL_RGBA, gl.GL_FLOAT, None)
            gl.glViewport(0, 0, iResolution[0], iResolution[1])

            # Update internal buffers
            if self.__empty_image.shape != (iResolution[0], iResolution[1]):
                self.__empty_image = np.zeros((iResolution[0], iResolution[1]), np.uint8)
                self.__last_frame = np.zeros((iResolution[0], iResolution[1]), np.uint8)

            # Clear texture hashes to force texture updates at new size
            self.__texture_hashes.clear()

            logger.debug(f"iResolution {self.__size} ==> {iResolution}")
            self.__size = iResolution

            val = self.__shaderVar['iResolution']
            if (loc := self.__shaderVar['iResolution']) > -1:
                gl.glUniform3f(loc, self.__size[0], self.__size[1], 0)

        texture_index = -1
        for uk, uv in self.__userVar.items():
            p_type, p_loc, p_value, texture_id = uv
            val = kw.get(uk, p_value)

            if p_type == 'sampler2D':
                texture_index += 1
                if texture_id is None:
                    continue
                    if (texture := self.__textures.get(uk, None)) is None:
                        logger.error(f"texture [{texture_index}] {uk} is None")
                        texture_index += 1
                        continue

                gl.glActiveTexture(gl.GL_TEXTURE0 + texture_index)
                gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)

                if isinstance(val, np.ndarray):
                    current_hash = hash((val.ctypes.data, val.shape, val.dtype))
                else:
                    current_hash = hash(0)

                if uk not in self.__texture_hashes or self.__texture_hashes[uk] != current_hash:
                    val = image_convert(val, 4)
                    val = val[::-1,:]
                    val = val.astype(np.float32) / 255.0
                    val = cv2.resize(val, self.__size, interpolation=cv2.INTER_LINEAR)

                    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA32F, self.__size[0], self.__size[1], 0, gl.GL_RGBA, gl.GL_FLOAT, val)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

                    self.__texture_hashes[uk] = current_hash

                    # Set edge wrapping modes
                    for idx, text_wrap in enumerate([gl.GL_TEXTURE_WRAP_S, gl.GL_TEXTURE_WRAP_T]):
                        if coreVar['edge'][idx] == EnumEdgeWrap.WRAP:
                            gl.glTexParameteri(gl.GL_TEXTURE_2D, text_wrap, gl.GL_REPEAT)
                        elif coreVar['edge'][idx] == EnumEdgeWrap.MIRROR:
                            gl.glTexParameteri(gl.GL_TEXTURE_2D, text_wrap, gl.GL_MIRRORED_REPEAT)
                        else:
                            gl.glTexParameteri(gl.GL_TEXTURE_2D, text_wrap, gl.GL_CLAMP_TO_EDGE)

                gl.glUniform1i(p_loc, texture_index)
            else:
                if isinstance(p_value, EnumType):
                    val = p_value[val].value
                elif isinstance(val, str):
                    val = val.split(',')

                val = parse_value(val, PTYPE[p_type], 0)

                if not isinstance(val, (list, tuple, )):
                    val = [val]

                uk = (uk, p_loc)
                if uk not in self.__uniform_state or self.__uniform_state[uk] != val:
                    LAMBDA_UNIFORM[p_type](p_loc, *val)
                    self.__uniform_state[uk] = val

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.__fbo)
        matte = [c/255. for c in coreVar['matte']]
        gl.glClearColor(*matte)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 3)

        data = gl.glReadPixels(0, 0, self.__size[0], self.__size[1], gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)
        image = np.frombuffer(data, dtype=np.uint8).reshape(self.__size[1], self.__size[0], 4)
        self.__last_frame = image[::-1, :, :]

        glfw.poll_events()
        return self.__last_frame
