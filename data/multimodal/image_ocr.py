import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError
import cv2
import numpy as np
import os
import io
import tempfile
import sys
from pathlib import Path

# Tesseract executable path - try to detect OS and set accordingly
if sys.platform.startswith('win'):
    # Windows
    tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if not os.path.exists(tesseract_cmd):
        tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
elif sys.platform.startswith('darwin'):
    # macOS
    tesseract_cmd = '/usr/local/bin/tesseract'
else:
    # Linux/Unix
    tesseract_cmd = '/usr/bin/tesseract'

# Set Tesseract path if it exists
if os.path.exists(tesseract_cmd):
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
else:
    print(f"⚠️ Tesseract not found at {tesseract_cmd}. OCR may not work correctly.")

def preprocess_image(image_path_or_object, preprocessing_level=2):
    """
    Preprocess an image for better OCR results.

    Args:
        image_path_or_object: Path to image file or PIL Image object
        preprocessing_level: 1=minimal, 2=standard, 3=aggressive

    Returns:
        PIL Image: Processed image ready for OCR
    """
    try:
        # Handle both file paths and PIL Image objects
        if isinstance(image_path_or_object, str):
            image = Image.open(image_path_or_object)
        elif isinstance(image_path_or_object, Image.Image):
            image = image_path_or_object
        else:
            raise ValueError("Input must be a file path or PIL Image object")

        # Check if image is too large and resize if needed
        max_dimension = 4000  # Prevent memory issues with very large images
        if max(image.size) > max_dimension:
            ratio = max_dimension / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.LANCZOS)

        # Basic preprocessing for all levels
        gray_image = image.convert("L")

        if preprocessing_level >= 2:
            # Standard preprocessing
            enhancer = ImageEnhance.Contrast(gray_image)
            enhanced_image = enhancer.enhance(2)

            # Convert to OpenCV format
            open_cv_image = np.array(enhanced_image)

            # Adaptive thresholding for variable lighting
            thresh_image = cv2.adaptiveThreshold(
                open_cv_image, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )

            # Morphological operations
            kernel = np.ones((3, 3), np.uint8)
            processed_image = cv2.morphologyEx(thresh_image, cv2.MORPH_CLOSE, kernel)

            result = Image.fromarray(processed_image)
        else:
            # Minimal preprocessing
            result = gray_image

        if preprocessing_level >= 3:
            # Aggressive preprocessing
            # Convert back to PIL for additional processing
            result = Image.fromarray(processed_image)

            # Apply additional filters
            result = result.filter(ImageFilter.SHARPEN)

            # Deskew if needed
            try:
                # Use OpenCV to find rotation angle
                img_array = np.array(result)
                coords = np.column_stack(np.where(img_array > 0))
                angle = cv2.minAreaRect(coords)[-1]

                if angle < -45:
                    angle = -(90 + angle)
                else:
                    angle = -angle

                # Rotate if angle is significant
                if abs(angle) > 0.5:
                    result = result.rotate(angle, expand=True, fillcolor=255)
            except Exception:
                # Skip deskewing if it fails
                pass

        return result

    except Exception as e:
        print(f"⚠️ Image preprocessing error: {str(e)}")
        # Return original image if preprocessing fails
        if isinstance(image_path_or_object, str):
            return Image.open(image_path_or_object)
        return image_path_or_object

def extract_text_from_image(image_path, debug=False, preprocessing_level=2, try_multiple_methods=True):
    """
    Extract text from an image using OCR with enhanced capabilities.

    Args:
        image_path: Path to the image file
        debug: Whether to save debug images
        preprocessing_level: Level of preprocessing (1=minimal, 2=standard, 3=aggressive)
        try_multiple_methods: Try different preprocessing and OCR settings if initial attempt fails

    Returns:
        str: Extracted text or error message
    """
    # Expanded list of supported formats
    supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.gif', '.heic', '.heif')

    # Check file extension
    if not any(image_path.lower().endswith(ext) for ext in supported_formats):
        # Try to open it anyway - some files might have wrong extensions
        try:
            Image.open(image_path)
        except UnidentifiedImageError:
            return f"❌ Unsupported file type: {os.path.splitext(image_path)[-1]}"

    # Check if file exists
    if not os.path.exists(image_path):
        return f"❌ File not found: {image_path}"

    try:
        print(f"🖼️  Reading image from: {image_path}")

        # First attempt with standard preprocessing
        processed_image = preprocess_image(image_path, preprocessing_level=preprocessing_level)

        if debug:
            debug_path = os.path.splitext(image_path)[0] + "_preprocessed.png"
            processed_image.save(debug_path)
            print(f"📄 Preprocessed image saved at: {debug_path}")

        # Standard OCR configuration
        config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(processed_image, config=config)

        # If text is empty or very short and we want to try multiple methods
        if try_multiple_methods and (not text or len(text.strip()) < 10):
            print("⚠️ Initial OCR produced little or no text. Trying alternative methods...")

            # Try different preprocessing levels
            for level in [1, 3]:  # Try minimal and aggressive preprocessing
                if level == preprocessing_level:
                    continue  # Skip the level we already tried

                alt_processed = preprocess_image(image_path, preprocessing_level=level)

                if debug:
                    alt_debug_path = os.path.splitext(image_path)[0] + f"_preprocessed_level{level}.png"
                    alt_processed.save(alt_debug_path)

                # Try different PSM modes
                for psm in [3, 4, 11, 12]:  # Different page segmentation modes
                    alt_config = f'--oem 3 --psm {psm}'
                    alt_text = pytesseract.image_to_string(alt_processed, config=alt_config)

                    if alt_text and len(alt_text.strip()) > len(text.strip()):
                        print(f"✅ Better results with preprocessing level {level} and PSM {psm}")
                        text = alt_text

            # If still no good results, try inverting the image
            if not text or len(text.strip()) < 10:
                inverted_image = ImageOps.invert(Image.open(image_path).convert('RGB'))
                inverted_processed = preprocess_image(inverted_image, preprocessing_level=2)

                if debug:
                    inv_debug_path = os.path.splitext(image_path)[0] + "_inverted.png"
                    inverted_processed.save(inv_debug_path)

                inv_text = pytesseract.image_to_string(inverted_processed, config=r'--oem 3 --psm 6')
                if inv_text and len(inv_text.strip()) > len(text.strip()):
                    print("✅ Better results with inverted image")
                    text = inv_text

        return text.strip()

    except Exception as e:
        print(f"❌ Error extracting text from image: {str(e)}")
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    image_path = r"D:\Work_Station\blackhole_core\data\multimodal\black-white-color-quotes-dave-matthews-nothing-is-black-or-white-nothings-us-o-2042.webp"
    result = extract_text_from_image(image_path, debug=True)
    print("\n🔍 Extracted Text:\n", result)
