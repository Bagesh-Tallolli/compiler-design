void compute_loop(int* data, int n) {
    // Dynamic bound - compiler cannot unroll this
    for(int i = 0; i < n; i++) {
        data[i] = data[i] * 2;
    }
}
