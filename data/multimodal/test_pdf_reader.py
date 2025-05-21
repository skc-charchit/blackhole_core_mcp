import os
import sys
from pdf_reader import extract_text_from_pdf, save_extracted_text

def test_pdf_reader():
    """Test the PDF reader with various options."""
    
    # Try to find a sample PDF
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
        print("❌ No sample PDF found. Please provide a PDF file path as an argument.")
        if len(sys.argv) > 1:
            pdf_path = sys.argv[1]
        else:
            return
    
    print(f"🔍 Testing PDF reader with file: {pdf_path}")
    
    # Test 1: Default settings
    print("\n🧪 Test 1: Default settings (with page numbers)")
    result1 = extract_text_from_pdf(pdf_path)
    print(f"Result: {result1[:200]}..." if len(result1) > 200 else f"Result: {result1}")
    
    # Test 2: Without page numbers
    print("\n🧪 Test 2: Without page numbers")
    result2 = extract_text_from_pdf(pdf_path, include_page_numbers=False)
    print(f"Result: {result2[:200]}..." if len(result2) > 200 else f"Result: {result2}")
    
    # Test 3: With quiet mode
    print("\n🧪 Test 3: Quiet mode (no verbose output)")
    result3 = extract_text_from_pdf(pdf_path, verbose=False)
    print(f"Result: {result3[:200]}..." if len(result3) > 200 else f"Result: {result3}")
    
    # Test 4: Save to file
    print("\n🧪 Test 4: Save to file")
    output_path = os.path.join(current_dir, "test_output.txt")
    save_extracted_text(result1, output_path)
    
    # Test 5: Invalid file
    print("\n🧪 Test 5: Invalid file")
    invalid_path = os.path.join(current_dir, "nonexistent.pdf")
    result5 = extract_text_from_pdf(invalid_path)
    print(f"Result: {result5}")
    
    # Test 6: Non-PDF file
    print("\n🧪 Test 6: Non-PDF file")
    non_pdf_path = __file__  # Use this script as a non-PDF file
    result6 = extract_text_from_pdf(non_pdf_path)
    print(f"Result: {result6}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    test_pdf_reader()
