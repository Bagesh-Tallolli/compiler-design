int compute_branch(int a) {
    int b = 10;
    if (b > 5) {
        // This branch is always taken, dead branch elimination will keep this and remove else
        return a * 2;
    } else {
        return a * 3;
    }
}
