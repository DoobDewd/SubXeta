"""Centralized theme colors for SubXeta's dark alien aesthetic.

Single source of truth for every color used in the UI. Change the green here
and it updates everywhere. Stylesheet strings reference these via
``string.Template`` ($NAME) so CSS braces don't need escaping; short inline
styles use f-strings.
"""

# --- Core accent (the signature green) ---
GREEN = "#00ff88"          # primary accent
GREEN_BRIGHT = "#00ffaa"   # hover / focus accent
GREEN_HOVER = "#66ffdd"    # icon hover highlight
GREEN_PRESSED = "#00dd77"  # button pressed
GREEN_BORDER = "#00aa55"   # button border (dark green)
GREEN_SHADOW = "#006644"   # key bevel shadow (dark green)

# --- Backgrounds ---
BG = "#1a1a1a"             # main background / text editors
BG_FOCUS = "#1f1f1f"       # input focus background
BG_HOVER = "#242424"       # input hover background
SURFACE = "#2a2a2a"        # input / control surface
PANEL = "#191e1c"          # chunks scroll panel background

# --- Text ---
TEXT = "#e0e0e0"           # primary text
TEXT_DIM = "#b0b0b0"       # dimmer text (hotkey descriptions)
TEXT_MUTED = "#777777"     # muted labels (In/Out, model buttons)
TEXT_DISABLED = "#666666"  # disabled button text
BLACK = "#000000"          # text on green buttons

# --- Borders / misc ---
BORDER = "#444444"         # control border (settings buttons)
BORDER_HOVER = "#555555"   # control border on hover
DISABLED_BG = "#333333"    # disabled button background
MARKER = "#ffffff"         # playhead + played-progress + drag-active highlight

# --- RGB tuples (for QColor / QPen) ---
GREEN_RGB = (0, 255, 136)         # matches GREEN
GREEN_KNOB_BORDER_RGB = (0, 200, 100)  # darker border on In/Out knobs
MARKER_RGB = (255, 255, 255)      # matches MARKER (playhead + played progress)
MARKER_BORDER_RGB = (170, 170, 170)  # grey border on the white playhead


def green_rgba(alpha: float) -> str:
    """Theme green as a CSS ``rgba()`` string with the given alpha (0.0-1.0)."""
    r, g, b = GREEN_RGB
    return f"rgba({r}, {g}, {b}, {alpha})"


def stylesheet_vars() -> dict:
    """All string color constants as a mapping for ``string.Template`` substitution."""
    return {
        name: value
        for name, value in globals().items()
        if name.isupper() and isinstance(value, str)
    }
