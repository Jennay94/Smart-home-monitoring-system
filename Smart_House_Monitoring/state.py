# --- GLOBAL STATE STORAGE ---

# Képgaléria adatai
GALLERY_DATA = []

# AI Chat előzmények
chat_history_for_api = [
    {"role": "system", "content": "You are a helpful assistant in a smart home monitor application. Answer concisely in English."}
]

# ThingSpeak diagram adatok
GLOBAL_THINGSPEAK_HISTORY = {
    "Field1": [], "Field2": [], "Field3": [],
    "Field4": [], "Field5": [], "Field7": []
}

# Szimuláció állapota
simulation_running = False
simulation_thread = None