// name: NORMAL
// desc: Convert input into a Normal map
// category: CREATE

#include .lib/shading.lib

uniform sampler2D image; //         | Input image to convert into a normal map
uniform float scalar;    // 1.00; 0 | Intensity of base normal
uniform float detail;    // 1.00; 0 | Intensity of detail normal
uniform bool flip;       //         | Reverse the Normal direction

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 uv = fragCoord / iResolution.xy;

    // detailed normal
    vec3 normal = vec3(0.0, 0.0, 1.0);
    normal.xy = shading_normal_scharr(image, uv, detail).xy * scalar;
    if (flip) {
        normal.xy = normal.yx;
    }
    normal.x *= -scalar;
    normal = normalize(normal) * 0.5 + 0.5;
    fragColor = vec4(normal, 1.0);
}