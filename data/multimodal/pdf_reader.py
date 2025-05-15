import os
import sys
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError

def extract_text_from_pdf(pdf_path, include_page_numbers=True, verbose=True):
    """
    Extract text from a PDF file.

    Args:
        pdf_path (str): Path to the PDF file
        include_page_numbers (bool): Whether to include page numbers in the output
        verbose (bool): Whether to print status messages

    Returns:
        str: Extracted text or error message
    """
    supported_formats = ('.pdf',)
    if not pdf_path.lower().endswith(supported_formats):
        return f"❌ Unsupported file type: {os.path.splitext(pdf_path)[-1]}"

    if not os.path.exists(pdf_path):
        return f"❌ File not found: {pdf_path}"

    try:
        if verbose:
            print(f"📄 Reading PDF from: {pdf_path}")

        reader = PdfReader(pdf_path)

        if len(reader.pages) == 0:
            return "⚠️ PDF has no pages."

        extracted_text = ""

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text:
                if include_page_numbers:
                    extracted_text += f"\n--- Page {page_number} ---\n{text}\n"
                else:
                    extracted_text += f"{text}\n"

        result = extracted_text.strip()
        if not result:
            return "⚠️ No text found in PDF. The file may be scanned images or protected."
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
            os.path.join(current_dir, "sample.pdf"),
            os.path.join(current_dir, "..", "sample.pdf"),
            os.path.join(current_dir, "..", "..", "sample.pdf")
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
