int process(int x) {
    int y = x * 2;
    int z = y + 10;
    int unused = z * 5; // dead code
    return z;
}
