#blackhole_core/data_source/run_multimodal_demo.py
import os
from data.multimodal.pdf_reader import extract_text_from_pdf
from data.multimodal.image_ocr import extract_text_from_image

# Base directory pointing to data/multimodal relative to this file
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "multimodal"))

def test_pdf_reader():
    print("\n📄 PDF Text Extraction Test")
    pdf_path = os.path.join(base_dir, "sample.pdf")
    print(f"Reading PDF from: {pdf_path}")

    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found at {pdf_path}")
        return

    text = extract_text_from_pdf(pdf_path)
    print("Extracted Text:\n", text)
    print("-" * 60)

def test_image_ocr():
    print("\n🖼️ Image OCR Test")
    image_path = os.path.join(base_dir, "black-white-color-quotes-dave-matthews-nothing-is-black-or-white-nothings-us-o-2042_preprocessed.png")
    print(f"Reading Image from: {image_path}")

    if not os.path.exists(image_path):
        print(f"❌ Image file not found at {image_path}")
        return

    text = extract_text_from_image(image_path)
    print("Extracted Text:\n", text)
    print("-" * 60)

if __name__ == "__main__":
    test_pdf_reader()
    test_image_ocr()
