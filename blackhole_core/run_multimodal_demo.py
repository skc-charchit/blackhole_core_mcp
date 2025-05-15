#blackhole_core/run_multimodal_demo.py
import os
import sys
import traceback

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from data.multimodal.pdf_reader import extract_text_from_pdf
    from data.multimodal.image_ocr import extract_text_from_image
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("⚠️ Make sure you're running this script from the project root directory.")
    sys.exit(1)

# Base directory pointing to data/multimodal relative to this file
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "multimodal"))

def test_pdf_reader():
    try:
        print("\n📄 PDF Text Extraction Test")
        pdf_path = os.path.join(base_dir, "sample.pdf")
        print(f"Reading PDF from: {pdf_path}")

        if not os.path.exists(pdf_path):
            print(f"❌ PDF file not found at {pdf_path}")
            return

        # The extract_text_from_pdf function now handles file existence check internally
        text = extract_text_from_pdf(pdf_path, include_page_numbers=True, verbose=True)
        print("Extracted Text:\n", text)
        print("-" * 60)
    except Exception as e:
        print(f"❌ Error in PDF reader test: {e}")
        traceback.print_exc()

def test_image_ocr():
    try:
        print("\n🖼️ Image OCR Test")

        # Try both the preprocessed and original image
        image_paths = [
            os.path.join(base_dir, "black-white-color-quotes-dave-matthews-nothing-is-black-or-white-nothings-us-o-2042_preprocessed.png"),
            os.path.join(base_dir, "black-white-color-quotes-dave-matthews-nothing-is-black-or-white-nothings-us-o-2042.webp")
        ]

        for image_path in image_paths:
            if os.path.exists(image_path):
                print(f"Reading Image from: {image_path}")
                text = extract_text_from_image(image_path)
                print("Extracted Text:\n", text)
                print("-" * 60)
                return  # Exit after first successful image processing

        print(f"❌ No valid image files found in the expected locations")
    except Exception as e:
        print(f"❌ Error in image OCR test: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        test_pdf_reader()
        test_image_ocr()
    except Exception as e:
        print(f"❌ Unhandled error: {e}")
        traceback.print_exc()
