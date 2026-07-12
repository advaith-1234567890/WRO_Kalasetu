import cv2
import time
import os
from gpiozero import DistanceSensor, Servo

# Initialize Hardware (Adjust GPIO pins as needed)
servo = Servo(18)  
sensor_left = DistanceSensor(echo=24, trigger=23, max_distance=2.0)
sensor_right = DistanceSensor(echo=22, trigger=27, max_distance=2.0)

# Constants
MIN_DIST = 0.40  # 40 cm in meters
MAX_DIST = 0.80  # 80 cm in meters
REQUIRED_TIME = 3.0  # 3 seconds
IMAGE_FILENAME = "person_pic.jpg"

def capture_and_cleanup():
    """Initializes the camera, takes a picture, displays it, and deletes it."""
    print("\nTarget confirmed! Initializing camera...")
    cap = cv2.VideoCapture(0)
    time.sleep(1) # Camera warm-up
    
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(IMAGE_FILENAME, frame)
        print(f"Image saved successfully as '{IMAGE_FILENAME}'")
        
        cv2.imshow("Captured Image", frame)
        print("Displaying image for 20 seconds...")
        cv2.waitKey(20000)
    else:
        print("Error: Could not grab a frame from the camera.")
        
    cap.release()
    cv2.destroyAllWindows()
    print("OpenCV windows destroyed.")
    
    if os.path.exists(IMAGE_FILENAME):
        os.remove(IMAGE_FILENAME)
        print(f"File '{IMAGE_FILENAME}' successfully deleted.")
    else:
        print("File not found, nothing to delete.")

def main():
    print("System active. Monitoring for targets between 40cm and 80cm...")
    
    # Tracking variables
    start_time = None
    tracked_direction = None  # Keeps track of which side ("LEFT" or "RIGHT") is active

    try:
        while True:
            dist_left = sensor_left.distance
            dist_right = sensor_right.distance
            
            # Check if object is in range on the Left
            left_in_range = MIN_DIST <= dist_left <= MAX_DIST
            # Check if object is in range on the Right
            right_in_range = MIN_DIST <= dist_right <= MAX_DIST
            
            current_direction = None
            if left_in_range:
                current_direction = "LEFT"
            elif right_in_range:
                current_direction = "RIGHT"
                
            # Timer Logic
            if current_direction:
                # If a target just entered the zone, or swapped sides, start/restart the timer
                if start_time is None or tracked_direction != current_direction:
                    start_time = time.time()
                    tracked_direction = current_direction
                    print(f"\nTarget detected on the {tracked_direction}. Starting 3-second countdown...")
                
                # Calculate elapsed time
                elapsed_time = time.time() - start_time
                print(f"Tracking {tracked_direction}: {elapsed_time:.1f}s / {REQUIRED_TIME}s", end="\r")
                
                # If target stays for 3 seconds, trigger action
                if elapsed_time >= REQUIRED_TIME:
                    if tracked_direction == "LEFT":
                        servo.min()
                    else:
                        servo.max()
                        
                    time.sleep(0.5)  # Allow servo to reach the position
                    capture_and_cleanup()
                    break  # Exit program after complete sequence
                    
            else:
                # Reset if nothing is within the 40-80cm range
                if start_time is not None:
                    print("\nTarget lost or out of range. Resetting timer.")
                    start_time = None
                    tracked_direction = None
            
            time.sleep(0.1)  # 100ms refresh rate
            
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    finally:
        servo.detach()
        print("Program closed gracefully.")

if __name__ == "__main__":
    main()