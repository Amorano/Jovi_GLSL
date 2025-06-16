// name: NOISE WORLEY BATCH
// desc: Worley (cellular) noise with batch output
// category: NOISE
// control: res, seed, batch

#include .lib/noise/noise_param.lib
#include .lib/noise/noise_worley.lib

uniform float frequency;   // 1.;  1.; 100.; 0.01  | Base frequency multiplier
uniform float amplitude;   // 1.;  1.; 100.; 0.01  | Base amplitude multiplier
uniform int   octaves;     // 4;   1;   12;  1     | Number of octaves
uniform float lacunarity;  // 2.;  0.; 100.; 0.01  | Frequency multiplier per octave
uniform float persistence; // 0.5; 0.; 100.; 0.01  | Amplitude multiplier per octave (same as 'gain' in some functions)
uniform float offset;      // 0.;  0.; 100.; 0.01  | For ridge noise
uniform float speed;       // 1.;  0.; 100.; 0.01  | Speed of noise variation

void mainImage( out vec4 fragColor, in vec2 fragCoord ) {
    vec2 uv = fragCoord / iResolution.xy;
    
    // Create 3D coordinates for the noise function
    vec3 p = vec3(uv * frequency, iTime * speed);
    
    // Use octaves as the number of cells for Worley noise
    float worley = noise_worley(p, octaves);
    
    // Apply amplitude scaling
    worley *= amplitude;
    
    fragColor = vec4(worley, worley, worley, 1.);
} 