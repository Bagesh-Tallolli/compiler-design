int unroll_test(int x) {
    int sum = 0;
    for(int i=0; i<4; i++) {
        sum += x;
    }
    return sum;
}
