import os
import sys
import io
import tempfile
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import optional OCR libraries
try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("⚠️ OCR libraries not available. Install pytesseract and Pillow for OCR functionality.")

# Try to import LangChain libraries for LLM functionality
try:
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
    from langchain_community.vectorstores import FAISS
    from langchain.memory import ConversationBufferMemory  
    from langchain.chains import ConversationalRetrievalChain
    from langchain_core.prompts import PromptTemplate
    from langchain_core.embeddings import Embeddings
    import requests
    HAS_LANGCHAIN = True
    print("✅ LangChain libraries imported successfully, including ConversationBufferMemory")
except ImportError as e:
    HAS_LANGCHAIN = False
    print(f"⚠️ LangChain libraries not available: {e}")
    print("💡 Install with: pip install langchain langchain-community langchain-core")

# Try to import Together.ai
try:
    from langchain_together import Together
    HAS_TOGETHER = True
except ImportError:
    try:
        from langchain_community.llms import Together
        HAS_TOGETHER = True
    except ImportError:
        HAS_TOGETHER = False
        print("⚠️ Together.ai not available. Install langchain-together for LLM functionality.")

# Set Tesseract path based on OS
if HAS_OCR:
    if sys.platform.startswith('win'):
        # Windows
        tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if not os.path.exists(tesseract_cmd):
            tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
        if os.path.exists(tesseract_cmd):
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            print(f"✅ Tesseract found at {tesseract_cmd}")
    elif sys.platform.startswith('darwin'):
        # macOS
        tesseract_cmd = '/usr/local/bin/tesseract'
        if os.path.exists(tesseract_cmd):
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            print(f"✅ Tesseract found at {tesseract_cmd}")
    else:
        # Linux/Unix
        tesseract_cmd = '/usr/bin/tesseract'
        if os.path.exists(tesseract_cmd):
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            print(f"✅ Tesseract found at {tesseract_cmd}")


class TogetherEmbeddings(Embeddings):
    """Together.ai embeddings implementation for LangChain."""

    def __init__(
        self,
        model_name: str = None,
        api_key: Optional[str] = None,
        dimensions: int = 768,
    ):
        """Initialize Together.ai embeddings."""
        self.model_name = model_name or os.getenv("TOGETHER_EMBEDDING_MODEL", "togethercomputer/m2-bert-80M-8k-retrieval")
        self.api_key = api_key or os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("TOGETHER_API_KEY not found in environment variables")

        self.dimensions = dimensions
        self.base_url = "https://api.together.xyz/v1/embeddings"

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model_name,
            "input": text
        }

        response = requests.post(self.base_url, headers=headers, json=data)

        if response.status_code != 200:
            raise ValueError(f"Error from Together.ai API: {response.text}")

        result = response.json()
        embedding = result["data"][0]["embedding"]

        return embedding

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        return [self._get_embedding(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        """Embed a query."""
        return self._get_embedding(text)


class EnhancedPDFReader:
    """Enhanced PDF reader with LLM question-answering capabilities."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the enhanced PDF reader."""
        self.api_key = api_key or os.getenv("TOGETHER_API_KEY")
        self.model_name = os.getenv("TOGETHER_MODEL_NAME", "deepseek-ai/DeepSeek-V3")
        self.embedding_model = os.getenv("TOGETHER_EMBEDDING_MODEL", "togethercomputer/m2-bert-80M-8k-retrieval")

        # Text processing settings
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "500"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "50"))

        # LLM settings
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2048"))
        self.memory_k = int(os.getenv("LLM_MEMORY_K", "5"))

        # Storage paths for organized file management
        self.uploaded_pdfs_dir = Path("data/multimodal/uploaded_pdfs")
        self.processed_outputs_dir = Path("data/multimodal/processed_outputs")

        # Create directories if they don't exist
        self.uploaded_pdfs_dir.mkdir(parents=True, exist_ok=True)
        self.processed_outputs_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.llm = None
        self.embeddings = None
        self.text_splitter = None
        self.vectorstore = None
        self.qa_chain = None
        self.memory = None

        # Initialize if LangChain is available
        if HAS_LANGCHAIN and HAS_TOGETHER and self.api_key:
            self._initialize_llm_components()
        else:
            print("⚠️ LLM functionality not available. Missing dependencies or API key.")

    def _initialize_llm_components(self):
        """Initialize LLM components."""
        try:
            # Set API key in environment
            os.environ["TOGETHER_API_KEY"] = self.api_key

            # Initialize LLM
            self.llm = Together(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            # Initialize embeddings
            self.embeddings = TogetherEmbeddings(
                model_name=self.embedding_model,
                api_key=self.api_key
            )

            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )

            # Initialize memory
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                k=self.memory_k
            )

            print("✅ LLM components initialized successfully")

        except Exception as e:
            print(f"⚠️ Error initializing LLM components: {e}")
            self.llm = None

    def extract_text_from_pdf(self, pdf_path: str, include_page_numbers: bool = True,
                             verbose: bool = True, try_ocr: bool = True) -> str:
        """Extract text from PDF with enhanced capabilities."""
        return extract_text_from_pdf(pdf_path, include_page_numbers, verbose, try_ocr)

    def load_and_process_pdf(self, pdf_path: str, verbose: bool = True) -> bool:
        """Load and process a PDF for question answering."""
        if not HAS_LANGCHAIN or not self.llm:
            print("⚠️ LLM functionality not available")
            return False

        try:
            if verbose:
                print(f"📄 Loading PDF: {pdf_path}")

            # Load PDF using LangChain
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()

            if not documents:
                print("❌ No content found in PDF")
                return False

            if verbose:
                print(f"✅ Loaded {len(documents)} pages from PDF")

            # Split documents into chunks
            split_docs = self.text_splitter.split_documents(documents)

            if verbose:
                print(f"✅ Split into {len(split_docs)} chunks")

            # Create vector store
            self.vectorstore = FAISS.from_documents(split_docs, self.embeddings)

            # Create QA chain
            prompt_template = PromptTemplate(
                input_variables=["context", "question"],
                template="""You are an expert assistant. Use the following document content to answer the user's question accurately and comprehensively.

Context: {context}

Question: {question}

Answer: Provide a detailed and accurate answer based on the document content. If the information is not available in the document, clearly state that."""
            )

            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.vectorstore.as_retriever(search_type="similarity"),
                memory=self.memory,
                combine_docs_chain_kwargs={"prompt": prompt_template}
            )

            if verbose:
                print("✅ PDF processed and ready for questions")

            return True

        except Exception as e:
            print(f"❌ Error processing PDF: {e}")
            return False

    def ask_question(self, question: str, verbose: bool = True) -> str:
        """Ask a question about the loaded PDF."""
        if not self.qa_chain:
            return "❌ No PDF loaded. Please load a PDF first using load_and_process_pdf()."

        try:
            if verbose:
                print(f"🤔 Processing question: {question}")

            response = self.qa_chain.invoke({"question": question})
            answer = response.get("answer", "I couldn't find an answer to that question in the document.")

            if verbose:
                print("✅ Answer generated")

            return answer

        except Exception as e:
            error_msg = f"❌ Error generating answer: {str(e)}"
            if verbose:
                print(error_msg)
            return error_msg

    def get_document_summary(self, max_length: int = 500) -> str:
        """Get a summary of the loaded document."""
        if not self.qa_chain:
            return "❌ No PDF loaded."

        summary_question = f"Please provide a comprehensive summary of this document in no more than {max_length} words. Include the main topics, key points, and overall purpose of the document."
        return self.ask_question(summary_question, verbose=False)

    def search_document(self, query: str, k: int = 3) -> List[str]:
        """Search for relevant sections in the document."""
        if not self.vectorstore:
            return ["❌ No PDF loaded."]

        try:
            # Perform similarity search
            docs = self.vectorstore.similarity_search(query, k=k)

            # Extract content from documents
            results = []
            for i, doc in enumerate(docs, 1):
                content = doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content
                results.append(f"Result {i}: {content}")

            return results

        except Exception as e:
            return [f"❌ Error searching document: {str(e)}"]

    def clear_memory(self):
        """Clear the conversation memory."""
        if self.memory:
            self.memory.clear()
            print("✅ Conversation memory cleared")

    def save_vectorstore(self, directory: str = None) -> bool:
        """Save the vector store to organized processed outputs folder."""
        if not self.vectorstore:
            print("❌ No vector store to save")
            return False

        try:
            # Use organized folder structure if no directory specified
            if directory is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                directory = self.processed_outputs_dir / f"vectorstore_{timestamp}"

            os.makedirs(directory, exist_ok=True)
            self.vectorstore.save_local(str(directory))
            print(f"✅ Vector store saved to {directory}")
            return True
        except Exception as e:
            print(f"❌ Error saving vector store: {e}")
            return False

    def save_extracted_text(self, text: str, pdf_filename: str) -> str:
        """Save extracted text to organized processed outputs folder."""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = Path(pdf_filename).stem
            output_filename = f"{timestamp}_{base_name}_extracted.txt"
            output_path = self.processed_outputs_dir / output_filename

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)

            print(f"✅ Extracted text saved to {output_path}")
            return str(output_path)

        except Exception as e:
            print(f"❌ Error saving extracted text: {e}")
            return ""

    def load_vectorstore(self, directory: str = "vectorstore") -> bool:
        """Load a vector store from disk."""
        if not HAS_LANGCHAIN or not self.embeddings:
            print("⚠️ LLM functionality not available")
            return False

        try:
            if not os.path.exists(directory):
                print(f"❌ Vector store directory {directory} not found")
                return False

            self.vectorstore = FAISS.load_local(directory, self.embeddings)

            # Recreate QA chain
            if self.llm:
                prompt_template = PromptTemplate(
                    input_variables=["context", "question"],
                    template="""You are an expert assistant. Use the following document content to answer the user's question accurately and comprehensively.

Context: {context}

Question: {question}

Answer: Provide a detailed and accurate answer based on the document content. If the information is not available in the document, clearly state that."""
                )

                self.qa_chain = ConversationalRetrievalChain.from_llm(
                    llm=self.llm,
                    retriever=self.vectorstore.as_retriever(search_type="similarity"),
                    memory=self.memory,
                    combine_docs_chain_kwargs={"prompt": prompt_template}
                )

            print(f"✅ Vector store loaded from {directory}")
            return True

        except Exception as e:
            print(f"❌ Error loading vector store: {e}")
            return False


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

def main():
    """Main function demonstrating the enhanced PDF reader capabilities."""
    print("🚀 Enhanced PDF Reader with LLM Integration")
    print("=" * 50)

    # Use command line argument if provided
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Check for user-uploaded PDFs in the organized folder
        uploaded_pdfs_dir = Path("data/multimodal/uploaded_pdfs")
        if uploaded_pdfs_dir.exists():
            pdf_files = list(uploaded_pdfs_dir.glob("*.pdf"))
            if pdf_files:
                # Use the most recent uploaded PDF
                pdf_path = str(max(pdf_files, key=os.path.getctime))
                print(f"📁 Using most recent uploaded PDF: {pdf_path}")
            else:
                print("❌ No PDF files found in uploaded_pdfs folder.")
                print("Please upload a PDF file first or provide a PDF file path as an argument.")
                print("Usage: python pdf_reader.py path/to/your/file.pdf")
                sys.exit(1)
        else:
            print("❌ Please provide a PDF file path as an argument.")
            print("Usage: python pdf_reader.py path/to/your/file.pdf")
            sys.exit(1)

    # Initialize the enhanced PDF reader
    print(f"\n📚 Initializing Enhanced PDF Reader for: {pdf_path}")
    reader = EnhancedPDFReader()

    # Extract text using traditional method
    print("\n📄 Extracting text using traditional method...")
    text = reader.extract_text_from_pdf(pdf_path, verbose=True)

    if text:
        print("\n" + "="*50)
        print("EXTRACTED TEXT (First 500 characters)")
        print("="*50)
        print(text[:500] + "..." if len(text) > 500 else text)

        # Optionally save to file if requested
        if len(sys.argv) > 2 and sys.argv[2] == "--save":
            output_path = os.path.splitext(pdf_path)[0] + ".txt"
            save_extracted_text(text, output_path)

    # If LLM functionality is available, demonstrate it
    if reader.llm:
        print("\n🤖 LLM functionality is available! Demonstrating advanced features...")

        # Load and process PDF for question answering
        print("\n📚 Loading PDF for question answering...")
        if reader.load_and_process_pdf(pdf_path):

            # Get document summary
            print("\n📋 Generating document summary...")
            summary = reader.get_document_summary()
            print("Summary:", summary)

            # Interactive question answering if no command line args
            if len(sys.argv) <= 1:
                print("\n❓ Interactive Question Answering Mode")
                print("Type your questions (or 'quit' to exit):")

                while True:
                    question = input("\nQ: ").strip()
                    if question.lower() in ['quit', 'exit', 'q']:
                        break
                    if question:
                        answer = reader.ask_question(question)
                        print(f"A: {answer}")

            # Save vector store for future use
            print("\n💾 Saving vector store...")
            reader.save_vectorstore("pdf_vectorstore")

        else:
            print("❌ Failed to process PDF for question answering")

    else:
        print("\n⚠️ LLM functionality not available.")
        print("To enable LLM features:")
        print("1. Install required packages: pip install langchain langchain-together langchain-community")
        print("2. Set TOGETHER_API_KEY in your .env file")
        print("3. Ensure all dependencies are properly installed")

    print("\n✅ Processing completed!")


if __name__ == "__main__":
    main()
