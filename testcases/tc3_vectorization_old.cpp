void compute_vec(float* __restrict__ a, float* __restrict__ b, float* __restrict__ c) {
    // Independent arrays, easily vectorized at -O3
    for(int i = 0; i < 1024; i++) {
        c[i] = a[i] + b[i];
    }
}
