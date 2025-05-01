// name: BLOOM
// desc: Bloom filter pass
// category: FILTER

uniform sampler2D image; //                    | RGB(A) image
uniform float threshold; // 0.25; 0; 1;   0.01 | Brightness threshold to start the bloom effect
uniform float intensity; // 2;    0; 200; 0.01 | Ramp up to intensity of bloom
uniform float blurSize;  // 3;    0; 100; 0.01 | Number of pixels to fade effect across

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
	vec2 uv = (fragCoord.xy / iResolution.xy);
    vec4 color = texture(image, uv);
    vec2 texel = blurSize / vec2(iResolution.x, iResolution.y);
    vec4 pixel = texture(image, uv, blurSize);
    pixel += texture(image, uv + vec2(texel.x, 0.0), blurSize);
    pixel += texture(image, uv + vec2(-texel.x, 0.0), blurSize);
    pixel += texture(image, uv + vec2(0.0, texel.y), blurSize);
    pixel += texture(image, uv + vec2(0.0, -texel.y), blurSize);
    pixel += texture(image, uv + vec2(texel.x, texel.y), blurSize);
    pixel += texture(image, uv + vec2(-texel.x, texel.y), blurSize);
    pixel += texture(image, uv + vec2(texel.x, -texel.y), blurSize);
    pixel += texture(image, uv + vec2(-texel.x, -texel.y), blurSize);
    pixel /= 9.0;

    vec4 bloom = clamp(pixel - threshold, 0.0, 1.0) * 1.0 / (1.0 - threshold);
    fragColor = 1.0 - (1.0 - color) * (1.0 - bloom * intensity);
}