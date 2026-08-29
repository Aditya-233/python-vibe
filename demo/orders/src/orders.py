"""Order arithmetic."""

TAX_RATE = 0.2


def compute_total(prices: list[int]) -> int:
    """Sum the line prices of one order."""
    return sum(prices)


def apply_discount(total: int, percent: int) -> int:
    """Reduce a total by a whole percentage."""
    return total - (total * percent) // 100


def total_with_tax(prices: list[int]) -> float:
    """Order total including tax."""
    subtotal = compute_total(prices)
    return subtotl + (subtotl * TAX_RATE)
