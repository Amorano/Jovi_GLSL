// name: FILTER RANGE
// desc: Select pixels from start color through end color. Maintains alpha/mask.
// category: FILTER

uniform sampler2D image; //                | RGB(A) image
uniform vec3 start;      // 0,0,0 ;;;; rgb | Start of the Range
uniform vec3 end;        //       ;;;; rgb | End of the Range

void mainImage( out vec4 fragColor, in vec2 fragCoord ) {
    vec2 uv = fragCoord / iResolution.xy;
    vec4 color = texture(image, uv);
    bool isInside = all(greaterThanEqual(color.rgb, start.rgb)) && all(lessThanEqual(color.rgb, end.rgb));
    fragColor = vec4(vec3(isInside ? 1.0 : 0.0), color.a);
}