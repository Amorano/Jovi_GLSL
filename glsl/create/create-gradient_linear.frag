// name: LINEAR GRADIENT
// desc: Generate a two color linear gradient
// category: CREATE
// control: res,

uniform ivec4 start;   // 0,0,0,255;       0; 255;; rgb | start color
uniform ivec4 end;     // 255,255,255,255; 0; 255;; rgb | end color
uniform bool vertical; //                               | if the gradient is top-bottom
uniform bool reverse;  //                               | reverse the starting direction

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec4 color_start = start / 255.0;
    vec4 color_end = end / 255.0;
    vec2 uv = fragCoord / iResolution.xy;
    float pos = vertical ? uv.y : uv.x;
    if (reverse) {
        pos = 1.0 - pos;
    }
    fragColor = mix(color_start, color_end, pos);
}
