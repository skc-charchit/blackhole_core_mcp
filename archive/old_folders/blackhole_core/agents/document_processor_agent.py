#!/usr/bin/env python3
"""
Document Processor Agent for BlackHole Core MCP
Handles document analysis, summarization, and Q&A
"""

import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from .base_agent import BaseAgent
from ..data_source.mongodb import get_mongo_client
from data.multimodal.pdf_reader import EnhancedPDFReader, extract_text_from_pdf
from data.multimodal.image_ocr import extract_text_from_image

logger = logging.getLogger(__name__)

class DocumentProcessorAgent(BaseAgent):
    """
    Agent for processing documents with AI capabilities.
    Handles PDFs, images, and text files with LLM integration.
    """
    
    def __init__(self, memory=None, source=None):
        """Initialize the Document Processor Agent."""
        super().__init__(memory=memory, source=source)
        
        self.client = get_mongo_client()
        self.db = self.client["blackhole_db"]
        
        # Initialize enhanced PDF reader
        self.pdf_reader = None
        try:
            self.pdf_reader = EnhancedPDFReader()
            if self.pdf_reader.llm:
                logger.info("Document Processor Agent initialized with LLM capabilities")
            else:
                logger.warning("Document Processor Agent initialized without LLM capabilities")
        except Exception as e:
            logger.error(f"Failed to initialize PDF reader: {e}")
    
    def plan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process document-related commands.
        
        Args:
            input_data: Dictionary containing document processing request
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Extract parameters
            document_text = input_data.get('document_text', '')
            file_path = input_data.get('file_path', '')
            command_type = input_data.get('command_type', 'analyze')
            
            # Determine processing type
            if file_path:
                return self._process_file(file_path, command_type)
            elif document_text:
                return self._process_text(document_text, command_type)
            else:
                return self._get_document_capabilities()
        
        except Exception as e:
            logger.error(f"Error in DocumentProcessorAgent.plan: {e}")
            return {
                "agent": "DocumentProcessorAgent",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _process_file(self, file_path: str, command_type: str) -> Dict[str, Any]:
        """Process a specific file."""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.pdf':
                return self._process_pdf(file_path, command_type)
            elif file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']:
                return self._process_image(file_path, command_type)
            else:
                return self._process_text_file(file_path, command_type)
        
        except Exception as e:
            return {
                "agent": "DocumentProcessorAgent",
                "status": "error",
                "error": f"Failed to process file {file_path}: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _process_pdf(self, file_path: str, command_type: str) -> Dict[str, Any]:
        """Process PDF file with LLM capabilities."""
        try:
            # Extract basic text
            text = extract_text_from_pdf(file_path, verbose=False)
            
            result = {
                "agent": "DocumentProcessorAgent",
                "status": "success",
                "file_path": file_path,
                "file_type": "PDF",
                "extracted_text": text,
                "text_length": len(text),
                "timestamp": datetime.now().isoformat()
            }
            
            # Enhanced processing with LLM if available
            if self.pdf_reader and self.pdf_reader.llm:
                try:
                    # Load PDF for Q&A
                    success = self.pdf_reader.load_and_process_pdf(file_path, verbose=False)
                    
                    if success:
                        # Generate summary
                        summary = self.pdf_reader.get_document_summary(max_length=200)
                        
                        # Generate key insights
                        insights = self.pdf_reader.ask_question(
                            "What are the key points and main topics in this document?",
                            verbose=False
                        )
                        
                        result.update({
                            "llm_processing": True,
                            "summary": summary,
                            "key_insights": insights,
                            "ready_for_questions": True
                        })
                    
                except Exception as e:
                    logger.warning(f"LLM processing failed for PDF: {e}")
                    result["llm_processing"] = False
                    result["llm_error"] = str(e)
            
            return result
        
        except Exception as e:
            return {
                "agent": "DocumentProcessorAgent",
                "status": "error",
                "error": f"PDF processing failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _process_image(self, file_path: str, command_type: str) -> Dict[str, Any]:
        """Process image file with OCR."""
        try:
            # Extract text using OCR
            text = extract_text_from_image(
                file_path,
                debug=False,
                preprocessing_level=2
            )
            
            result = {
                "agent": "DocumentProcessorAgent",
                "status": "success",
                "file_path": file_path,
                "file_type": "Image",
                "extracted_text": text,
                "text_length": len(text),
                "timestamp": datetime.now().isoformat()
            }
            
            # Analyze extracted text with LLM if available and text was found
            if self.pdf_reader and self.pdf_reader.llm and text and len(text.strip()) > 10:
                try:
                    # Create a temporary document for analysis
                    analysis = self.pdf_reader.llm.invoke(
                        f"Analyze this text extracted from an image and provide key insights:\n\n{text}"
                    )
                    
                    result.update({
                        "llm_analysis": analysis,
                        "llm_processing": True
                    })
                
                except Exception as e:
                    logger.warning(f"LLM analysis failed for image text: {e}")
                    result["llm_processing"] = False
                    result["llm_error"] = str(e)
            
            return result
        
        except Exception as e:
            return {
                "agent": "DocumentProcessorAgent",
                "status": "error",
                "error": f"Image processing failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _process_text_file(self, file_path: str, command_type: str) -> Dict[str, Any]:
        """Process text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            result = {
                "agent": "DocumentProcessorAgent",
                "status": "success",
                "file_path": file_path,
                "file_type": "Text",
                "extracted_text": text,
                "text_length": len(text),
                "timestamp": datetime.now().isoformat()
            }
            
            # Analyze with LLM if available
            if self.pdf_reader and self.pdf_reader.llm and len(text.strip()) > 10:
                try:
                    analysis = self.pdf_reader.llm.invoke(
                        f"Analyze this text document and provide a summary and key insights:\n\n{text[:2000]}..."
                    )
                    
                    result.update({
                        "llm_analysis": analysis,
                        "llm_processing": True
                    })
                
                except Exception as e:
                    logger.warning(f"LLM analysis failed for text: {e}")
                    result["llm_processing"] = False
                    result["llm_error"] = str(e)
            
            return result
        
        except Exception as e:
            return {
                "agent": "DocumentProcessorAgent",
                "status": "error",
                "error": f"Text file processing failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _process_text(self, text: str, command_type: str) -> Dict[str, Any]:
        """Process raw text input."""
        try:
            result = {
                "agent": "DocumentProcessorAgent",
                "status": "success",
                "input_text": text,
                "text_length": len(text),
                "timestamp": datetime.now().isoformat()
            }
            
            # Analyze with LLM if available
            if self.pdf_reader and self.pdf_reader.llm:
                try:
                    if command_type == 'summarize':
                        prompt = f"Provide a concise summary of this text:\n\n{text}"
                    elif command_type == 'analyze':
                        prompt = f"Analyze this text and provide key insights, themes, and important points:\n\n{text}"
                    else:
                        prompt = f"Process this text and provide relevant information:\n\n{text}"
                    
                    analysis = self.pdf_reader.llm.invoke(prompt)
                    
                    result.update({
                        "llm_analysis": analysis,
                        "llm_processing": True,
                        "command_type": command_type
                    })
                
                except Exception as e:
                    logger.warning(f"LLM analysis failed: {e}")
                    result["llm_processing"] = False
                    result["llm_error"] = str(e)
            
            return result
        
        except Exception as e:
            return {
                "agent": "DocumentProcessorAgent",
                "status": "error",
                "error": f"Text processing failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_document_capabilities(self) -> Dict[str, Any]:
        """Return information about document processing capabilities."""
        return {
            "agent": "DocumentProcessorAgent",
            "status": "success",
            "capabilities": {
                "supported_formats": ["PDF", "PNG", "JPG", "JPEG", "BMP", "TIFF", "TXT"],
                "features": [
                    "Text extraction from PDFs",
                    "OCR for images",
                    "LLM-powered analysis",
                    "Document summarization",
                    "Question answering",
                    "Key insights extraction"
                ],
                "llm_available": self.pdf_reader is not None and self.pdf_reader.llm is not None,
                "ocr_available": True
            },
            "usage": {
                "commands": [
                    "process document [file_path]",
                    "analyze [text]",
                    "summarize [text]",
                    "extract from [file_path]"
                ],
                "examples": [
                    "process document data/sample.pdf",
                    "analyze this is sample text to analyze",
                    "summarize the main points of this document"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
