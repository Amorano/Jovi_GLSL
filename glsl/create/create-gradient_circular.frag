// name: CIRCULAR GRADIENT
// desc: Generate a two color circular gradient
// category: CREATE
// control: res,

uniform vec4 start;   // 0,0,0,255;       0; 255;; rgb | Start color
uniform vec4 end;     // 255,255,255,255; 0; 255;; rgb | End color
uniform vec2 center;  // 0.5,0.5;         0; 1         | Center point
uniform float radius; // 0.5;             0; 1         | Max distance to outer edge
uniform bool reverse; //                               | Reverse the starting direction

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec4 color_start = start / 255.0;
    vec4 color_end = end / 255.0;
    vec2 uv = fragCoord / iResolution.xy;
    float dist = distance(uv, center);
    float pos = clamp(dist / radius, 0.0, 1.0);
    if (reverse) {
        pos = 1.0 - pos;
    }
    fragColor = mix(color_end, color_start, pos);

}
