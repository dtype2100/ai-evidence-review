def discounted_price(total: float, rate: float) -> float:
    """Return the total after subtracting a fractional discount."""
    return total * (1 + rate)
