"""Constants for Bin Day Tracker."""

DOMAIN = "bin_day_tracker"
NAME = "Bin Day Tracker"
VERSION = "0.0.1"

CONF_BINS = "bins"

CONF_ID = "id"
CONF_NAME = "name"
CONF_MATERIAL = "material"
CONF_COLOUR = "colour"
CONF_ENABLED = "enabled"
CONF_PRIMARY = "primary"
CONF_START_DATE = "start_date"
CONF_REPEAT_DAYS = "repeat_days"
CONF_DISPLAY_ORDER = "display_order"

MAX_BINS = 10

COLOUR_OPTIONS = {
    "black": {"label": "Black", "hex": "#000000"},
    "dark_grey": {"label": "Dark Grey", "hex": "#4A4A4A"},
    "grey": {"label": "Grey", "hex": "#808080"},
    "light_grey": {"label": "Silver / Light Grey", "hex": "#C0C0C0"},
    "navy": {"label": "Navy", "hex": "#003366"},
    "blue": {"label": "Blue", "hex": "#0074D9"},
    "sky_blue": {"label": "Sky Blue", "hex": "#5BC0EB"},
    "turquoise": {"label": "Turquoise", "hex": "#40E0D0"},
    "dark_green": {"label": "Dark Green", "hex": "#1B5E20"},
    "green": {"label": "Green", "hex": "#2ECC40"},
    "light_green": {"label": "Light Green", "hex": "#7ED957"},
    "yellow": {"label": "Yellow", "hex": "#FFD60A"},
    "amber": {"label": "Amber", "hex": "#FFB000"},
    "orange": {"label": "Orange", "hex": "#FF851B"},
    "red": {"label": "Red", "hex": "#FF4136"},
    "burgundy": {"label": "Burgundy", "hex": "#800020"},
    "pink": {"label": "Pink", "hex": "#FF6F91"},
    "purple": {"label": "Purple", "hex": "#9B59B6"},
    "brown": {"label": "Brown", "hex": "#8B5A2B"},
    "white": {"label": "White", "hex": "#FFFFFF"},
}