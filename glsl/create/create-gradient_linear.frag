// name: LINEAR GRADIENT
// desc: Generate a two color linear gradient
// category: CREATE
// control: res,

uniform vec4 start;    // 0,0,0,255;;;; rgb | start color
uniform vec4 end;      // ;;;; rgba         | end color
uniform bool vertical; //                   | if the gradient is top-bottom
uniform bool reverse;  //                   | reverse the starting direction

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 uv = fragCoord / iResolution.xy;
    float pos = vertical ? uv.y : uv.x;
    if (reverse) {
        pos = 1.0 - pos;
    }
    fragColor = mix(start, end, pos);
}
