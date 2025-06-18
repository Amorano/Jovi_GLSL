// name: NOISE WORLEY
// desc: Worley (cellular) noise with batch output
// category: NOISE
// control: res, seed, batch

#include .lib/noise/noise_param.lib
#include .lib/noise/noise_worley.lib

uniform float frequency; //   1; 1; 100; 0.01 | Base frequency multiplier
uniform float amplitude; //   1; 0; 100; 0.01 | Base amplitude multiplier
uniform int   octaves;   //   4; 1;  12;    1 | Number of octaves
uniform vec2  offset;    // 0,0;  ;    ; 0.01 | Positional offset
uniform float speed;     //   0; 0; 100; 0.01 | Speed of noise variation

void mainImage( out vec4 fragColor, in vec2 fragCoord ) {
    vec2 uv = fragCoord / iResolution.xy;

    // Create 3D coordinates for the noise function
    vec3 pos = vec3(uv + offset.xy, iTime * speed);

    // Use octaves as the number of cells for Worley noise
    float worley = noise_worley(pos * frequency, octaves, iSeed);

    // Apply amplitude scaling
    worley *= amplitude;

    fragColor = vec4(worley, worley, worley, 1.);
}