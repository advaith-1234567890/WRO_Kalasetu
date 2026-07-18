import os
from google import genai
from dotenv import load_dotenv
from gtts import gTTS
from playsound import playsound

# -----------------------------
# CONFIG
# -----------------------------

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)

TARGET_LANGUAGE = "Hindi" # To be changed to the language selected
Translate_file = "kalakari_file.txt" # To be be changed to the text selected
SAMPLE_RATE = 16000

# -----------------------------
# Read file
# -----------------------------
def read_file (file):
    with open(file, "r", encoding="utf-8") as file:
        content = file.read()
        return content

# -----------------------------
# TRANSLATE
# -----------------------------

def translate_audio(file):

    prompt = f"""
You are a live translator.
1. Translate into {TARGET_LANGUAGE}.
2. Return ONLY the translated text.
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            prompt,
            file
        ]
    )

    return response.text

# -----------------------------
# TEXT TO SPEECH
# -----------------------------

def speak(text):

    tts = gTTS(
        text=text,
        lang="hi"
    )

    tts.save("output.mp3")

    playsound("output.mp3")

# -----------------------------
# MAIN LOOP
# -----------------------------

print("="*50)
print("LIVE GEMINI TRANSLATOR")
print("="*50)

while True:
    try:
        data = read_file(Translate_file)
        translated = translate_audio(data)

        print("\nTranslation:\n")
        print(translated)
        speak(translated)

    except KeyboardInterrupt:
        print("\nStopped.")
        break

    except Exception as e:
        print(e)