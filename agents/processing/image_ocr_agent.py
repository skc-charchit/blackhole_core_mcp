import os
import sys
import io
import tempfile
from pathlib import Path
from datetime import datetime
import numpy as np

# Try to import required libraries with error handling
try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    print("⚠️ pytesseract not installed. OCR functionality will be limited.")

try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("⚠️ PIL/Pillow not installed. Image processing will not work.")

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    print("⚠️ OpenCV (cv2) not installed. Advanced image processing will not work.")

# Tesseract executable path - try to detect OS and set accordingly
if HAS_TESSERACT:
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
        print(f"✅ Tesseract found at {tesseract_cmd}")
    else:
        print(f"⚠️ Tesseract not found at {tesseract_cmd}. OCR may not work correctly.")

# Initialize organized storage directories
def initialize_storage_directories():
    """Initialize organized storage directories for images and outputs."""
    uploaded_images_dir = Path("data/multimodal/uploaded_images")
    processed_outputs_dir = Path("data/multimodal/processed_outputs")

    uploaded_images_dir.mkdir(parents=True, exist_ok=True)
    processed_outputs_dir.mkdir(parents=True, exist_ok=True)

    return uploaded_images_dir, processed_outputs_dir

def save_processed_image(image, original_filename, suffix="_processed"):
    """Save processed image to organized outputs folder."""
    try:
        _, processed_outputs_dir = initialize_storage_directories()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = Path(original_filename).stem
        output_filename = f"{timestamp}_{base_name}{suffix}.png"
        output_path = processed_outputs_dir / output_filename

        image.save(output_path)
        print(f"✅ Processed image saved to {output_path}")
        return str(output_path)

    except Exception as e:
        print(f"❌ Error saving processed image: {e}")
        return ""

def save_extracted_text(text, original_filename):
    """Save extracted text to organized outputs folder."""
    try:
        _, processed_outputs_dir = initialize_storage_directories()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = Path(original_filename).stem
        output_filename = f"{timestamp}_{base_name}_extracted.txt"
        output_path = processed_outputs_dir / output_filename

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)

        print(f"✅ Extracted text saved to {output_path}")
        return str(output_path)

    except Exception as e:
        print(f"❌ Error saving extracted text: {e}")
        return ""

def preprocess_image(image_path_or_object, preprocessing_level=2):
    """
    Preprocess an image for better OCR results.

    Args:
        image_path_or_object: Path to image file or PIL Image object
        preprocessing_level: 1=minimal, 2=standard, 3=aggressive

    Returns:
        PIL Image: Processed image ready for OCR
    """
    # Check if required libraries are available
    if not HAS_PIL:
        print("⚠️ PIL/Pillow not installed. Cannot preprocess image.")
        return image_path_or_object

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

        # If OpenCV is not available, return the grayscale image
        if not HAS_CV2 and preprocessing_level >= 2:
            print("⚠️ OpenCV not available. Using basic preprocessing only.")
            # Apply basic PIL enhancements instead
            enhancer = ImageEnhance.Contrast(gray_image)
            result = enhancer.enhance(2)

            # Apply sharpening if aggressive preprocessing is requested
            if preprocessing_level >= 3:
                result = result.filter(ImageFilter.SHARPEN)

            return result

        if preprocessing_level >= 2 and HAS_CV2:
            # Standard preprocessing with OpenCV
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

        if preprocessing_level >= 3 and HAS_CV2:
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
        if isinstance(image_path_or_object, str) and HAS_PIL:
            try:
                return Image.open(image_path_or_object)
            except:
                print(f"⚠️ Could not open image: {image_path_or_object}")
        return image_path_or_object

def repair_image(image_path):
    """
    Attempt to repair a corrupted image file.

    Args:
        image_path: Path to the potentially corrupted image file

    Returns:
        str: Path to the repaired image or None if repair failed
    """
    try:
        # Create a temporary file for the repaired image
        temp_dir = tempfile.gettempdir()
        base_name = os.path.basename(image_path)
        name_without_ext = os.path.splitext(base_name)[0]
        repaired_path = os.path.join(temp_dir, f"{name_without_ext}_repaired.png")

        # Try to repair the image using binary manipulation
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Look for JPEG markers
            if b'\xff\xd8' in image_data:  # JPEG SOI marker
                print("✅ JPEG signature found, attempting repair")
                # Find the start of image marker
                start_idx = image_data.find(b'\xff\xd8')
                if start_idx > 0:
                    # Trim any garbage at the beginning
                    image_data = image_data[start_idx:]

                # Write the repaired data
                with open(repaired_path, 'wb') as f:
                    f.write(image_data)
                return repaired_path

            # Look for PNG markers
            elif b'\x89PNG\r\n\x1a\n' in image_data:  # PNG signature
                print("✅ PNG signature found, attempting repair")
                # Find the start of PNG signature
                start_idx = image_data.find(b'\x89PNG\r\n\x1a\n')
                if start_idx > 0:
                    # Trim any garbage at the beginning
                    image_data = image_data[start_idx:]

                # Write the repaired data
                with open(repaired_path, 'wb') as f:
                    f.write(image_data)
                return repaired_path

            # If no known signatures found, try a more aggressive approach
            print("⚠️ No standard image signatures found, trying aggressive repair")

            # Create a new blank image
            try:
                # Try to get image dimensions using OpenCV
                img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
                if img is not None and img.size > 0:
                    # If OpenCV can read it, save it
                    cv2.imwrite(repaired_path, img)
                    return repaired_path
            except:
                pass

            # If all else fails, create a small blank image with error message
            blank_img = np.ones((300, 500, 3), np.uint8) * 255  # White background
            # Add error text
            cv2.putText(
                blank_img,
                "Image could not be processed",
                (50, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )
            cv2.imwrite(repaired_path, blank_img)
            return repaired_path

        except Exception as e:
            print(f"⚠️ Binary repair failed: {str(e)}")
            return None

    except Exception as e:
        print(f"⚠️ Image repair error: {str(e)}")
        return None

def convert_image_format(image_path, target_format='PNG'):
    """
    Convert an image to a different format to handle problematic files.

    Args:
        image_path: Path to the original image file
        target_format: Format to convert to (default: PNG)

    Returns:
        str: Path to the converted image or original path if conversion failed
    """
    try:
        # Create a temporary file with the target format
        temp_dir = tempfile.gettempdir()
        base_name = os.path.basename(image_path)
        name_without_ext = os.path.splitext(base_name)[0]
        converted_path = os.path.join(temp_dir, f"{name_without_ext}.{target_format.lower()}")

        # Try different methods to open the image
        try:
            # Method 1: Direct PIL open
            with Image.open(image_path) as img:
                img.save(converted_path, format=target_format)
                print(f"✅ Successfully converted image using PIL direct method")
                return converted_path
        except Exception as e1:
            print(f"⚠️ PIL direct open failed: {str(e1)}")

            try:
                # Method 2: Use OpenCV to read and convert
                img = cv2.imread(image_path)
                if img is not None:
                    cv2.imwrite(converted_path, img)
                    print(f"✅ Successfully converted image using OpenCV")
                    return converted_path
            except Exception as e2:
                print(f"⚠️ OpenCV conversion failed: {str(e2)}")

                try:
                    # Method 3: Read as binary and use PIL's Image.open with a BytesIO object
                    with open(image_path, 'rb') as f:
                        image_data = f.read()
                        with Image.open(io.BytesIO(image_data)) as img:
                            img.save(converted_path, format=target_format)
                            print(f"✅ Successfully converted image using BytesIO method")
                            return converted_path
                except Exception as e3:
                    print(f"⚠️ BytesIO conversion failed: {str(e3)}")

                    # Method 4: Try to repair the image
                    repaired_path = repair_image(image_path)
                    if repaired_path:
                        print(f"✅ Successfully repaired and converted image")
                        return repaired_path

        # If all methods failed, return the original path
        print("⚠️ All conversion methods failed, returning original path")
        return image_path

    except Exception as e:
        print(f"⚠️ Image conversion error: {str(e)}")
        return image_path

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
    # Check if required libraries are available
    if not HAS_TESSERACT:
        return "❌ Tesseract OCR is not installed. Cannot extract text from images."

    if not HAS_PIL:
        return "❌ PIL/Pillow is not installed. Cannot process images."

    # Expanded list of supported formats
    supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.gif', '.heic', '.heif')

    # Check if file exists
    if not os.path.exists(image_path):
        return f"❌ File not found: {image_path}"

    # Check file extension
    if not any(image_path.lower().endswith(ext) for ext in supported_formats):
        print(f"⚠️ File extension not in supported formats list: {os.path.splitext(image_path)[-1]}")
        # We'll still try to process it

    try:
        print(f"🖼️  Reading image from: {image_path}")

        # Try to open the image
        try:
            # First try to open directly
            Image.open(image_path)
            working_path = image_path
        except Exception as e:
            print(f"⚠️ Error opening image: {str(e)}. Trying to convert format...")
            # If direct open fails, try to convert the image format
            working_path = convert_image_format(image_path)
            if working_path == image_path:
                # If conversion failed, try to repair the image
                print(f"⚠️ Conversion failed. Trying to repair the image...")
                repaired_path = repair_image(image_path)
                if repaired_path:
                    working_path = repaired_path
                    print(f"✅ Image repaired successfully")
                else:
                    # If repair failed, create a blank image with error message
                    if HAS_CV2:
                        temp_dir = tempfile.gettempdir()
                        error_img_path = os.path.join(temp_dir, "error_image.png")
                        blank_img = np.ones((300, 500, 3), np.uint8) * 255  # White background
                        # Add error text
                        cv2.putText(
                            blank_img,
                            "Image could not be processed",
                            (50, 150),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 0, 255),
                            2
                        )
                        cv2.imwrite(error_img_path, blank_img)
                        working_path = error_img_path
                        print(f"⚠️ Created error image at {error_img_path}")
                    # Return error message
                    return f"❌ Error: cannot identify image file '{image_path}'. Repair attempts failed."

        # First attempt with standard preprocessing
        processed_image = preprocess_image(working_path, preprocessing_level=preprocessing_level)

        if debug and HAS_PIL:
            # Save to organized outputs folder
            debug_path = save_processed_image(processed_image, image_path, "_preprocessed")
            if debug_path:
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

                alt_processed = preprocess_image(working_path, preprocessing_level=level)

                if debug and HAS_PIL:
                    save_processed_image(alt_processed, image_path, f"_preprocessed_level{level}")

                # Try different PSM modes
                for psm in [3, 4, 11, 12]:  # Different page segmentation modes
                    alt_config = f'--oem 3 --psm {psm}'
                    alt_text = pytesseract.image_to_string(alt_processed, config=alt_config)

                    if alt_text and len(alt_text.strip()) > len(text.strip()):
                        print(f"✅ Better results with preprocessing level {level} and PSM {psm}")
                        text = alt_text

            # If still no good results, try inverting the image
            if (not text or len(text.strip()) < 10) and HAS_PIL:
                try:
                    with Image.open(working_path) as img:
                        inverted_image = ImageOps.invert(img.convert('RGB'))
                        inverted_processed = preprocess_image(inverted_image, preprocessing_level=2)

                        if debug:
                            save_processed_image(inverted_processed, image_path, "_inverted")

                        inv_text = pytesseract.image_to_string(inverted_processed, config=r'--oem 3 --psm 6')
                        if inv_text and len(inv_text.strip()) > len(text.strip()):
                            print("✅ Better results with inverted image")
                            text = inv_text
                except Exception as e:
                    print(f"⚠️ Error inverting image: {str(e)}")

            # If we still have no text, try one more approach with OpenCV
            if (not text or len(text.strip()) < 10) and HAS_CV2:
                try:
                    print("⚠️ Still no text. Trying OpenCV approach...")
                    # Read image with OpenCV
                    img = cv2.imread(working_path)
                    if img is not None:
                        # Convert to grayscale
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        # Apply threshold
                        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                        # Save to temp file
                        temp_path = os.path.join(tempfile.gettempdir(), "ocv_processed.png")
                        cv2.imwrite(temp_path, thresh)
                        # OCR on the processed image
                        ocv_text = pytesseract.image_to_string(Image.open(temp_path), config=r'--oem 3 --psm 6')
                        if ocv_text and len(ocv_text.strip()) > len(text.strip()):
                            print("✅ Better results with OpenCV processing")
                            text = ocv_text
                except Exception as e:
                    print(f"⚠️ OpenCV approach failed: {str(e)}")

        # Clean up temporary files if needed
        if working_path != image_path and os.path.exists(working_path):
            try:
                # Uncomment to delete temporary files
                # os.remove(working_path)
                pass
            except:
                pass

        return text.strip() if text else "No text detected in image."

    except Exception as e:
        print(f"❌ Error extracting text from image: {str(e)}")
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    # Use command line argument if provided
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # Check for user-uploaded images in the organized folder
        uploaded_images_dir = Path("data/multimodal/uploaded_images")
        if uploaded_images_dir.exists():
            image_files = []
            for ext in ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tiff', '*.tif', '*.webp', '*.gif', '*.heic', '*.heif']:
                image_files.extend(uploaded_images_dir.glob(ext))

            if image_files:
                # Use the most recent uploaded image
                image_path = str(max(image_files, key=os.path.getctime))
                print(f"📁 Using most recent uploaded image: {image_path}")
            else:
                print("❌ No image files found in uploaded_images folder.")
                print("Please upload an image file first or provide an image file path as an argument.")
                print("Usage: python image_ocr.py path/to/your/image.jpg")
                sys.exit(1)
        else:
            print("❌ Please provide an image file path as an argument.")
            print("Usage: python image_ocr.py path/to/your/image.jpg")
            sys.exit(1)

    print(f"🖼️ Processing image: {image_path}")
    result = extract_text_from_image(image_path, debug=True)
    print("\n🔍 Extracted Text:\n", result)

    # Save extracted text to organized outputs folder
    if result and not result.startswith("❌"):
        text_file_path = save_extracted_text(result, image_path)
        if text_file_path:
            print(f"\n💾 Text saved to: {text_file_path}")
