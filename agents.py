import pdfplumber
from typing import Dict, Any, Optional
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnableSequence
import json
import re
from logger_config import setup_logger

# Setup loggers for each agent
extractor_logger = setup_logger('extractor_agent')
summarizer_logger = setup_logger('summarizer_agent')
field_extractor_logger = setup_logger('field_extractor_agent')
processor_logger = setup_logger('document_processor')

class ExtractorAgent:
    def __init__(self):
        self.name = "Extractor Agent"
        self.logger = extractor_logger
    
    def process(self, pdf_path: str) -> str:
        """Extract text from PDF document."""
        self.logger.info(f"Starting text extraction from PDF: {pdf_path}")
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for i, page in enumerate(pdf.pages, 1):
                    self.logger.debug(f"Processing page {i}")
                    page_text = page.extract_text() or ""
                    text += page_text
                self.logger.info(f"Successfully extracted text from {len(pdf.pages)} pages")
                return text
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF: {str(e)}", exc_info=True)
            raise Exception(f"Error extracting text from PDF: {str(e)}")

class SummarizerAgent:
    def __init__(self, fast_mode=False):
        self.name = "Summarizer Agent"
        self.logger = summarizer_logger
        self.fast_mode = fast_mode
        
        if not fast_mode:
            self.llm = Ollama(model="llama3")
            self.prompt = PromptTemplate(
                input_variables=["text"],
                template="""Please provide a concise summary of the following text. 
                Focus on the main points and key information:
                
                {text}
                
                Summary:"""
            )
            self.chain = self.prompt | self.llm
    
    def process(self, text: str) -> str:
        """Generate a summary of the extracted text."""
        self.logger.info("Starting text summarization")
        try:
            if self.fast_mode:
                # Fast mode: extract first few sentences and key phrases
                sentences = text.split('.')
                # Get first 2-3 sentences as summary
                summary_sentences = sentences[:min(3, len(sentences))]
                summary = '. '.join(summary_sentences) + '.'
                
                # Add key phrases (words that appear frequently)
                words = re.findall(r'\b\w+\b', text.lower())
                word_freq = {}
                for word in words:
                    if len(word) > 3:  # Skip short words
                        word_freq[word] = word_freq.get(word, 0) + 1
                
                # Get top 5 most frequent words
                top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
                key_phrases = [word for word, freq in top_words if freq > 1]
                
                if key_phrases:
                    summary += f"\n\nKey topics: {', '.join(key_phrases)}"
                
                self.logger.info("Generated fast summary")
                return summary
            else:
                # Full LLM mode
                summary = self.chain.invoke({"text": text})
                self.logger.info("Successfully generated LLM summary")
                return summary
        except Exception as e:
            self.logger.error(f"Error generating summary: {str(e)}", exc_info=True)
            # Fallback to fast mode if LLM fails
            self.logger.info("Falling back to fast mode")
            self.fast_mode = True
            return self.process(text)

class FieldExtractorAgent:
    def __init__(self, fast_mode=False):
        self.name = "Field Extractor Agent"
        self.logger = field_extractor_logger
        self.fast_mode = fast_mode
        
        if not fast_mode:
            self.llm = Ollama(model="llama3")
            self.prompt = PromptTemplate(
                input_variables=["text"],
                template="""Analyze the following text and extract key information into a JSON object.
                Include these fields if present in the text:
                - date: The date mentioned in the document
                - title: The title or main topic
                - author: The author or sender
                - recipient: The recipient or audience
                - main_points: A list of key points or topics
                - summary: A brief summary of the content
                
                Return ONLY a valid JSON object with no additional text or explanation.
                Example format:
                {{
                    "date": "2024-03-20",
                    "title": "Sample Document",
                    "author": "John Doe",
                    "recipient": "Jane Smith",
                    "main_points": ["Point 1", "Point 2"],
                    "summary": "Brief summary here"
                }}
                
                Text to analyze:
                {text}
                
                JSON:"""
            )
            self.chain = self.prompt | self.llm
    
    def process(self, text: str) -> Dict[str, Any]:
        """Extract key fields from the text and return as structured JSON."""
        self.logger.info("Starting field extraction")
        try:
            if self.fast_mode:
                # Fast mode: use regex and simple text analysis
                result = self._fast_field_extraction(text)
                self.logger.info("Generated fast field extraction")
                return result
            else:
                # Full LLM mode
                result = self.chain.invoke({"text": text})
                self.logger.debug("Received raw LLM response")
                
                # Clean the result to ensure it's valid JSON
                result = result.strip()
                
                # Remove any markdown code block markers
                result = re.sub(r'```json\s*', '', result)
                result = re.sub(r'```\s*$', '', result)
                
                # Try to find JSON object in the response
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    result = json_match.group(0)
                    self.logger.debug("Successfully extracted JSON from response")
                
                # Parse the JSON
                try:
                    parsed_json = json.loads(result)
                    self.logger.info("Successfully parsed JSON response")
                    return parsed_json
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to parse JSON response: {str(e)}")
                    # If JSON parsing fails, return a basic structure with the error
                    return {
                        "error": "Failed to parse JSON response",
                        "raw_response": result[:200] + "..." if len(result) > 200 else result,
                        "parsed_fields": {
                            "date": None,
                            "title": None,
                            "author": None,
                            "recipient": None,
                            "main_points": [],
                            "summary": "Failed to generate summary"
                        }
                    }
        except Exception as e:
            self.logger.error(f"Error extracting fields: {str(e)}", exc_info=True)
            # Fallback to fast mode if LLM fails
            self.logger.info("Falling back to fast mode")
            self.fast_mode = True
            return self.process(text)
    
    def _fast_field_extraction(self, text: str) -> Dict[str, Any]:
        """Fast field extraction using regex and text analysis."""
        # Date extraction (various formats)
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or MM-DD-YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD or YYYY-MM-DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
        ]
        
        date = None
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                date = match.group()
                break
        
        # Title extraction (first line or first sentence)
        lines = text.strip().split('\n')
        title = lines[0][:100] if lines else "Untitled Document"
        
        # Author extraction (look for common patterns)
        author_patterns = [
            r'(?:by|author|from|sent by|written by)[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'([A-Z][a-z]+ [A-Z][a-z]+)(?:\s+<[^>]+>|\s+\([^)]+\))?',
        ]
        
        author = None
        for pattern in author_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                author = match.group(1)
                break
        
        # Main points extraction (bullet points, numbered lists, or key phrases)
        main_points = []
        
        # Look for bullet points or numbered lists
        bullet_patterns = [
            r'[•\-\*]\s*([^.\n]+)',
            r'\d+\.\s*([^.\n]+)',
        ]
        
        for pattern in bullet_patterns:
            matches = re.findall(pattern, text)
            main_points.extend(matches[:5])  # Limit to 5 points
        
        # If no bullet points found, extract key sentences
        if not main_points:
            sentences = text.split('.')
            # Get sentences that contain key words
            key_words = ['important', 'key', 'main', 'primary', 'essential', 'critical']
            for sentence in sentences[:10]:  # Check first 10 sentences
                if any(word in sentence.lower() for word in key_words):
                    clean_sentence = sentence.strip()
                    if len(clean_sentence) > 10 and len(clean_sentence) < 200:
                        main_points.append(clean_sentence)
                        if len(main_points) >= 3:
                            break
        
        # Generate a simple summary
        sentences = text.split('.')
        summary_sentences = sentences[:min(2, len(sentences))]
        summary = '. '.join(summary_sentences) + '.'
        
        return {
            "date": date,
            "title": title,
            "author": author,
            "recipient": None,  # Hard to extract without LLM
            "main_points": main_points[:5],  # Limit to 5 points
            "summary": summary,
            "extraction_method": "fast_regex"
        }

class DocumentProcessor:
    def __init__(self, fast_mode=False):
        self.logger = processor_logger
        self.fast_mode = fast_mode
        self.extractor = ExtractorAgent()
        self.summarizer = SummarizerAgent(fast_mode=fast_mode)
        self.field_extractor = FieldExtractorAgent(fast_mode=fast_mode)
        self.logger.info(f"Document processor initialized with fast_mode={fast_mode}")
    
    def process_document(self, pdf_path: str) -> Dict[str, Any]:
        """Process a PDF document and return extracted information."""
        self.logger.info(f"Starting document processing: {pdf_path}")
        
        try:
            # Extract text
            extracted_text = self.extractor.process(pdf_path)
            
            # Generate summary
            summary = self.summarizer.process(extracted_text)
            
            # Extract fields
            fields = self.field_extractor.process(extracted_text)
            
            result = {
                "extracted_text": extracted_text,
                "summary": summary,
                "fields": fields
            }
            
            self.logger.info("Document processing completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing document: {str(e)}", exc_info=True)
            raise Exception(f"Error processing document: {str(e)}") 