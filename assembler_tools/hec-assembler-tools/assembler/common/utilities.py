
def clamp(x, minimum = float("-inf"), maximum = float("inf")):
    """
    Clamp a value between a specified minimum and maximum.

    This function ensures that a given value `x` is constrained within the
    bounds defined by `minimum` and `maximum`.

    Args:
        x: The value to be clamped.
        minimum (float, optional): The lower bound to clamp `x` to.
        maximum (float, optional): The upper bound to clamp `x` to.

    Returns:
        The clamped value.
    """
    if x < minimum:
        return minimum
    if x > maximum:
        return maximum
    return x
