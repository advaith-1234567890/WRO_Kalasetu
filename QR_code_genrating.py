import cv2
import numpy as np
import qrcode

# 1. Load your main background image
# Replace 'your_image.jpg' with your actual filename
image_path = "your_image.jpg"
img = cv2.imread(image_path)

if img is None:
    print(
        f"Error: Could not load image from {image_path}. Please check the file path."
    )
    exit()

# 2. Define the URL or data for downloading the image
download_url = "https://example.com/download-my-image.jpg"

# 3. Generate the QR code
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=0,
)
qr.add_data(download_url)
qr.make(fit=True)

# Create the QR code image (Black and White)
qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
qr_cv = cv2.cvtColor(np.array(qr_img), cv2.COLOR_RGB2BGR)

# 4. Resize the QR code and add a clean white background/border
qr_size = 120  # Size of the QR code itself
padding = 15  # Thickness of the white background border around it
total_qr_size = qr_size + (padding * 2)

qr_cv_resized = cv2.resize(
    qr_cv, (qr_size, qr_size), interpolation=cv2.INTER_NEAREST
)

# Create a solid white square canvas for the background
white_background = np.full(
    (total_qr_size, total_qr_size, 3), 255, dtype=np.uint8
)
white_background[
    padding : padding + qr_size, padding : padding + qr_size
] = qr_cv_resized

# 5. Overlay the QR code onto the top-left corner of the main image
img_h, img_w, _ = img.shape
if img_h > total_qr_size and img_w > total_qr_size:
    img[0:total_qr_size, 0:total_qr_size] = white_background
else:
    print("Warning: The main image is too small for the generated QR code size.")

# 6. Save the new image, overwriting the original file
cv2.imwrite(image_path, img)
print(f"Success! The image has been updated and saved to: {image_path}")

# Optional: Display the final result on screen
cv2.imshow("Saved Image with QR Code", img)
cv2.waitKey(0)
cv2.destroyAllWindows()