int validate(int status) {
    if (status >= 0) { // Bug introduced here (>= instead of >)
        return 1;
    } else {
        return 0;
    }
}
