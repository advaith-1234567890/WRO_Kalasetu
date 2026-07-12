# -----------------------------
# IMPORTS
# -----------------------------
import os  # Allows the script to interact with files and folders.
import sys  # Provides access to system-related functions.
import time  # Lets the script pause and track timing.
import threading  # Allows multiple tasks to run at the same time.
from pathlib import Path  # Helps manage file paths more easily.

try:  # Try to import OpenCV for camera and image handling.
    import cv2  # Import the OpenCV library.
except Exception:  # pragma: no cover  # If OpenCV is missing, use a fallback.
    cv2 = None  # Set cv2 to None so the script can check availability.

try:  # Try to import NumPy for image array work.
    import numpy as np  # Import NumPy as np.
except Exception:  # pragma: no cover  # If NumPy is missing, use a fallback.
    np = None  # Set np to None so the script can check availability.

try:  # Try to import the qrcode library.
    import qrcode  # Import the QR code generator.
except Exception:  # pragma: no cover  # If qrcode is missing, skip QR generation.
    qrcode = None  # Set qrcode to None for fallback handling.

try:  # Try to import pygame for display output.
    import pygame  # Import pygame.
except Exception:  # pragma: no cover  # If pygame is missing, display will be skipped.
    pygame = None  # Set pygame to None for fallback handling.

try:  # Try to import playsound for audio playback.
    from playsound import playsound  # Import the playsound function.
except Exception:  # pragma: no cover  # If playsound is missing, audio playback will be skipped.
    playsound = None  # Set playsound to None for fallback handling.

try:  # Try to import gTTS for speech synthesis.
    from gtts import gTTS  # Import gTTS.
except Exception:  # pragma: no cover  # If gTTS is missing, speech will be skipped.
    gTTS = None  # Set gTTS to None for fallback handling.

try:  # Try to import the Google GenAI package for translation.
    from google import genai  # Import the genai module.
except Exception:  # pragma: no cover  # If translation is unavailable, use the original text.
    genai = None  # Set genai to None so translation can be skipped.

try:  # Try to import dotenv to load settings from a .env file.
    from dotenv import load_dotenv  # Import load_dotenv.
except Exception:  # pragma: no cover  # If dotenv is missing, continue without it.
    load_dotenv = None  # Set load_dotenv to None.

try:  # Try to import TensorFlow for advanced image stylization.
    import tensorflow as tf  # Import TensorFlow.
    import tensorflow_hub as hub  # Import TensorFlow Hub.
except Exception:  # pragma: no cover  # If TensorFlow is unavailable, use a simpler fallback.
    tf = None  # Set tf to None.
    hub = None  # Set hub to None.

# -----------------------------
# CONFIG
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent  # Set BASE_DIR to the folder containing the script.
CAPTURED_IMAGE = BASE_DIR / "captured_image.jpg"  # Define the file path for the captured image.
STYLED_IMAGE = BASE_DIR / "styled_image.jpg"  # Define the file path for the stylized image.
FINAL_IMAGE = BASE_DIR / "final_output.jpg"  # Define the file path for the final image with the QR code.
TRANSLATION_FILE = BASE_DIR / "kalakari_file.txt"  # Define the file path for the translation text.
OUTPUT_AUDIO = BASE_DIR / "output.mp3"  # Define the file path for the generated speech audio.
TARGET_LANGUAGE = "Hindi"  # Set the default target language to Hindi.
ART_STYLE = "Kalamkari"  # Set the default art style to Kalamkari.
DOWNLOAD_URL = "https://example.com/download-my-image.jpg"  # Set the URL that will be encoded in the QR code.
STYLE_ASSET_MAP = {  # Map each style name to its matching image and text file.
    "Kalamkari": ("Kalamkari.jpg", "Kalamkari.txt"),  # Link Kalamkari to its image and text file.
    "Madubani": ("Madhubani.jpg", "Madhubani.txt"),  # Link Madubani to its image and text file.
    "Pattachitara": ("Pattachitara.jpg", "Pattachitara.txt"),  # Link Pattachitara to its image and text file.
    "Gond Art": ("Gond_Art.jpg", "Gond_Art.txt"),  # Link Gond Art to its image and text file.
    "Pichhavai": ("Pichhavai.jpg", "Pichhavai.txt"),  # Link Pichhavai to its image and text file.
}

# -----------------------------
# FALLBACK IMAGE
# -----------------------------
def create_placeholder_image(path: Path, title: str = "Captured Image"):
    # Create a fallback image when OpenCV is unavailable or the camera cannot be opened.
    if cv2 is None:
        return False
    canvas = np.zeros((720, 1280, 3), dtype=np.uint8)
    canvas[:] = (30, 30, 60)
    cv2.putText(canvas, title, (80, 180), cv2.FONT_HERSHEY_SIMPLEX, 2.2, (255, 255, 255), 3)
    cv2.putText(canvas, "Camera unavailable", (80, 320), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (220, 220, 220), 2)
    cv2.putText(canvas, "Using fallback image", (80, 420), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (220, 220, 220), 2)
    return cv2.imwrite(str(path), canvas)

# -----------------------------
# TRIGGER / SENSOR
# -----------------------------
def wait_for_trigger():
    # Wait until a person is detected near the trigger area before starting the capture process.
    print("[1/6] Waiting for a person to stand on the mark...")
    try:
        from gpiozero import DistanceSensor, Servo
    except Exception as exc:
        print(f"GPIO hardware not available ({exc}); waiting for manual confirmation.")
        input("Press Enter when you are ready to capture the image...")
        return True

    servo = Servo(18)
    sensor_left = DistanceSensor(echo=24, trigger=23, max_distance=2.0)
    sensor_right = DistanceSensor(echo=22, trigger=27, max_distance=2.0)

    min_dist = 0.40
    max_dist = 0.80
    required_time = 3.0
    start_time = None
    tracked_direction = None

    try:
        # Keep checking the sensor values until the target remains in range long enough.
        while True:
            dist_left = sensor_left.distance
            dist_right = sensor_right.distance
            left_in_range = min_dist <= dist_left <= max_dist
            right_in_range = min_dist <= dist_right <= max_dist

            current_direction = None
            if left_in_range:
                current_direction = "LEFT"
            elif right_in_range:
                current_direction = "RIGHT"

            # Start or reset the timer only when the detected direction changes.
            if current_direction:
                if start_time is None or tracked_direction != current_direction:
                    start_time = time.time()
                    tracked_direction = current_direction
                    print(f"Target detected on the {tracked_direction}. Starting countdown...")

                elapsed_time = time.time() - start_time
                # Trigger the action once the person stays in range for the required time.
                if elapsed_time >= required_time:
                    if tracked_direction == "LEFT":
                        servo.min()
                    else:
                        servo.max()
                    time.sleep(0.5)
                    print("Target confirmed. Capturing image...")
                    return True
            else:
                # Reset the timer if the target leaves the trigger zone.
                if start_time is not None:
                    start_time = None
                    tracked_direction = None

            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Trigger cancelled by user.")
        return False
    finally:
        try:
            servo.detach()
        except Exception:
            pass

# -----------------------------
# CAPTURE IMAGE
# -----------------------------
def capture_photo():
    # Capture the image only after the trigger condition has been satisfied.
    wait_for_trigger()

    if cv2 is None:
        create_placeholder_image(CAPTURED_IMAGE, "Captured Image")
        print("OpenCV is not available; created a fallback image.")
        return str(CAPTURED_IMAGE)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        create_placeholder_image(CAPTURED_IMAGE, "Captured Image")
        print("Camera not available; created a fallback image.")
        return str(CAPTURED_IMAGE)

    ret, frame = cap.read()
    if ret:
        cv2.imwrite(str(CAPTURED_IMAGE), frame)
        print(f"Image saved to {CAPTURED_IMAGE}")
    else:
        create_placeholder_image(CAPTURED_IMAGE, "Captured Image")
        print("Camera capture failed; created a fallback image.")

    cap.release()
    return str(CAPTURED_IMAGE)

# -----------------------------
# OLED MENU
# -----------------------------
def select_preferences():
    # Let the user choose the target language and artistic style using the OLED and joystick.
    print("[2/6] Selecting language and art style...")
    global TARGET_LANGUAGE, ART_STYLE

    try:
        from machine import ADC, Pin, I2C
        import ssd1306

        i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
        oled = ssd1306.SSD1306_I2C(128, 64, i2c)
        joy_x = ADC(Pin(26))
        joy_btn = Pin(16, Pin.IN, Pin.PULL_UP)

        languages = ["English", "Hindi", "Kannada", "Tamil", "Bengali"]
        art_styles = ["Madubani", "Pattachitara", "Gond Art", "Kalamkari", "Pichhavai"]

        def display_menu(title, items, selected_index):
            # Render the current menu screen on the OLED display.
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
            # Loop until the user confirms the selected item with the joystick button.
            selected_index = 0
            while True:
                display_menu(menu_title, items, selected_index)
                x_val = joy_x.read_u16()
                # Move selection up or down based on joystick movement.
                if x_val > 45000:
                    selected_index = (selected_index + 1) % len(items)
                    time.sleep(0.2)
                elif x_val < 20000:
                    selected_index = (selected_index - 1) % len(items)
                    time.sleep(0.2)
                # Confirm the selection when the button is pressed.
                if joy_btn.value() == 0:
                    time.sleep(0.2)
                    while joy_btn.value() == 0:
                        pass
                    return items[selected_index]
                time.sleep(0.05)

        TARGET_LANGUAGE = get_menu_selection("Language", languages)
        ART_STYLE = get_menu_selection("Art Style", art_styles)
        return TARGET_LANGUAGE, ART_STYLE
    except Exception as exc:
        print(f"OLED joystick hardware not available ({exc}); using console prompts instead.")
        print("Available languages: English, Hindi, Kannada, Tamil, Bengali")
        TARGET_LANGUAGE = input("Enter target language [Hindi]: ").strip() or TARGET_LANGUAGE
        print("Available art styles: Madubani, Pattachitara, Gond Art, Kalamkari, Pichhavai")
        ART_STYLE = input("Enter art style [Kalamkari]: ").strip() or ART_STYLE
        return TARGET_LANGUAGE, ART_STYLE

# -----------------------------
# STYLE ASSETS
# -----------------------------
def get_style_assets(style_name: str):
    style_key = style_name.strip()
    if style_key not in STYLE_ASSET_MAP:
        style_key = "Kalamkari"
    image_name, text_name = STYLE_ASSET_MAP[style_key]
    return BASE_DIR / image_name, BASE_DIR / text_name

# -----------------------------
# IMAGE STYLIZATION
# -----------------------------
def stylize_image(input_path: str, output_path: str, style_name: str, style_image_path: str | None = None):
    # Apply the selected art style to the captured image and save the result.
    print("[3/6] Applying art stylization...")
    if cv2 is None or np is None:
        print("OpenCV is not available; skipping stylization.")
        if os.path.exists(input_path):
            os.replace(input_path, output_path)
        return str(output_path)

    img = cv2.imread(input_path)
    if img is None:
        img = np.zeros((720, 1280, 3), dtype=np.uint8)

    style_img = None
    if style_image_path and os.path.exists(style_image_path):
        style_img = cv2.imread(style_image_path)

    # Use TensorFlow-based stylization when it is available; otherwise fall back to OpenCV effects.
    if tf is not None and hub is not None and style_img is not None:
        try:
            os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
            os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            style_rgb = cv2.cvtColor(style_img, cv2.COLOR_BGR2RGB)
            img_tensor = tf.convert_to_tensor([img_rgb], dtype=tf.uint8)
            style_tensor = tf.convert_to_tensor([style_rgb], dtype=tf.uint8)
            model = hub.load("https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/2")
            stylized = model(img_tensor, style_tensor)[0]
            stylized = np.array(stylized * 255, dtype=np.uint8)
            stylized = cv2.cvtColor(stylized, cv2.COLOR_RGB2BGR)
            cv2.imwrite(output_path, stylized)
            return output_path
        except Exception as exc:
            print(f"TensorFlow stylization failed ({exc}); using fallback effect instead.")

    result = img.copy()
    if style_img is not None:
        # Blend the captured image with the selected art-style reference image.
        style_resized = cv2.resize(style_img, (result.shape[1], result.shape[0]))
        result = cv2.addWeighted(result, 0.75, style_resized, 0.25, 0)

    # Choose a different visual effect based on the selected art style.
    if style_name.lower().startswith("mad"):
        result = cv2.bilateralFilter(result, 9, 75, 75)
        result = cv2.cvtColor(result, cv2.COLOR_BGR2HSV)
    elif style_name.lower().startswith("pat"):
        result = cv2.GaussianBlur(result, (0, 0), 3)
        result = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
    elif style_name.lower().startswith("gond"):
        result = cv2.Canny(result, 100, 200)
        result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
    else:
        result = cv2.detailEnhance(result, sigma_s=10, sigma_r=0.15)

    cv2.putText(result, style_name, (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
    cv2.imwrite(output_path, result)
    return str(output_path)

# -----------------------------
# QR CODE
# -----------------------------
def add_qr_code(input_path: str, output_path: str):
    # Overlay a QR code onto the final image and save it.
    print("[4/6] Adding QR code...")
    if cv2 is None or np is None or qrcode is None:
        print("QR dependencies missing; skipping QR code addition.")
        if os.path.exists(input_path):
            os.replace(input_path, output_path)
        return str(output_path)

    img = cv2.imread(input_path)
    if img is None:
        img = np.zeros((720, 1280, 3), dtype=np.uint8)

    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=0)
    qr.add_data(DOWNLOAD_URL)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_cv = cv2.cvtColor(np.array(qr_img), cv2.COLOR_RGB2BGR)
    qr_size = 120
    padding = 15
    total_qr_size = qr_size + (padding * 2)
    qr_cv_resized = cv2.resize(qr_cv, (qr_size, qr_size), interpolation=cv2.INTER_NEAREST)
    white_background = np.full((total_qr_size, total_qr_size, 3), 255, dtype=np.uint8)
    white_background[padding:padding + qr_size, padding:padding + qr_size] = qr_cv_resized

    h, w, _ = img.shape
    # Only place the QR code if the image is large enough to fit it cleanly.
    if h > total_qr_size and w > total_qr_size:
        img[0:total_qr_size, 0:total_qr_size] = white_background
    cv2.imwrite(output_path, img)
    return str(output_path)

# -----------------------------
# TRANSLATE AND SPEAK
# -----------------------------
def translate_and_speak(text: str, target_language: str):
    # Translate the selected text and convert it into speech.
    print("[5/6] Translating and generating speech...")
    TRANSLATION_FILE.write_text(text, encoding="utf-8")

    translated_text = text
    # Use the Gemini API for translation when the API key is available.
    if genai is not None and os.getenv("GEMINI_API_KEY"):
        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            prompt = f"Translate the following text into {target_language}. Return only the translated text.\n\n{text}"
            response = client.models.generate_content(model="gemini-2.5-flash", contents=[prompt])
            translated_text = response.text
        except Exception as exc:
            print(f"Gemini translation failed ({exc}); using original text.")

    # Convert the final text into speech if the TTS library is available.
    if gTTS is not None:
        try:
            tts = gTTS(text=translated_text, lang="hi" if target_language.lower() == "hindi" else "en")
            tts.save(str(OUTPUT_AUDIO))
            if playsound is not None:
                playsound(str(OUTPUT_AUDIO))
        except Exception as exc:
            print(f"Text-to-speech failed ({exc}).")
    return translated_text

# -----------------------------
# DISPLAY RESULT
# -----------------------------
def display_result(image_path: str, audio_path: str, play_audio: bool = True):
    # Show the final image on the display and optionally play the generated audio.
    print("[6/6] Displaying final result...")
    if pygame is None:
        print("Pygame is not available; image display skipped.")
        return

    pygame.init()
    pygame.mouse.set_visible(False)
    info = pygame.display.Info()
    screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
    image = pygame.image.load(image_path)
    image = pygame.transform.scale(image, (info.current_w, info.current_h))
    screen.blit(image, (0, 0))
    pygame.display.flip()

    if play_audio and os.path.exists(audio_path) and playsound is not None:
        try:
            playsound(audio_path)
        except Exception as exc:
            print(f"Audio playback failed ({exc}).")

    running = True
    # Keep the display open until the user exits with Escape or Q.
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
                running = False
        time.sleep(0.05)
    pygame.quit()

# -----------------------------
# VISUAL PIPELINE
# -----------------------------
def run_visual_pipeline(captured_image_path: str, style_name: str, styled_image_path: str, final_image_path: str):
    # Run the visual processing pipeline: style transfer, QR code embedding, and display.
    style_image_path, style_text_path = get_style_assets(style_name)
    stylized_path = stylize_image(captured_image_path, styled_image_path, style_name, str(style_image_path))
    final_path = add_qr_code(stylized_path, final_image_path)
    display_result(final_path, str(OUTPUT_AUDIO), play_audio=False)
    return final_path

# -----------------------------
# MAIN LOOP
# -----------------------------
def main():
    # Main control flow for the full experience.
    if load_dotenv is not None:
        load_dotenv()

    capture_photo()
    select_preferences()

    style_image_path, style_text_path = get_style_assets(ART_STYLE)
    base_text = style_text_path.read_text(encoding="utf-8") if style_text_path.exists() else "Welcome to the art experience."

    # Start translation and speech in one thread while the visual pipeline runs in another.
    audio_thread = threading.Thread(target=lambda: print(f"Translated text: {translate_and_speak(base_text, TARGET_LANGUAGE)}"), daemon=True)
    audio_thread.start()

    visual_thread = threading.Thread(
        target=lambda: run_visual_pipeline(str(CAPTURED_IMAGE), ART_STYLE, str(STYLED_IMAGE), str(FINAL_IMAGE)),
        daemon=True,
    )
    visual_thread.start()

    audio_thread.join()
    visual_thread.join()


if __name__ == "__main__":
    main()