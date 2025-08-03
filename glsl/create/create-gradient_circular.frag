// name: CIRCULAR GRADIENT
// desc: Generate a two color circular gradient
// category: CREATE
// control: res,

uniform vec4 start;   // 0,0,0,255;;;; rgb  | Start color
uniform vec4 end;     // ;;;         ; rgba | End color
uniform vec2 center;  // 0.5,0.5; 0; 1      | Center point
uniform float radius; // 0.5;     0; 1      | Max distance to outer edge
uniform bool reverse; //                    | Reverse the starting direction

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 uv = fragCoord / iResolution.xy;
    float dist = distance(uv, center);
    float pos = clamp(dist / radius, 0.0, 1.0);
    if (reverse) {
        pos = 1.0 - pos;
    }
    fragColor = mix(end, start, pos);

}
