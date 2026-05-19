static inline int helper(int x) {
    return x * x;
}

int compute_inline(int a, int b) {
    // helper is inlined here
    return helper(a) + helper(b);
}
