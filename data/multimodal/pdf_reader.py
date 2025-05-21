import os
import sys
import io
import tempfile
import subprocess
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError

# Try to import optional OCR libraries
try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

# Set Tesseract path based on OS
if sys.platform.startswith('win'):
    # Windows
    tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if not os.path.exists(tesseract_cmd):
        tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
    if os.path.exists(tesseract_cmd) and HAS_OCR:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
elif sys.platform.startswith('darwin'):
    # macOS
    tesseract_cmd = '/usr/local/bin/tesseract'
    if os.path.exists(tesseract_cmd) and HAS_OCR:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
else:
    # Linux/Unix
    tesseract_cmd = '/usr/bin/tesseract'
    if os.path.exists(tesseract_cmd) and HAS_OCR:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

def extract_text_from_pdf(pdf_path, include_page_numbers=True, verbose=True, try_ocr=True):
    """
    Extract text from a PDF file with enhanced capabilities.

    Args:
        pdf_path (str): Path to the PDF file
        include_page_numbers (bool): Whether to include page numbers in the output
        verbose (bool): Whether to print status messages
        try_ocr (bool): Whether to try OCR if no text is found in the PDF

    Returns:
        str: Extracted text or error message
    """
    # Check file extension
    supported_formats = ('.pdf',)
    if not pdf_path.lower().endswith(supported_formats):
        return f"❌ Unsupported file type: {os.path.splitext(pdf_path)[-1]}"

    # Check if file exists
    if not os.path.exists(pdf_path):
        return f"❌ File not found: {pdf_path}"

    try:
        if verbose:
            print(f"📄 Reading PDF from: {pdf_path}")

        # Try to read the PDF with PyPDF2
        reader = PdfReader(pdf_path)

        if len(reader.pages) == 0:
            return "⚠️ PDF has no pages."

        extracted_text = ""
        empty_pages = 0

        # Extract text from each page
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text()

            # If text extraction failed, try alternative methods
            if not text or text.isspace():
                empty_pages += 1
                if verbose:
                    print(f"⚠️ No text found on page {page_number} using standard extraction.")

            # Add the text to the result
            if text:
                if include_page_numbers:
                    extracted_text += f"\n--- Page {page_number} ---\n{text}\n"
                else:
                    extracted_text += f"{text}\n"

        # Check if we got any text
        result = extracted_text.strip()

        # If no text was found and OCR is available, try OCR
        if (not result or empty_pages == len(reader.pages)) and try_ocr and HAS_OCR:
            if verbose:
                print("🔍 No text found using standard extraction. Trying OCR...")

            ocr_text = ""

            try:
                # Import pdf2image here to avoid import errors if it's not installed
                from pdf2image import convert_from_path

                # Process each page with OCR
                for page_number, page in enumerate(reader.pages, start=1):
                    if verbose:
                        print(f"🔍 Processing page {page_number} with OCR...")

                    try:
                        # Extract the page as an image
                        images = convert_from_path(pdf_path, first_page=page_number, last_page=page_number)

                        if images:
                            # Process the image with OCR
                            page_text = pytesseract.image_to_string(images[0])

                            if page_text:
                                if include_page_numbers:
                                    ocr_text += f"\n--- Page {page_number} (OCR) ---\n{page_text}\n"
                                else:
                                    ocr_text += f"{page_text}\n"
                    except Exception as ocr_err:
                        if verbose:
                            print(f"⚠️ OCR failed for page {page_number}: {str(ocr_err)}")
            except ImportError:
                if verbose:
                    print("⚠️ pdf2image module not found. OCR processing requires pdf2image.")
            except Exception as e:
                if verbose:
                    print(f"⚠️ OCR processing failed: {str(e)}")

            # If OCR found text, use it
            if ocr_text.strip():
                result = ocr_text.strip()
                if verbose:
                    print("✅ Successfully extracted text using OCR.")

        # If still no text, return a warning
        if not result:
            return "⚠️ No text found in PDF. The file may contain only images or be protected."

        return result

    except PdfReadError as e:
        return f"❌ Error reading PDF: {str(e)}. The file may be corrupted or password-protected."
    except PermissionError:
        return f"❌ Permission denied: Cannot access {pdf_path}"
    except Exception as e:
        return f"❌ Error processing PDF: {str(e)}"

def save_extracted_text(text, output_path):
    """
    Save extracted text to a file.

    Args:
        text (str): Text to save
        output_path (str): Path to save the text to

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"✅ Text saved to: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving text: {str(e)}")
        return False

if __name__ == "__main__":
    # Use command line argument if provided, otherwise use a default path
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Try to find a sample PDF in the current directory or parent directories
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sample_paths = [
            os.path.join(current_dir, "stats.pdf"),
            os.path.join(current_dir, "..", "stats.pdf"),
            os.path.join(current_dir, "..", "..", "stats.pdf")
        ]

        pdf_path = None
        for path in sample_paths:
            if os.path.exists(path):
                pdf_path = path
                break

        if not pdf_path:
            print("❌ Please provide a PDF file path as an argument.")
            print("Usage: python pdf_reader.py path/to/your/file.pdf")
            sys.exit(1)

    # Extract text
    result = extract_text_from_pdf(pdf_path)
    print("\n🔍 Extracted Text:\n", result)

    # Optionally save to file if requested
    if len(sys.argv) > 2 and sys.argv[2] == "--save":
        output_path = os.path.splitext(pdf_path)[0] + ".txt"
        save_extracted_text(result, output_path)
