#define MAGIC_COMPUTE(x, y) _Pragma("unroll") ((x) * (y) + (x) / 2)

int compute_macro(int a, int b) {
    // Complex macro, might cause parsing issues if simulated or handled badly
    return MAGIC_COMPUTE(a, b);
}
