__attribute__((noinline)) int helper(int x) {
    return x * x;
}

int compute_inline(int a, int b) {
    // helper is no longer inlined
    return helper(a) + helper(b);
}
