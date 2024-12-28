// name: CONICAL GRADIENT
// desc: Generate a conical gradient from black to white
// category: CREATE
// control: res,

#include .lib/const.lib

uniform vec2 origin; // 0.5,0.5; 0; 1; 0.01 | Intensity of base normal
uniform vec2 range;  // 0.0,1.0; 0; 1; 0.01 | start of range. 0=start. size of range. 1=full range.
uniform float angle; // 0.0; ; ; 0.5 | offset of the gradient starting angle

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 uv = fragCoord / iResolution.xy - origin;
    float normAngle = atan(uv.y, uv.x) - (angle * M_TAU / 360);
    float t = fract(normAngle * M_TAU_INV);
    float norm = mix(range.x, range.y, t);
    fragColor = vec4(norm, norm, norm, 1.0);
}