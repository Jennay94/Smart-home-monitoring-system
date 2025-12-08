import flet as ft
import logging

# --- CONFIGURATION ---
API_KEY = "API KEY_HERE"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-chat"

THINGSPEAK_CHANNEL_ID = "3156213"
THINGSPEAK_READ_KEY = "WXM1B5P9O2XBKKMS"
THINGSPEAK_URL = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds/last.json?api_key={THINGSPEAK_READ_KEY}"
POLL_INTERVAL_SECONDS = 15

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- UI DESIGN SYSTEM ---
BG_COLOR = "#F5F7FA"
CARD_BG = "#FFFFFF"
TEXT_PRIMARY = "#212121"
TEXT_SECONDARY = "#757575"

# Accent Colors
COLOR_TEMP = "#FF3B30"
COLOR_HUM = "#0056D2"
COLOR_LIGHT = "#FF9500"
COLOR_SOIL = "#8D6E63"
COLOR_RAIN = "#546E7A"
COLOR_FAN = "#78909C"

# Status Colors
COLOR_SUCCESS = "#34C759"
COLOR_DANGER = "#FF3B30"
COLOR_WARNING = "#FF9500"

# Constants
CARD_ELEVATION = 2
CARD_BORDER_RADIUS = 16
SECTION_PADDING = 24

# Chart Styles
CHART_BG_COLOR = CARD_BG
AXIS_TITLE_STYLE = ft.TextStyle(size=14, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY)
LABEL_STYLE = ft.TextStyle(size=12, weight=ft.FontWeight.W_500, color=TEXT_SECONDARY)