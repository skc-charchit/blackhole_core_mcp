import os
from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_path):
    supported_formats = ('.pdf',)
    if not pdf_path.lower().endswith(supported_formats):
        return f"❌ Unsupported file type: {os.path.splitext(pdf_path)[-1]}"

    try:
        print(f"📄 Reading PDF from: {pdf_path}")
        reader = PdfReader(pdf_path)
        extracted_text = ""

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text:
                extracted_text += f"\n--- Page {page_number} ---\n{text}\n"

        return extracted_text.strip() or "⚠️ No text found in PDF."

    except Exception as e:
        return f"❌ Error processing PDF: {str(e)}"

if __name__ == "__main__":
    pdf_path = r"D:\Work_Station\blackhole_core\data\multimodal\sample.pdf"
    result = extract_text_from_pdf(pdf_path)
    print("\n🔍 Extracted Text:\n", result)
