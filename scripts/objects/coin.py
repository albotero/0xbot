class Coin:
    def __init__(
            self, symbol: str, base: str, quote: str, precision: int, min_qty: str, max_qty: str, step_size: str,
            tick_size: str) -> None:
        self.base = base
        self.quote = quote
        self.strsymbol = f"{base}/{quote}"
        self.symbol = symbol
        self.precision = precision
        self.price = 0
        self.min_qty = float(min_qty)
        self.max_qty = float(max_qty)
        self.step_size = step_size.index("1") - 1
        self.tick_size = tick_size.index("1") - 1
        self.value = 0
