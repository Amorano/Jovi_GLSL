// name: TRANSFORM
// desc: Move, Rotate, Scale and Tile an image
// category: TRANSFORM
// control: edge

#include .lib/vector.lib

uniform sampler2D image; //                           | RGB(A) input to repeat
uniform vec2 offset;     // 0.0,0.0; -0.5;  0.5; 0.01 | positional offset (-0.5..0.5)
uniform float rotate;    // 0      ;     ;     ; 0.1  | rotation from 0..2pi
uniform vec2 tile;       // 1.0,1.0;    1; 2048; 1    | repetitions on X and Y

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    // normalize + offset
    vec2 uv = (fragCoord - offset * iResolution.xy) / iResolution.xy;

	// center rotate
    uv = vec_rotation(-rotate) * (uv - 0.5) + 0.5;

    // scale
	vec2 repeat = vec2(min(iResolution.x / 4., tile.x), min(iResolution.y / 4., tile.y));
    uv *= repeat;
    fragColor = texture(image, uv);
}