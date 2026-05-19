void compute_loop(int* data) {
    // Fixed bound - compiler unrolls this at -O3
    for(int i = 0; i < 4; i++) {
        data[i] = data[i] * 2;
    }
}
