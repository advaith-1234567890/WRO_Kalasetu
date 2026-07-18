import os
import logging
from typing import Dict, Tuple

# --- Configuration & Logging Suppression ---
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
logging.getLogger('tensorflow').setLevel(logging.ERROR)

import cv2
import numpy as np
import qrcode
import tensorflow as tf
import tensorflow_hub as hub
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import Response

app = FastAPI(title="Media Processing & Translation API")

# =====================================================================
# 1. TRANSLATION ENGINE (Encapsulation)
# =====================================================================
class TranslationEngine:
    """Handles text translation tasks using Argos Translate."""
    
    # Supported language mapping encapsulation
    LANGUAGE_CODES: Dict[str, str] = {
        "English": "en",
        "Hindi": "hi",
        "Bengali": "bn",
        "Spanish": "es",
        "Japanese": "ja"
    }

    def __init__(self):
        # Import argos_translate inside the class to handle dependencies gracefully
        try:
            import argostranslate.package
            import argostranslate.translate
            self.translator = argostranslate.translate
        except ImportError:
            raise ImportError("Please install argos-translate: pip install argostranslate")

    def translate_text(self, text: str, target_language: str, source_language: str = "English") -> str:
        """Translates text from source language to target language."""
        src_code = self.LANGUAGE_CODES.get(source_language)
        tgt_code = self.LANGUAGE_CODES.get(target_language)

        if not tgt_code:
            raise ValueError(f"Target language '{target_language}' is not supported.")
        if not src_code:
            raise ValueError(f"Source language '{source_language}' is not supported.")

        if src_code == tgt_code:
            return text

        # Core translation abstraction
        try:
            return self.translator.translate(text, src_code, tgt_code)
        except Exception as e:
            raise RuntimeWarning(f"Translation failed: {str(e)}. Ensure language packages are installed.")


# =====================================================================
# 2. NEURAL STYLE TRANSFER & QR ENGINE (Encapsulation)
# =====================================================================
class StyleTransferEngine:
    """Handles AI Neural Style Transfer and QR Code overlay utilities."""

    def __init__(self, max_res: int = 512, qr_size: int = 120, qr_padding: int = 15):
        self.max_res = max_res
        self.qr_size = qr_size
        self.qr_padding = qr_padding
        self.total_qr_size = qr_size + (qr_padding * 2)
        
        # Load the TF Hub model once during initialization
        self.model = hub.load('https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/2')

    def _preprocess_tensor_image(self, image_bytes: bytes) -> tf.Tensor:
        """Converts raw bytes to a scaled TF Tensor."""
        image = tf.image.decode_image(image_bytes, channels=3)
        image = tf.image.convert_image_dtype(image, tf.float32)

        shape = tf.cast(tf.shape(image)[:-1], tf.float32)
        long_side = max(shape)
        scaling_factor = self.max_res / long_side

        new_shape = tf.cast(shape * scaling_factor, tf.int32)
        image = tf.image.resize(image, new_shape)
        return image[tf.newaxis, ...]

    def _tensor_to_cv2(self, tensor: tf.Tensor) -> np.ndarray:
        """Converts a TF Tensor back into a standard BGR OpenCV Image Matrix."""
        tensor = np.array(tensor * 255, dtype=np.uint8)
        if np.ndim(tensor) > 3:
            tensor = tensor[0]
        return cv2.cvtColor(tensor, cv2.COLOR_RGB2BGR)

    def _generate_qr_overlay(self, url: str) -> np.ndarray:
        """Generates a QR code matrix surrounded by a clean white padded background."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=0,
        )
        qr.add_data(url)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        qr_cv = cv2.cvtColor(np.array(qr_img), cv2.COLOR_RGB2BGR)
        qr_cv_resized = cv2.resize(qr_cv, (self.qr_size, self.qr_size), interpolation=cv2.INTER_NEAREST)

        # Create padded container matrix
        white_background = np.full((self.total_qr_size, self.total_qr_size, 3), 255, dtype=np.uint8)
        p = self.qr_padding
        white_background[p : p + self.qr_size, p : p + self.qr_size] = qr_cv_resized
        return white_background

    def process_stylization(self, content_bytes: bytes, style_bytes: bytes, download_url: str) -> np.ndarray:
        """Executes full pipeline: Styles content image, builds QR code, and embeds overlay."""
        # 1. Tensor Preprocessing
        content_tensor = self._preprocess_tensor_image(content_bytes)
        style_tensor = self._preprocess_tensor_image(style_bytes)

        # 2. Run Neural Style Transfer
        stylized_tensor = self.model(content_tensor, style_tensor)[0]
        final_cv_img = self._tensor_to_cv2(stylized_tensor)

        # 3. Generate and Embed QR code matrix
        img_h, img_w, _ = final_cv_img.shape
        if img_h > self.total_qr_size and img_w > self.total_qr_size:
            qr_overlay = self._generate_qr_overlay(download_url)
            final_cv_img[0:self.total_qr_size, 0:self.total_qr_size] = qr_overlay
        
        return final_cv_img


# =====================================================================
# 3. SERVICE SYSTEM COORDINATOR (High-Level Abstraction)
# =====================================================================
class MediaProcessingService:
    """Unified Facade system coordinating processing workflows for the API."""
    
    def __init__(self):
        self.translation_engine = TranslationEngine()
        self.style_engine = StyleTransferEngine()

    def handle_text_translation(self, file_bytes: bytes, target_lang: str) -> str:
        """Extracts text from an uploaded file and translates it."""
        try:
            raw_text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("The provided file must be a valid text file format (UTF-8 encoded).")
        
        return self.translation_engine.translate_text(raw_text, target_lang)

    def handle_image_stylization(self, content_bytes: bytes, style_bytes: bytes, qr_url: str) -> bytes:
        """Processes style transfer + QR injection, returning ready-to-stream jpeg bytes."""
        cv_result = self.style_engine.process_stylization(content_bytes, style_bytes, qr_url)
        
        # Encode back to file format bytes
        success, encoded_img = cv2.imencode(".jpg", cv_result)
        if not success:
            raise RuntimeError("Failed to encode final image output matrix to JPEG format.")
        
        return encoded_img.tobytes()


# Instantiate the service singleton
media_service = MediaProcessingService()


# =====================================================================
# 4. FASTAPI ROUTING CONTROLLERS
# =====================================================================

@app.post("/translate-file/")
async def translate_file(target_language: str, file: UploadFile = File(...)):
    """Endpoint: Accepts a text file and target language string, returning translated text string."""
    try:
        file_bytes = await file.read()
        translated_text = media_service.handle_text_translation(file_bytes, target_language)
        return {"target_language": target_language, "translated_text": translated_text}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal translation server error: {str(e)}")


@app.post("/style-transfer/")
async def style_transfer(
    download_url: str = "https://example.com/download-my-image.jpg",
    content_file: UploadFile = File(...),
    style_file: UploadFile = File(...)
):
    """Endpoint: Mixes 2 images, embeds a download URL via a QR code, and drops the raw image file."""
    try:
        content_bytes = await content_file.read()
        style_bytes = await style_file.read()
        
        processed_img_bytes = media_service.handle_image_stylization(
            content_bytes=content_bytes, 
            style_bytes=style_bytes, 
            qr_url=download_url
        )
        
        return Response(content=processed_img_bytes, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal computer vision pipeline error: {str(e)}")