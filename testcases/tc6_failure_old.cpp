#define MULT(x, y) ((x) * (y))
#define ADD(x, y) ((x) + (y))

int compute_macro(int a, int b) {
    return ADD(MULT(a, 2), MULT(b, 3));
}
