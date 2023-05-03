from pandas import Series


class Direction:
    DOWN_UP = 1
    UP_DOWN = -1


def signal_cross(signal: Series[float] | Series[int], direction: Direction, *,
                 base: Series[float] | Series[int] = None,
                 reference: float | int = None) -> bool:
    ''' Base series defined -> True if last value of signal crosses base

      Reference defined -> True if last value of signal crosses reference '''
    # Last values of signal
    last_signal = signal.loc[-2] * direction
    current_signal = signal.loc[-1] * direction
    if base is not None:
        # Last values of base
        last_base = base.loc[-2] * direction
        current_base = base.loc[-1] * direction
        # Check if signal crosses base
        if last_signal <= last_base and current_signal > current_base:
            return True
    if reference is not None:
        # Check if signal crosses reference
        if last_signal <= reference and current_signal > reference:
            return True
    return False
