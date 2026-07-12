import time
from machine import ADC, Pin, I2C
import ssd1306

# --- Hardware Configuration ---
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

joy_x = ADC(Pin(26))       
joy_btn = Pin(16, Pin.IN, Pin.PULL_UP) 

# --- Data Lists ---
languages = ["English", "Hindi", "Kannada", "Tamil", "Bengali"]
art_styles = ["Madubani", "Pattachitara", "Gond Art", "Kalamkari", "Pichhavai"] 

# --- Condition Flag ---
photo_taken = False  # Default state is False

# --- Menu Helper Functions ---
def display_menu(title, items, selected_index):
    oled.fill(0)
    oled.text(f"== {title} ==", 0, 0, 1)
    for idx, item in enumerate(items):
        y_pos = 16 + (idx * 10)
        if idx == selected_index:
            oled.text("> " + item, 0, y_pos, 1)  
        else:
            oled.text("  " + item, 0, y_pos, 1)
    oled.show()

def get_menu_selection(menu_title, items):
    selected_index = 0
    num_items = len(items)
    while True:
        display_menu(menu_title, items, selected_index)
        x_val = joy_x.read_u16()
        
        if x_val > 45000:
            selected_index = (selected_index + 1) % num_items
            time.sleep(0.2) 
        elif x_val < 20000:
            selected_index = (selected_index - 1) % num_items
            time.sleep(0.2) 
            
        if joy_btn.value() == 0:
            time.sleep(0.2) 
            while joy_btn.value() == 0: 
                pass 
            return items[selected_index]
        time.sleep(0.05)

# --- Main Program Flow (Infinite Loop) ---

while True:
    if not photo_taken:
        # Prompt user and wait until the system changes photo_taken to True
        oled.fill(0)
        oled.text("Please stand on", 0, 15, 1)
        oled.text("the mark for", 0, 30, 1)
        oled.text("the photo.", 0, 45, 1)
        oled.show()
        
        # In a real setup, your camera system or external trigger 
        # would flip photo_taken to True here.
        time.sleep(1) 
        
    else:
        # 1. User choices saved to requested variables
        TARGET_LANGUAGE = get_menu_selection("Language", languages)
        ARTform = get_menu_selection("Art Style", art_styles)

        # 2. Final Output Selection Screen
        oled.fill(0)
        oled.text("Selection Saved!", 0, 0, 1)
        oled.text(f"Lang: {TARGET_LANGUAGE}", 0, 20, 1)
        oled.text(f"Style: {ARTform}", 0, 35, 1) 
        oled.show()

        print("--- Menu Selection Complete ---")
        print(f"TARGET_LANGUAGE = '{TARGET_LANGUAGE}'")
        print(f"ARTform = '{ARTform}'")
        
        # Reset the flag to wait for the next photo session
        photo_taken = False
        time.sleep(5) # Show final screen details for 5 seconds before restarting loop