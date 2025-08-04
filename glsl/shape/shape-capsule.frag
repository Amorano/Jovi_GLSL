// name: SHAPE: CAPSULE
// desc: Create an capsule with adjustable ends
// category: SHAPE
// control: res, edge,

#include .lib/sdf.lib
#include .lib/vector.lib

// default; min; max; step; metadata; tooltip
uniform sampler2D imageA; //                           | MASK, RGB or RGBA
uniform vec2 center;      // 0.5,0.5  ;-0.5 ;0.5 ;0.01 | positional offset (-0.5..0.5)
uniform float radius;     // 0.5      ;0    ;1   ;0.01 | radius (0...1.)
uniform vec2 cap_a;       // -0.25,0. ;-0.5 ;0.5 ;0.01 | endcap a
uniform vec2 cap_b;       // 0.25,0.  ;-0.5 ;0.5 ;0.01 | endcap b
uniform float rotate;     // 0;;                 ;0.1  | rotation from 0..2pi
uniform vec4 color;       // ;;;                 ;rgba | color
uniform bool invert;      //                           | invert the shape

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 uv = fragCoord / iResolution.xy;
    vec2 rotatedUV = vec_rotation(center - uv, rotate);
    float d = sdf_capsule(rotatedUV, radius * 0.25, -cap_a, -cap_b);
    fragColor = sdf_blend(d, imageA, uv, color, invert);
}
