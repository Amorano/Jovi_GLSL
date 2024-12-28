#ifndef LIB_MATH_DISTANCE
#define LIB_MATH_DISTANCE

//------------------------------------------------------------------------------
// DISTANCE
//------------------------------------------------------------------------------

float math_distance(vec2 v, int metric) {
    if(metric == 1) return abs(v.x) + abs(v.y);        // Manhattan
    if(metric == 2) return max(abs(v.x), abs(v.y));    // Chebyshev
    return dot(v, v);                                  // Euclidean (squared)
}

float math_distance(vec3 v, int metric) {
    if(metric == 1) return abs(v.x) + abs(v.y) + abs(v.z);
    if(metric == 2) return max(max(abs(v.x), abs(v.y)), abs(v.z));
    return dot(v, v);
}

float math_distance(vec4 v, int metric) {
    if(metric == 1) return abs(v.x) + abs(v.y) + abs(v.z) + abs(v.w);
    if(metric == 2) return max(max(max(abs(v.x), abs(v.y)), abs(v.z)), abs(v.w));
    return dot(v, v);
}

#endif