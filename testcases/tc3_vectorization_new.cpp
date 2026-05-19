void compute_vec(float* a, float* b, float* c) {
    // Alias dependency added - vectorization lost
    for(int i = 0; i < 1024; i++) {
        c[i] = a[i] + b[i];
        a[i+1] = c[i]; // Loop carried dependency
    }
}
