<div align="center">

<picture>
  <source srcset="https://raw.githubusercontent.com/Amorano/Jovimetrix-examples/refs/heads/master/res/logo-jovi_glsl.png">
  <img alt="ComfyUI Nodes for creating GLSL shaders" width="256" height="256">
</picture>

</div>

<div align="center">

<a href="https://github.com/comfyanonymous/ComfyUI">COMFYUI</a> Nodes for creating GLSL shaders

</div>

<div align="center">

![KNIVES!](https://badgen.net/github/open-issues/Amorano/JOVI_GLSL)
![FORKS!](https://badgen.net/github/forks/Amorano/JOVI_GLSL)

</div>

<!---------------------------------------------------------------------------->

# SPONSORSHIP

Please consider sponsoring me if you enjoy the results of my work, code or documentation or otherwise. A good way to keep code development open and free is through sponsorship.

<div align="center">

&nbsp;|&nbsp;|&nbsp;|&nbsp;
-|-|-|-
[![BE A GITHUB SPONSOR ❤️](https://img.shields.io/badge/sponsor-30363D?style=for-the-badge&logo=GitHub-Sponsors&logoColor=#EA4AAA)](https://github.com/sponsors/Amorano) | [![DIRECTLY SUPPORT ME VIA PAYPAL](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://www.paypal.com/paypalme/onarom) | [![PATREON SUPPORTER](https://img.shields.io/badge/Patreon-F96854?style=for-the-badge&logo=patreon&logoColor=white)](https://www.patreon.com/joviex) | [![SUPPORT ME ON KO-FI!](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/alexandermorano)
</div>

## HIGHLIGHTS

* `Dynamic GLSL` Nodes compiles existing GLSL script files into ComfyUI nodes at load time
* Support for 2, 3 and 4 tuple sized vectors (integer or float)
* RGB/RGBA color vector support with access to the system/browser level color picker
* All `Image` inputs/outputs on `Dynamic GLSL` nodes support RGB, RGBA or pure MASK input
* Dozens of hand written GLSL nodes to speed up specific tasks better done on the GPU (10x speedup in most cases)
* Over a 100+ functions in the GLSL library supports to freely use

## UPDATES

**2025/04/22** @1.1.33:
* realigned categories

**2025/04/19** @1.1.32:
* removed old vector conversions waiting for new frontend mechanism

**2025/04/14** @1.1.31:
* force fixed import problem in comfyui

**2025/04/13** @1.1.30:
* core supports switched to [cozy_comfyui](https://github.com/cozy-comfyui/cozy_comfyui)
* updated requirements for numpy to be < 2.0.0

**2025/03/28** @1.1.27:
* updated requirements for numpy to only be >=1.26.4

# INSTALLATION

[Please see the wiki for advanced use of the environment variables that can be used at startup](https://github.com/Amorano/Jovi_GLSL/wiki)

## COMFYUI MANAGER

If you have [ComfyUI Manager](https://github.com/ltdrdata/ComfyUI-Manager) installed, simply search for Jovi_GLSL and install from the manager's database.

## MANUAL INSTALL
Clone the repository into your ComfyUI custom_nodes directory. You can clone the repository with the command:
```
git clone https://github.com/Amorano/Jovi_GLSL.git
```
You can then install the requirements by using the command:
```
.\python_embed\python.exe -s -m pip install -r .\ComfyUI\custom_nodes\Jovi_GLSL\requirements.txt
```
If you are using a <code>virtual environment</code> (<code><i>venv</i></code>), make sure it is activated before installation. Then install the requirements with the command:
```
pip install -r .\ComfyUI\custom_nodes\Jovi_GLSL\requirements.txt
```
## ENVIRONMENT

### CUSTOM SHADERS

You are able to add your own shaders such that they compile into nodes at ComfyUI load time. Custom shaders that are local to your machine will have a 🦄 (uniforn emoji) at the end of their name. The default location for local shaders is to search a folder in the root of Jovimetrix:

`<ComfyUI>/custom_nodes/Jovi_GLSL/user`

If you want to change the search location, you can set the environment variable:

`SET JOV_GLSL=<location to glsl shader files>`

<!---------------------------------------------------------------------------->

Shaders are compiled and loaded at runtime via the `Dynamic GLSL` system. This will search a filepath for shader files, load them and compile them into nodes for ComfyUI. They will register as normal nodes and work in any API calls.

The benefit of the dynamic nodes are the reduced footprint of making explict nodes. Dynamic nodes load their scripts statically so the node only contains the inputs and widgets for that specific script.

# CORE

All shaders have two parts: a vertex shader (.vert) and a fragment shader (.frag).

The default location for the included shaders is:

`<ComfyUI>/custom_nodes/Jovi_GLSL/glsl`

The basic shaders for each of these programs is included in the default location and are named:

`_.frag` and `_.vert`

Shaders with a 🌈 (rainbow) icon at the end of their name are internal shaders that ship with this repository.
Shaders with a 🦄 (unicorn) icon at the end of their name are custom user shaders loaded from [the user directory](#custom-shaders).

## VERTEX SHADER

```
#version 330 core

precision highp float;

void main()
{
    vec2 verts[3] = vec2[](vec2(-1, -1), vec2(3, -1), vec2(-1, 3));
    gl_Position = vec4(verts[gl_VertexID], 0, 1);
}
```

The default vertex shader is simply a quad with the UV mapped from 0..1.

## FRAGMENT SHADER

```
#version 440

precision highp float;

// system globals
uniform vec3    iResolution;
uniform float   iTime;
uniform float   iFrameRate;
uniform int     iFrame;

// old deprecated functions
#define texture2D texture

// useful constants
#define M_EPSILON 1.0e-10
#define M_PI 3.1415926535897932384626433832795
#define M_TAU (2.0 * M_PI)
```

All shaders will have a header file, with pre-set variables for shader program usage, injected at the top. These are "mostly" mirrored from Shadertoy variables, with a few changes:

NAME | TYPE | USAGE
---|---|---
iResolution | vec3 | Width and Height dimensions of the GL canvas
iFrame | int | the current frame
iFrameRate | float | the desired FPS
iTime | float | current time in shader's lifetime based on `iFrameRate` and `iFrame`
iSeed | int | seed value for noise shaders

## ENTRY POINT

The fragment shader's entry point is defined as:

```
void mainImage(out vec4 fragColor, vec2 fragCoord)
```

such that setting fragColor will output the final RGBA value for the pixel.

## SHADER META

Shaders are 100% fully GLSL compatible; however, there can be additional information (meta data) added to the shaders via comments. This expands the usefulness of the shaders since they can be pre-parsed and turned into nodes made at runtime (Dynamic Nodes).

```
// name: GRAYSCALE
// desc: Convert input to grayscale
// category: COLOR
// control:
```

The meta data breakdown of this shader header:

KEY | USAGE | EXPLANATION
---|---|---
name | GRAYSCALE | title of the node with an added 🧙🏽 for internal and 🧙🏽‍♀️ for custom nodes
desc | Convert input to grayscale | text that shows up for preview nodes and the Jovimetrix help panel
category | COLOR | ComfyUI menu placement. Added to the end of `JOVI_GLSL 🦚`
control | Comma Seperated List | Explicit list of additional controls to add to the dynamic node. Possible values are included in the control list below.

### CONTROLS

The case of the controls doesnt matter when being parsed. The formats are just for clarity.

NAME | PURPOSE | DEFAULT
---|---|---
res | Width and Height | 512, 512
frame | Current frame to render | 0
frameRate | Used to calculate frame step size and iTime | 24
time | Value to use directly; if > -1 will override iFrame/iFrameRate calculation | -1
batch | Number of frames to generate | 0 (Continuous per queue)
matte | GL Clear or Background color | 0,0,0,255
edge | Clamp, Wrap or Mirror the image edge(s) | Clamp
seed | Seed value | 0

`UNIFORM fields` also have metadata about usage(clipping for number fields) and their tooltips:

```
// default grayscale using NTSC conversion weights
uniform sampler2D image; | MASK, RGB or RGBA
uniform vec3 convert; // 0.299, 0.587, 0.114; 0; 1; 0.01 | Scalar for each channel
```

`<default value> ; <minimum> ; <maximum>; <step> | <tooltip>`

For the convert uniform this means a vector3 field with a default value of `<0.299, 0.587, 0.114>` clipped in the range `0..1` with a `0.01` step when the user interacts with the mouse and the tooltip will read: `Scalar for each channel`

If you need to omit fields, like a minimum, just place the token separator (;) by itself, for example:

`uniform float num; // 0.5; ; 10`

This would allow the number to have a lower bound of -system maximum and clip the upper-bound at 10.

<!---------------------------------------------------------------------------->

# SPONSORSHIP

Please consider sponsoring me if you enjoy the results of my work, code or documentation or otherwise. A good way to keep code development open and free is through sponsorship.

<div align="center">

[![BE A GITHUB SPONSOR ❤️](https://img.shields.io/badge/sponsor-30363D?style=for-the-badge&logo=GitHub-Sponsors&logoColor=#EA4AAA)](https://github.com/sponsors/Amorano)

[![DIRECTLY SUPPORT ME VIA PAYPAL](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://www.paypal.com/paypalme/onarom)

[![PATREON SUPPORTER](https://img.shields.io/badge/Patreon-F96854?style=for-the-badge&logo=patreon&logoColor=white)](https://www.patreon.com/joviex)

[![SUPPORT ME ON KO-FI!](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/alexandermorano)

</div>

<!---------------------------------------------------------------------------->

# WHERE TO FIND ME

You can find me on [![DISCORD](https://dcbadge.vercel.app/api/server/62TJaZ3Z5r?style=flat-square)](https://discord.gg/62TJaZ3Z5r).
