class C:
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"

    def Style(text, *style) -> str:
        return "".join(style) + text + C.END


class I:
    CHECK = "\U00002705"
    CLOCK = "\U000023F3"
    COIN = "\U0001FA99"
    CROSS = "\U0000274C"
    NOTEPAD = "\U0001F5D2"
    PROFIT = "\U0001F4B0"
    TRADE = "\U0001F4C8"
    WARNING = "\U0001F4E3"


def move_cursor(y, x):
    print("\033[%d;%dH" % (y, x))


def progress_bar(index, count, bar_length=30):
    step = bar_length / count
    progress = index * step
    return C.Style("\U00002588"*int(progress), C.GREEN) + C.Style("\U00002592"*int(bar_length-progress), C.CYAN)
