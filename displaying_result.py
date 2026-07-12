import os
import sys
import time
import threading
import sounddevice as sd
import soundfile as sf
import pygame

# --- CONFIGURATION ---
USB_SPEAKER_INDEX = 1  # Replace with your USB speaker index number
IMAGE_PATH = "your_image.jpg"
AUDIO_PATH = "your_audio.wav"
# ---------------------

# Event flag to signal all threads when it's time to shut down
shutdown_event = threading.Event()

def audio_thread_worker(audio_path, device_index, stop_signal):
    """Worker thread dedicated entirely to playing audio."""
    try:
        print(f"[Audio Thread] Loading: {audio_path}")
        data, fs = sf.read(audio_path)
        
        print("[Audio Thread] Starting playback...")
        sd.play(data, fs, device=device_index)
        
        # Wait until the audio finishes naturally OR a shutdown is requested
        while sd.get_stream().active and not stop_signal.is_set():
            time.sleep(0.1)
            
        sd.stop()
        print("[Audio Thread] Playback finished/stopped.")
    except Exception as e:
        print(f"[Audio Thread] Error: {e}")
    finally:
        # Trigger global shutdown if the audio finishes first
        stop_signal.set()

def video_thread_worker(image_path, stop_signal):
    """Worker thread dedicated entirely to handling the projector display."""
    pygame.init()
    pygame.mouse.set_visible(False)
    
    screen_info = pygame.display.Info()
    screen_width = screen_info.current_w
    screen_height = screen_info.current_h
    
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
    
    try:
        print(f"[Display Thread] Loading image: {image_path}")
        image = pygame.image.load(image_path)
        image = pygame.transform.scale(image, (screen_width, screen_height))
    except Exception as e:
        print(f"[Display Thread] Error: {e}")
        stop_signal.set()
        pygame.quit()
        return

    print("[Display Thread] Projecting image...")
    
    # Render loop running in parallel
    while not stop_signal.is_set():
        screen.blit(image, (0, 0))
        pygame.display.flip()
        
        # Listen for keyboard interrupts to close early (ESC or Q)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_signal.set()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    print("[Display Thread] Exit key pressed.")
                    stop_signal.set()
                    
        time.sleep(0.03)  # Roughly ~30 FPS to optimize CPU usage

    pygame.quit()
    print("[Display Thread] Window closed.")

def main():
    # Verify files exist before spinning up threads
    if not os.path.exists(IMAGE_PATH) or not os.path.exists(AUDIO_PATH):
        print("Error: Please check your IMAGE_PATH and AUDIO_PATH. Files not found.")
        sys.exit(1)

    # Define the threads
    audio_thread = threading.Thread(
        target=audio_thread_worker, 
        args=(AUDIO_PATH, USB_SPEAKER_INDEX, shutdown_event)
    )
    video_thread = threading.Thread(
        target=video_thread_worker, 
        args=(IMAGE_PATH, shutdown_event)
    )

    # Start both operations in parallel
    print("Launching parallel media streams...")
    audio_thread.start()
    video_thread.start()

    # Keep the main process alive until both threads signal they are done
    try:
        while not shutdown_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nMain process interrupted by user. Cleaning up...")
        shutdown_event.set()

    # Wait safely for both threads to wrap up their cleanup tasks
    audio_thread.join()
    video_thread.join()
    print("All systems shut down cleanly.")

if __name__ == "__main__":
    main()