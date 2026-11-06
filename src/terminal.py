import os
import sys


COLORS = {
    "cyan": "96",
    "blue": "94",
    "green": "92",
    "yellow": "93",
    "red": "91",
    "title": "1;94",
}


def paint(text, color, stream=None):
    if stream is None:
        stream = sys.stdout
    if not stream.isatty() or "NO_COLOR" in os.environ or os.environ.get("TERM") == "dumb":
        return text
    return f"\033[{COLORS[color]}m{text}\033[0m"


def timer_text(seconds, text):
    color = "cyan"
    if seconds <= 5 * 60:
        color = "red"
    elif seconds <= 30 * 60:
        color = "yellow"
    return paint(text, color)


def clear_screen():
    if sys.stdout.isatty() and os.environ.get("TERM") != "dumb":
        print("\033[2J\033[H", end="", flush=True)
