def round_float(number: float, decimal_places: int) -> float:
    ''' Rounds a safe float number to desired decimal places '''
    base_decimal = 10 ** decimal_places
    return int(number * base_decimal) / base_decimal


def float_to_precision(number: float, precision: int) -> str:
    return f"{number:.0{precision}f}"
