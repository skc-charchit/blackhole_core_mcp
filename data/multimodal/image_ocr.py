import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import cv2
import numpy as np
import os

# Tesseract executable path (move to .env later if desired)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image_path):
    image = Image.open(image_path)
    gray_image = image.convert("L")
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

    return Image.fromarray(processed_image)

def extract_text_from_image(image_path, debug=False):
    supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')
    if not image_path.lower().endswith(supported_formats):
        return f"❌ Unsupported file type: {os.path.splitext(image_path)[-1]}"

    try:
        print(f"🖼️  Reading image from: {image_path}")
        processed_image = preprocess_image(image_path)

        if debug:
            debug_path = os.path.splitext(image_path)[0] + "_preprocessed.png"
            processed_image.save(debug_path)
            print(f"📄 Preprocessed image saved at: {debug_path}")

        config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(processed_image, config=config)
        return text.strip()

    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    image_path = r"D:\Work_Station\blackhole_core\data\multimodal\black-white-color-quotes-dave-matthews-nothing-is-black-or-white-nothings-us-o-2042.webp"
    result = extract_text_from_image(image_path, debug=True)
    print("\n🔍 Extracted Text:\n", result)
