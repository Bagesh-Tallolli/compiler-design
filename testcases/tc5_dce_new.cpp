int compute_branch(int a, int b) {
    // b is dynamic now, branch cannot be eliminated
    if (b > 5) {
        return a * 2;
    } else {
        return a * 3;
    }
}
